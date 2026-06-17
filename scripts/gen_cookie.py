import requests, re

s = requests.Session()
r = s.get("http://127.0.0.1:3002/login.php", timeout=5)
# Extract user_token from HTML safely
import html
match = re.search(r"user_token. value=.([^'\"\s]+)", r.text)
token = match.group(1) if match else ""
s.post("http://127.0.0.1:3002/login.php", data={"username":"admin","password":"password","Login":"Login","user_token":token}, timeout=5)

r = s.get("http://127.0.0.1:3002/vulnerabilities/sqli/?id=1", timeout=5)
phpsessid = s.cookies.get("PHPSESSID", "")
print("Page: %d bytes, has admin: %s" % (len(r.text), "First name" in r.text))
print("PHPSESSID: %s" % phpsessid)

with open("D:\\大论文\\sqlmap_cookies.txt", "w") as f:
    f.write("127.0.0.1\tFALSE\t/\tFALSE\t0\tPHPSESSID\t%s\n" % phpsessid)
    f.write("127.0.0.1\tFALSE\t/\tFALSE\t0\tsecurity\tlow\n")
print("Cookie file ready")
