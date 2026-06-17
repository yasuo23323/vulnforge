import requests, re, subprocess, sys, os

target = "http://127.0.0.1:3002"
TOOLS = "D:\\大论文\\tools"

s = requests.Session()
r = s.get(target + "/login.php", timeout=5)
token = re.search(r"name='user_token' value='([^']+)'", r.text).group(1)
s.post(target + "/login.php", data={"username":"admin","password":"password","Login":"Login","user_token":token}, timeout=5)

# Verify XSS works
r = s.get(target + "/vulnerabilities/xss_r/", params={"name": "<script>alert(1)</script>"}, timeout=5)
payload = "<script>alert(1)</script>"
print("Manual XSS works: %s" % (payload in r.text))

# Run Dalfox with cookie
cookie = "PHPSESSID=%s; security=low" % s.cookies["PHPSESSID"]
dalfox_path = os.path.join(TOOLS, "dalfox.exe")
result = subprocess.run(
    [dalfox_path, "url", "--url", target + "/vulnerabilities/xss_r/?name=dalfox",
     "--header", "Cookie: " + cookie, "--silence"],
    capture_output=True, timeout=60)
out = (result.stdout + result.stderr).decode("utf-8", "replace")
print("Dalfox full output:")
for line in out.split("\n"):
    l = line.strip()
    if l:
        print("  %s" % l[:150])
if "XSS" in out or "VULN" in out:
    print("\nRESULT: XSS FOUND!")
else:
    print("\nRESULT: No XSS detected by Dalfox")

# Dalfox might need -f flag or different approach
# Try with --mining or --follow-redirects
print("\n\n=== Try 2: Dalfox with mining ===")
result2 = subprocess.run(
    [dalfox_path, "url", "--url", target + "/vulnerabilities/xss_r/?name=dalfox",
     "--header", "Cookie: " + cookie, "--mining", "dom"],
    capture_output=True, timeout=60)
out2 = (result2.stdout + result2.stderr).decode("utf-8", "replace")
for line in out2.split("\n"):
    l = line.strip()
    if l and ("XSS" in l or "found" in l.lower() or "VULN" in l):
        print("  %s" % l[:150])
