import asyncio
import subprocess
import tempfile
import json
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
        process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
        raw_output = stdout.decode("utf-8", errors="replace")
        return parser(raw_output, target_url)

    def _build_command(self, scanner_name: str, target_url: str, **kwargs) -> Optional[list[str]]:
        path_map = {
            "nuclei": settings.SCANNER_NUCLEI_PATH,
            "dalfox": settings.SCANNER_DALFOX_PATH,
            "ffuf": settings.SCANNER_FFUF_PATH,
        }
        binary = path_map.get(scanner_name)

        if scanner_name == "nuclei":
            return [binary, "-u", target_url, "-j", "-silent",
                    "-timeout", "5", "-retries", "1",
                    "-severity", "critical,high,medium"]

        if scanner_name == "sqlmap":
            # Find sqlmap executable in venv Scripts or system PATH
            sqlmap_path = os.path.join(os.path.dirname(sys.executable), "sqlmap.exe")
            if not os.path.exists(sqlmap_path):
                sqlmap_path = "sqlmap"
            return [sqlmap_path, "-u", target_url, "--batch",
                    "--level", "1", "--risk", "1", "--no-cast", "--flush-session"]

        if scanner_name == "dalfox":
            return [binary, "url", "--url", target_url, "--silence"]

        if scanner_name == "ffuf":
            wordlist = kwargs.get("wordlist", "")
            if not wordlist or not os.path.exists(wordlist):
                wordlist = os.path.join(settings.tools_dir, "common.txt")
            return [binary, "-u", f"{target_url}/FUZZ", "-w", wordlist,
                    "-t", "10", "-ac", "-s"]

        return None
