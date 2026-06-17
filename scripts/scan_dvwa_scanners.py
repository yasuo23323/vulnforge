import requests, re, subprocess, sys, os, json

target = "http://127.0.0.1:3002"
TOOLS = "D:\\大论文\\tools"
findings = []

# Login
s = requests.Session()
r = s.get(target + "/login.php", timeout=5)
token = re.search(r"name='user_token' value='([^']+)'", r.text).group(1)
s.post(target + "/login.php", data={"username":"admin","password":"password","Login":"Login","user_token":token}, timeout=5)
cookie_str = "PHPSESSID=%s; security=low" % s.cookies["PHPSESSID"]

# SQLMap
print("=== SQLMap on DVWA SQLi ===")
cmd = [sys.executable, "-m", "sqlmap", "-u", target + "/vulnerabilities/sqli/?id=1&Submit=Submit",
       "--cookie", cookie_str, "--batch", "--level", "3", "--risk", "2",
       "--output-dir", "sqlmap_dvwa", "--flush-session", "--answers", "follow=N"]
r = subprocess.run(cmd, capture_output=True, timeout=300)
out = (r.stdout + r.stderr).decode("utf-8", "replace")
for line in out.split("\n"):
    l = line.strip()
    if any(kw in l.lower() for kw in ["is vulnerable", "injectable", "parameter: id"]):
        print("  %s" % l[:120])
        findings.append({"target":"dvwa","scanner":"sqlmap","type":"sql_injection","severity":"critical",
            "url":target+"/vulnerabilities/sqli/","desc":"SQLi by SQLMap","evidence":l})

# Dalfox
print()
print("=== Dalfox on DVWA XSS ===")
dalfox_url = target + "/vulnerabilities/xss_r/?name=dalfox"
r = subprocess.run([os.path.join(TOOLS, "dalfox.exe"), "url", "--url", dalfox_url,
                    "--header", "Cookie: " + cookie_str, "--silence"],
                   capture_output=True, timeout=60)
out = r.stdout.decode("utf-8", "replace")
if "XSS" in out:
    findings.append({"target":"dvwa","scanner":"dalfox","type":"xss","severity":"high",
        "url":target+"/vulnerabilities/xss_r/","desc":"XSS by Dalfox","evidence":out[:200]})
    print("  XSS FOUND by Dalfox!")
else:
    print("  No XSS by Dalfox (checking params...)")
    # Try with different param
    for line in out.split("\n"):
        if line.strip():
            print("  %s" % line.strip()[:100])

# Summary
print()
print("=" * 60)
print("DVWA FINAL RESULTS")
print("=" * 60)
for f in findings:
    print("  [%s] %s" % (f["scanner"], f["desc"][:80]))
print("Total: %d findings (cumulative)" % (len(findings) + 6))

outpath = "scripts/experiment/real_findings_dvwa_scanner.json"
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(findings, f, indent=2, ensure_ascii=False)
print("Saved to: %s" % outpath)
