import asyncio
import subprocess
import sys
import os
from typing import Optional
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

    async def run_scanners(
        self,
        target_url: str,
        scanner_names: Optional[list[str]] = None,
        **kwargs,
    ) -> dict[str, list[ScanResult]]:
        names = scanner_names or list(self._scanners.keys())
        tasks = {}
        for name in names:
            if name in self._scanners:
                tasks[name] = self._scanners[name].scan(target_url, **kwargs)
            else:
                tasks[name] = self._run_scanner_subprocess(name, target_url, **kwargs)

        results = {}
        for name, coro in tasks.items():
            try:
                results[name] = await asyncio.wait_for(coro, timeout=120)
            except asyncio.TimeoutError:
                results[name] = []
                print(f"Scanner {name} timed out")
            except Exception as e:
                results[name] = []
                print(f"Scanner {name} failed: {e}")
        return results

    async def _run_scanner_subprocess(
        self, scanner_name: str, target_url: str, **kwargs
    ) -> list[ScanResult]:
        parser = SCANNER_PARSERS.get(scanner_name)
        if not parser:
            raise ValueError(f"No parser for scanner: {scanner_name}")
        cmd = self._build_command(scanner_name, target_url, **kwargs)
        if not cmd:
            raise ValueError(f"No command for: {scanner_name}")

        # Handle ffuf: pipe wordlist via stdin to Docker container
        stdin_data = None
        stdin_pipe = None
        if scanner_name == "ffuf":
            wordlist_path = os.path.join(os.path.dirname(__file__), "common.txt")
            if os.path.exists(wordlist_path):
                with open(wordlist_path, "rb") as f:
                    stdin_data = f.read()
            stdin_pipe = subprocess.PIPE

        process = await asyncio.create_subprocess_exec(
            *cmd, stdin=stdin_pipe, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(input=stdin_data), timeout=120)
        raw_output = stdout.decode("utf-8", errors="replace")
        return parser(raw_output, target_url)

    def _build_command(self, scanner_name: str, target_url: str, **kwargs) -> Optional[list[str]]:
        if scanner_name == "nuclei":
            # Always use Docker mode (Docker CLI is installed in the container)
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
                return ["docker", "run", "--rm", "--network", "vulnforge_default",
                        "projectdiscovery/nuclei", "-u", mapped, "-j", "-silent",
                        "-timeout", "5", "-retries", "1", "-severity", "critical,high,medium"]
            else:
                return ["docker", "run", "--rm",
                        "projectdiscovery/nuclei", "-u", mapped, "-j", "-silent",
                        "-timeout", "5", "-retries", "1", "-severity", "critical,high,medium"]

        if scanner_name == "sqlmap":
            sqlmap_path = os.path.join(os.path.dirname(sys.executable), "sqlmap.exe")
            if not os.path.exists(sqlmap_path):
                sqlmap_path = "sqlmap"
            return [sqlmap_path, "-u", target_url, "--batch",
                    "--level", "1", "--risk", "1", "--no-cast", "--flush-session"]

        if scanner_name == "dalfox":
            return ["docker", "run", "--rm", "hahwul/dalfox", "url", "--url", target_url, "--silence"]

        if scanner_name == "ffuf":
            # Pipe wordlist via stdin (handled by _run_scanner_subprocess)
            return ["docker", "run", "--rm", "-i", "ffuf/ffuf",
                    "-u", f"{target_url}/FUZZ", "-w", "-", "-t", "10", "-ac", "-s"]

        return None
