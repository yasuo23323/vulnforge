import requests, re

target = "http://127.0.0.1:3002"
s = requests.Session()

# Login with CSRF
r = s.get(target + "/login.php", timeout=5)
tok = re.search(r"name='user_token' value='([^']+)'", r.text)
if tok:
    r = s.post(target + "/login.php",
              data={"username":"admin","password":"password","Login":"Login","user_token":tok.group(1)},
              timeout=5)
    print("Login: HTTP %d" % r.status_code)

# Setup DB with CSRF
r = s.get(target + "/setup.php", timeout=5)
tok2 = re.search(r"name='user_token' value='([^']+)'", r.text)
if tok2:
    r = s.post(target + "/setup.php",
              data={"create_db":"Create/Reset Database","user_token":tok2.group(1)},
              timeout=5)
    print("DB Setup: HTTP %d" % r.status_code)

# Security with CSRF
r = s.get(target + "/security.php", timeout=5)
tok3 = re.search(r"name='user_token' value='([^']+)'", r.text)
if tok3:
    r = s.post(target + "/security.php",
              data={"security":"low","seclev_submit":"Submit","user_token":tok3.group(1)},
              timeout=5)
    print("Security: HTTP %d" % r.status_code)

# Access SQLi page
r = s.get(target + "/vulnerabilities/sqli/?id=1", timeout=5)
if "First name" in r.text:
    print("SQLi page: ACCESSIBLE!")
else:
    print("SQLi page: Still login (%d bytes)" % len(r.text))

# Final cookie check
print("Cookies: %s" % dict(s.cookies))
