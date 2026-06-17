import requests, re, subprocess, sys, os, json

target = "http://127.0.0.1:3002"
TOOLS = "D:\\大论文\\tools"
findings = []
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Login
s = requests.Session()
r = s.get(target + "/login.php", timeout=5)
token = re.search(r"name='user_token' value='([^']+)'", r.text).group(1)
s.post(target + "/login.php", data={"username":"admin","password":"password","Login":"Login","user_token":token}, timeout=5)
cookie = "PHPSESSID=%s; security=low" % s.cookies["PHPSESSID"]

# 1. Dalfox on DVWA XSS (FIXED: --headers not --header)
print("=== Dalfox on DVWA XSS ===")
dalfox_path = os.path.join(TOOLS, "dalfox.exe")
r = subprocess.run(
    [dalfox_path, "url", "--url", target + "/vulnerabilities/xss_r/?name=dalfox",
     "--headers", "Cookie: " + cookie, "--silence"],
    capture_output=True, timeout=60)
out = (r.stdout + r.stderr).decode("utf-8", "replace")
for line in out.split("\n"):
    l = line.strip()
    if l and ("XSS" in l or "VULN" in l or "found" in l.lower()):
        print("  %s" % l[:120])
        findings.append({"target":"dvwa","scanner":"dalfox","type":"xss","severity":"high",
            "url":target+"/vulnerabilities/xss_r/","desc":"XSS detected by Dalfox","evidence":l})

# 2. SQLMap on DVWA SQLi  
print()
print("=== SQLMap on DVWA SQLi ===")
r = subprocess.run(
    [sys.executable, "-m", "sqlmap", "-u", target + "/vulnerabilities/sqli/?id=1&Submit=Submit",
     "--cookie", cookie, "--batch", "--level", "1", "--risk", "1",
     "--output-dir", "sqlmap_dvwa2", "--flush-session", "--answers", "follow=N"],
    capture_output=True, timeout=120)
out = (r.stdout + r.stderr).decode("utf-8", "replace")
for line in out.split("\n"):
    l = line.strip()
    if any(k in l.lower() for k in ["is vulnerable", "injectable", "parameter:", "type: ", "payload: "]):
        print("  %s" % l[:120])
        if "vulnerable" in l.lower() or "injectable" in l.lower():
            findings.append({"target":"dvwa","scanner":"sqlmap","type":"sql_injection","severity":"critical",
                "url":target+"/vulnerabilities/sqli/","desc":"SQLi by SQLMap","evidence":l})

# Summary
print()
print("=" * 60)
print("SCANNER FIX RESULTS")
print("=" * 60)
for f in findings:
    print("  [%s] %s: %s" % (f["scanner"], f["type"], f["desc"][:60]))
if not findings:
    print("  No findings from automated scanners")
print("  (Manual findings already confirmed: SQLi, XSS, Command Injection)")

with open("scripts/experiment/scanner_fix_results.json", "w", encoding="utf-8") as f:
    json.dump(findings, f, indent=2, ensure_ascii=False)
print("Saved to scripts/experiment/scanner_fix_results.json")
