import asyncio
import subprocess
import sys
import os
import re
from urllib.parse import urlparse, urljoin
from typing import Optional
import httpx
from app.scanner.base import BaseScanner, ScanResult
from app.scanner.parsers import SCANNER_PARSERS
from app.config import settings
from app.llm.prompts import PromptBuilder


class ScannerOrchestrator:

    def __init__(self):
        self._scanners: dict[str, BaseScanner] = {}
        self.prompt_builder = PromptBuilder()

    def register_scanner(self, scanner: BaseScanner):
        self._scanners[scanner.name] = scanner

    async def _discover_urls(self, target_url: str) -> list[str]:
        """Discover URLs: crawl homepage + probe common API paths."""
        discovered = {target_url}
        parsed = urlparse(target_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        # Step 1: Crawl homepage for <a href> and <form action>
        try:
            async with httpx.AsyncClient(timeout=10, verify=False) as client:
                resp = await client.get(target_url, headers={"User-Agent": "Mozilla/5.0"})
                html = resp.text
                for m in re.finditer(r'href=["'"'"']([^"'"'"']+)["'"'"']', html):
                    link = m.group(1)
                    if link.startswith("#") or link.startswith("javascript:"):
                        continue
                    full = urljoin(target_url, link)
                    if base.rstrip("/") in full:
                        discovered.add(full.split("#")[0])
                for m in re.finditer(r'action=["'"'"']([^"'"'"']+)["'"'"']', html):
                    link = m.group(1)
                    full = urljoin(target_url, link)
                    if base.rstrip("/") in full:
                        discovered.add(full.split("#")[0])
        except:
            pass

        # Step 2: Probe common API/endpoint paths (for SPA apps like Juice Shop)
        common_paths = [
            "/api/Products", "/api/Users", "/api/Feedbacks",
            "/api/Challenges", "/api/BasketItems", "/api/Orders",
            "/api/", "/swagger.json", "/api-docs/",
            "/robots.txt", "/sitemap.xml", "/.well-known/security.txt",
            "/search", "/login", "/admin", "/assets/",
        ]
        async with httpx.AsyncClient(timeout=5, verify=False) as client:
            for path in common_paths:
                try:
                    full = f"{base.rstrip('/')}{path}"
                    resp = await client.get(full, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code in (200, 401, 403, 500):
                        discovered.add(full)
                except:
                    pass

        # Step 3: For discovered API endpoints, add ?id=1 variant for sqlmap
        api_urls = list(discovered)
        for url in api_urls:
            if "?" not in url and ("/api/" in url):
                discovered.add(f"{url}?id=1")

        return list(discovered)

    async def run_scanners(
        self,
        target_url: str,
        scanner_names: Optional[list[str]] = None,
        **kwargs,
    ) -> dict[str, list[ScanResult]]:
        names = scanner_names or list(self._scanners.keys())
        tasks = {}

        # Discover URLs first (for sqlmap/dalfox multi-url scanning)
        discovered = await self._discover_urls(target_url)
        print(f"[Discovery] Found {len(discovered)} URLs on {target_url}")

        for name in names:
            if name in self._scanners:
                tasks[name] = self._scanners[name].scan(target_url, **kwargs)
            elif name in ("sqlmap", "dalfox"):
                # These scanners benefit from multi-URL scanning
                tasks[name] = self._run_multi_url_scanner(name, target_url, discovered, **kwargs)
            else:
                tasks[name] = self._run_scanner_subprocess(name, target_url, **kwargs)

        results = {}
        for name, coro in tasks.items():
            try:
                results[name] = await asyncio.wait_for(coro, timeout=300)
            except asyncio.TimeoutError:
                results[name] = []
                print(f"Scanner {name} timed out")
            except Exception as e:
                results[name] = []
                print(f"Scanner {name} failed: {e}")
        return results

    async def _run_multi_url_scanner(
        self, scanner_name: str, target_url: str, urls: list[str], **kwargs
    ) -> list[ScanResult]:
        """Run sqlmap/dalfox against ALL discovered URLs, not just the homepage."""
        parser = SCANNER_PARSERS.get(scanner_name)
        if not parser:
            raise ValueError(f"No parser for scanner: {scanner_name}")
        all_results = []
        for url in urls:
            # Skip URLs without query params for sqlmap
            if scanner_name == "sqlmap" and "?" not in url:
                continue
            cmd = self._build_command(scanner_name, url, **kwargs)
            if not cmd:
                continue
            try:
                stdin_data = None
                stdin_pipe = None
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdin=stdin_pipe, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(input=stdin_data), timeout=120)
                raw_output = stdout.decode("utf-8", errors="replace")
                all_results.extend(parser(raw_output, url))
            except:
                pass
        return all_results

    async def _run_scanner_subprocess(
        self, scanner_name: str, target_url: str, **kwargs
    ) -> list[ScanResult]:
        parser = SCANNER_PARSERS.get(scanner_name)
        if not parser:
            raise ValueError(f"No parser for scanner: {scanner_name}")
        cmd = self._build_command(scanner_name, target_url, **kwargs)
        if not cmd:
            raise ValueError(f"No command for: {scanner_name}")

        stdin_data = None
        stdin_pipe = None
        wordlist_path = os.path.join(os.path.dirname(__file__), "common.txt")

        process = await asyncio.create_subprocess_exec(
            *cmd, stdin=stdin_pipe, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(input=stdin_data), timeout=300)
        raw_output = stdout.decode("utf-8", errors="replace")
        return parser(raw_output, target_url)

    def _build_command(self, scanner_name: str, target_url: str, **kwargs) -> Optional[list[str]]:
        cookies = kwargs.get("cookies", "")
        header = ["-H", f"Cookie: {cookies}"] if cookies else []
        sqlmap_cookie = ["--cookie", cookies] if cookies else []

        if scanner_name == "nuclei":
            mapped = target_url
            if "127.0.0.1" in target_url or "localhost" in target_url:
                port_map = {
                    "3001": ("vulnforge-juice-shop-1", "3000"),
                    "3002": ("vulnforge-dvwa-1", "80"),
                    "3003": ("vulnforge-webgoat-1", "8080"),
                    "8080": ("dvwa", "80"),
                }
                for host_port, (container, container_port) in port_map.items():
                    if ":" + host_port in target_url:
                        for prefix in ["http://127.0.0.1:", "http://localhost:"]:
                            mapped = mapped.replace(prefix + host_port, "http://" + container + ":" + container_port)
                        break
                return (["docker", "run", "--rm", "--network", "vulnforge_default",
                        "projectdiscovery/nuclei", "-u", mapped, "-j", "-silent",
                        "-timeout", "15", "-retries", "2", "-esc", "-severity", "critical,high,medium,low,info"]
                        + header)
            else:
                return (["docker", "run", "--rm",
                        "projectdiscovery/nuclei", "-u", mapped, "-j", "-silent",
                        "-timeout", "15", "-retries", "2", "-esc", "-severity", "critical,high,medium,low,info"]
                        + header)

        if scanner_name == "sqlmap":
            return (["sqlmap", "-u", target_url, "--batch",
                    "--level", "1", "--risk", "1", "--no-cast", "--flush-session"]
                    + sqlmap_cookie)

        if scanner_name == "dalfox":
            return (["docker", "run", "--rm", "--entrypoint", "/app/dalfox", "hahwul/dalfox", "url", "--url", target_url, "--silence"]
                    + header)

        if scanner_name == "ffuf":
            wordlist_path = os.path.join(os.path.dirname(__file__), "common.txt")
            return (["ffuf", "-u", f"{target_url}/FUZZ", "-w", wordlist_path, "-t", "10", "-s"]
                    + header)

        return None





