import asyncio
import os
from typing import Optional

from app.scanner.base import ScanResult
from app.scanner.parsers import SCANNER_PARSERS
from app.config import settings


class ScannerOrchestrator:

    def _get_tool_path(self, name: str) -> str:
        """Return path to scanner tool. Check local tools/ dir first, then PATH."""
        local_path = os.path.join(settings.SCANNER_TOOLS_DIR, name)
        if os.path.exists(local_path):
            return local_path
        # Also check project tools directory
        project_tools = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "..", "tools")
        project_path = os.path.join(project_tools, name)
        if os.path.exists(project_path):
            return project_path
        return name

    def _build_command(self, scanner_name: str, target_url: str) -> Optional[list[str]]:
        if scanner_name == "nuclei":
            nuclei_path = self._get_tool_path("nuclei")
            return [nuclei_path, "-u", target_url, "-silent",
                    "-severity", "medium,high,critical",
                    "-retries", "1", "-timeout", "10"]
        elif scanner_name == "dalfox":
            dalfox_path = self._get_tool_path("dalfox")
            return [dalfox_path, "url", "--url", target_url, "--silence", "--no-cast"]
        elif scanner_name == "ffuf":
            wordlist_path = os.path.join(settings.SCANNER_TOOLS_DIR, "common.txt")
            local_wordlist = os.path.join(os.path.dirname(__file__), "common.txt")
            if os.path.exists(local_wordlist):
                wordlist_path = local_wordlist
            return ["ffuf", "-u", f"{target_url}/FUZZ", "-w", wordlist_path,
                    "-t", "10", "-s"]
        elif scanner_name == "sqlmap":
            return ["sqlmap", "-u", target_url,
                    "--batch", "--flush-session",
                    "--level", "3", "--risk", "2"]
        return None

    async def _run_scanner_subprocess(self, cmd: list[str], timeout: int = 120) -> str:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            output = (stdout or b"").decode("utf-8", errors="replace")
            if stderr:
                output += "\n[STDERR]\n" + stderr.decode("utf-8", errors="replace")
            return output
        except asyncio.TimeoutError:
            return "[TIMEOUT]"
        except Exception as e:
            return f"[ERROR] {e}"

    async def execute(self, scanner_name: str, target_url: str) -> list[ScanResult]:
        parser = SCANNER_PARSERS.get(scanner_name)
        if not parser:
            return [ScanResult(scanner_name=scanner_name, description="No parser", severity="info")]

        cmd = self._build_command(scanner_name, target_url)
        if not cmd:
            return [ScanResult(scanner_name=scanner_name, description="No command", severity="info")]

        raw_output = await self._run_scanner_subprocess(cmd)
        results = parser(raw_output)
        for r in results:
            r.scanner_name = scanner_name
            r.raw_output = raw_output
        if not results:
            results = [ScanResult(scanner_name=scanner_name, raw_output=raw_output)]
        return results

    async def execute_all(self, target_url: str) -> list[ScanResult]:
        scanners = ["nuclei", "dalfox", "ffuf", "sqlmap"]
        all_results = []
        for name in scanners:
            try:
                results = await self.execute(name, target_url)
                all_results.extend(results)
            except Exception as e:
                all_results.append(ScanResult(
                    scanner_name=name,
                    description=f"Scanner failed: {e}",
                    severity="info",
                ))
        return all_results