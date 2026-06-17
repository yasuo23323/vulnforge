import json, subprocess, os, sys

TOOLS = "D:\\大论文\\tools"
WORDLIST = os.path.join(TOOLS, "common.txt")
TARGET = "http://127.0.0.1:3001"
RESULTS = []

def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return r.stdout.decode("utf-8", errors="replace")
    except Exception as e:
        return ""

# 1. FFUF - run with silent mode, parse plain text output
print("=== FFUF: Directory scan ===")
r = run([os.path.join(TOOLS, "ffuf.exe"), "-u", TARGET + "/FUZZ", "-w", WORDLIST,
         "-t", "10", "-s", "-ac"], timeout=30)
for line in r.strip().split("\n"):
    line = line.strip()
    if line and not line.startswith("::"):
        RESULTS.append({
            "scanner": "ffuf", "type": "directory_enumeration",
            "severity": "info", "url": TARGET + "/" + line,
            "desc": "Discovered path via directory brute-force",
            "evidence": line
        })
        print("  Found: /%s" % line)

# 2. Dalfox on known endpoints (uses POST for better XSS detection)
print()
print("=== Dalfox: XSS on API endpoints ===")
for path in ["/api", "/rest/products/search?q=", "/rest/user/login"]:
    url = TARGET + path
    r = run([os.path.join(TOOLS, "dalfox.exe"), "url", "--url", url, "--silence"], timeout=60)
    for line in r.strip().split("\n"):
        line = line.strip()
        if line and "VULN" in line:
            RESULTS.append({
                "scanner": "dalfox", "type": "xss", "severity": "medium",
                "url": url, "desc": "XSS vulnerability detected", "evidence": line
            })
            print("  XSS found: %s" % url)

# 3. SQLMap on search endpoint (known to be injectable via GET param)
print()
print("=== SQLMap: Search endpoint ===")
r = run([sys.executable, "-m", "sqlmap", "-u", TARGET + "/rest/products/search?q=test",
         "--batch", "--level", "1", "--risk", "1",
         "--output-dir", "sqlmap_output"], timeout=120)
has_param = False
for line in r.split("\n"):
    if "Parameter:" in line:
        has_param = True
        RESULTS.append({
            "scanner": "sqlmap", "type": "sql_injection", "severity": "high",
            "url": TARGET + "/rest/products/search?q=",
            "desc": line.strip()[:100], "evidence": line.strip()
        })
        print("  SQLi param detected: %s" % line.strip()[:80])
    if "is vulnerable" in line.lower() or "injectable" in line.lower():
        RESULTS.append({
            "scanner": "sqlmap", "type": "sql_injection", "severity": "critical",
            "url": TARGET + "/rest/products/search?q=",
            "desc": "SQL injection confirmed", "evidence": line.strip()
        })
        print("  SQLi CONFIRMED: %s" % line.strip()[:80])

# Summary
print()
print("=" * 60)
print("SCAN SUMMARY - Juice Shop")
print("=" * 60)
print("Total findings: %d" % len(RESULTS))
for r in RESULTS:
    print("  [%s] %s | %s" % (r["scanner"], r["type"], r["desc"][:60]))

outpath = "scripts/experiment/real_findings.json"
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, indent=2, ensure_ascii=False)
print("\nSaved to: %s" % outpath)
