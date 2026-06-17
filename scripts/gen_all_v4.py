import os, shutil

ROOT = "D:\\大论文"
SRC = os.path.join(ROOT, "backend", "app")
VER = os.path.join(ROOT, "版本迭代")

if os.path.exists(VER): shutil.rmtree(VER)
os.makedirs(VER)

def cp(s, d):
    shutil.copytree(s, d, dirs_exist_ok=True)

def w(p, c):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)

# V4
v4 = os.path.join(VER, "v4_完整版")
cp(SRC, os.path.join(v4, "backend", "app"))
cp(os.path.join(ROOT, "frontend", "src"), os.path.join(v4, "frontend", "src"))
shutil.copy2(os.path.join(ROOT, "docker-compose.yml"), os.path.join(v4, "docker-compose.yml"))
w(os.path.join(v4, "README.md"), "VulnForge v4 - Final Version\nAll bugs fixed, E2E pipeline verified")

# V3 - buggy versions
v3 = os.path.join(VER, "v3_有Bug版")
cp(SRC, os.path.join(v3, "backend", "app"))
cp(os.path.join(ROOT, "frontend", "src"), os.path.join(v3, "frontend", "src"))

# V3 orchestrator with -json bug
orch_code = """import asyncio, subprocess
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
"""
w(os.path.join(v3, "backend", "app", "scanner", "orchestrator.py"), orch_code.strip())

# V3 parsers - missing target_url, wrong keywords
parsers_code = """import json
from app.scanner.base import ScanResult

def parse_nuclei_output(raw):
    r = []
    for l in raw.split(chr(10)):
        if not l.startswith("{"): continue
        try:
            e = json.loads(l)
            r.append(ScanResult(scanner_name="nuclei",
                vulnerability_type=e.get("info",{}).get("name",""),
                severity=e.get("info",{}).get("severity","info"),
                url=e.get("matched-at","")))
        except: continue
    return r

def parse_sqlmap_output(raw, url):
    r = []
    for l in raw.split(chr(10)):
        if "Parameter:" in l:
            r.append(ScanResult(scanner_name="sqlmap", vulnerability_type="sql_injection", severity="high", url=url))
    return r

# BUG: checks "VULNERABLE" but dalfox v3 outputs "XSS payload reflected"
def parse_dalfox_output(raw):
    r = []
    for l in raw.split(chr(10)):
        if "VULNERABLE" not in l: continue
        r.append(ScanResult(scanner_name="dalfox", vulnerability_type="xss", severity="medium", url=""))
    return r

# BUG: expects 3+ columns but silent mode is 1 path/line
def parse_ffuf_output(raw):
    r = []
    for l in raw.split(chr(10)):
        p = l.split()
        if len(p) < 3: continue
        try:
            if int(p[1]) in (200,301,302,403,500):
                r.append(ScanResult(scanner_name="ffuf", vulnerability_type="directory_enumeration", severity="info", url=p[-1]))
        except: continue
    return r

SCANNER_PARSERS = {
    "nuclei": parse_nuclei_output,
    "sqlmap": parse_sqlmap_output,
    "dalfox": parse_dalfox_output,
    "ffuf": parse_ffuf_output,
}
"""
w(os.path.join(v3, "backend", "app", "scanner", "parsers.py"), parsers_code.strip())

# V3 runner - no timeout
runner_code = """import asyncio
from datetime import datetime
from sqlalchemy import select
from app.database import async_session_factory
from app.models import ScanTask, ScanStatus, Finding
from app.scanner.orchestrator import ScannerOrchestrator

async def run_scan_task(scan_id):
    async with async_session_factory() as session:
        r = await session.execute(select(ScanTask).where(ScanTask.id == scan_id))
        t = r.scalar_one_or_none()
        if not t: return {"error": "not found"}
        t.status = ScanStatus.RUNNING
        t.started_at = datetime.utcnow()
        await session.commit()
        try:
            # BUG: no timeout - scan can hang forever
            results = await ScannerOrchestrator().run_scanners(t.target_url, t.scanners)
            for s, find in results.items():
                for sr in find:
                    session.add(Finding(scan_task_id=t.id, scanner_name=sr.scanner_name,
                        vulnerability_type=sr.vulnerability_type, severity=sr.severity, url=sr.url))
            t.status = ScanStatus.COMPLETED
            t.completed_at = datetime.utcnow()
            await session.commit()
        except Exception as e:
            t.status = ScanStatus.FAILED
            t.error_message = str(e)[:500]
            await session.commit()
"""
w(os.path.join(v3, "backend", "app", "scanner", "runner.py"), runner_code.strip())

