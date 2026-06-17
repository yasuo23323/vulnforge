import urllib.request, http.cookiejar

target = "http://127.0.0.1:3002"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
print("=== Login ===")
data = "username=admin&password=password&Login=Login".encode()
r = opener.open(target + "/login.php", data=data, timeout=5)
print("  Login: HTTP %d" % r.status)

# Probe paths
print()
print("=== Probing paths ===")
for path in ["/setup.php", "/security.php", "/vulnerabilities/sqli/",
             "/vulnerabilities/xss_r/", "/vulnerabilities/exec/",
             "/vulnerabilities/brute/", "/vulnerabilities/"]:
    try:
        r = opener.open(target + path, timeout=5)
        print("  [%s] HTTP %d (%d bytes)" % (path, r.status, len(r.read())))
    except urllib.request.HTTPError as e:
        print("  [%s] HTTP %d" % (path, e.code))
    except Exception as e:
        print("  [%s] Error: %s" % (path, str(e)[:60]))
