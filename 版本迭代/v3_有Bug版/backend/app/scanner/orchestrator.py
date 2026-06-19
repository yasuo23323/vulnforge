import asyncio, subprocess
from app.scanner.parsers import SCANNER_PARSERS
from app.config import settings

class ScannerOrchestrator:
    async def run_scanners(self, url, names):
        results = {}
        for n in (names or []):
            try:
                p = await asyncio.create_subprocess_exec(*self._cmd(n, url), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, _ = await p.communicate()
                results[n] = SCANNER_PARSERS[n](out.decode("utf-8","replace"), url)
            except: results[n] = []
        return results

    def _cmd(self, n, url):
        if n == "nuclei": return [settings.SCANNER_NUCLEI_PATH, "-u", url, "-json", "-silent"]
        if n == "sqlmap": return ["python", "-m", "sqlmap", "-u", url, "--batch"]
        if n == "dalfox": return [settings.SCANNER_DALFOX_PATH, "url", url, "--silence"]
        if n == "ffuf": return [settings.SCANNER_FFUF_PATH, "-u", url + "/FUZZ", "-w", "/usr/share/wordlists/dirb/common.txt", "-t", "10"]
        return None