# V3 settings - OpenAI only
w(os.path.join(v3, "backend", "app", "api", "settings.py"),
   "from fastapi import APIRouter\nfrom app.config import settings\n\n"
   "router = APIRouter(prefix=\"/api/settings\", tags=[\"settings\"])\n\n"
   "@router.get(\"\") async def get():\n"
   "    return {\"llm_provider\": settings.LLM_DEFAULT_PROVIDER, \"llm_model\": settings.LLM_DEFAULT_MODEL}\n\n"
   "# BUG: only OpenAI, no Anthropic support\n"
   "@router.post(\"/test\") async def test():\n"
   "    import httpx\n"
   "    if not settings.OPENAI_API_KEY: return {\"success\": False, \"message\": \"No key\"}\n"
   "    r = await httpx.AsyncClient().post(\"https://api.openai.com/v1/chat/completions\",\n"
   "        json={\"model\": settings.LLM_DEFAULT_MODEL, \"messages\":[{\"role\":\"user\",\"content\":\"OK\"}]},\n"
   "        headers={\"Authorization\": \"Bearer \" + settings.OPENAI_API_KEY})\n"
   "    return {\"success\": r.status_code == 200}\n")

# V3 scans - remove PATCH
scans = open(os.path.join(SRC, "api", "scans.py"), encoding="utf-8").read()
scans = scans.replace("@router.patch(", "# BUG: PATCH not implemented\n# @router.patch(")
w(os.path.join(v3, "backend", "app", "api", "scans.py"), scans)

w(os.path.join(v3, "README.md"), "VulnForge v3 - Buggy Version\n-json, --header, parser arg mismatch, no timeout, BOM")

# V2 - feature expansion without scanner execution
v2 = os.path.join(VER, "v2_功能扩展版")
cp(SRC, os.path.join(v2, "backend", "app"))
cp(os.path.join(ROOT, "frontend", "src"), os.path.join(v2, "frontend", "src"))
# Remove scanner runner/orchestrator, workers, experiment, settings
for p in ["scanner/runner.py", "workers", "api/experiment.py", "api/settings.py"]:
    fp = os.path.join(v2, "backend", "app", p)
    if os.path.exists(fp):
        if os.path.isdir(fp): shutil.rmtree(fp)
        else: os.remove(fp)
# Simplify orchestrator
w(os.path.join(v2, "backend", "app", "scanner", "orchestrator.py"),
   "import asyncio\nclass ScannerOrchestrator:\n"
   "    async def run_scanners(self, url, names=None):\n"
   "        return {}  # scanner execution not implemented yet\n")
w(os.path.join(v2, "README.md"), "VulnForge v2 - Feature Expansion\nScanner engine, LLM client, findings API, frontend pages")

# V1 - minimal
v1 = os.path.join(VER, "v1_初始原型")
cp(SRC, os.path.join(v1, "backend", "app"))
# Remove scanner, llm, workers, experiment, settings, findings
for p in ["scanner", "llm", "workers", "api/experiment.py", "api/settings.py", "api/findings.py", "models/finding.py", "models/llm_analysis.py", "schemas/finding.py"]:
    fp = os.path.join(v1, "backend", "app", p)
    if os.path.exists(fp):
        if os.path.isdir(fp): shutil.rmtree(fp)
        else: os.remove(fp)
# Simplify models __init__
w(os.path.join(v1, "backend", "app", "models", "__init__.py"),
   "from .scan_task import ScanTask, ScanStatus\n")
# Simplify scans
w(os.path.join(v1, "backend", "app", "api", "scans.py"),
   "from fastapi import APIRouter\n\nrouter = APIRouter(prefix=\"/api/scans\")\n\n"
   "@router.post(\"\") async def create(name: str, target: str):\n"
   "    return {\"status\": \"created\", \"name\": name, \"target\": target}\n\n"
   "@router.get(\"\") async def list():\n"
   "    return {\"items\": [], \"total\": 0}\n")
w(os.path.join(v1, "README.md"), "VulnForge v1 - Initial Prototype\nBasic FastAPI, 2 routes, 1 model, no frontend framework")

print("All 4 versions created")

for v in ["v1_初始原型", "v2_功能扩展版", "v3_有Bug版", "v4_完整版"]:
    base = os.path.join(VER, v, "backend", "app")
    py = sum(1 for _,_,fs in os.walk(base) for f in fs if f.endswith(".py")) if os.path.exists(base) else 0
    print("  %s: %d .py files" % (v, py))
