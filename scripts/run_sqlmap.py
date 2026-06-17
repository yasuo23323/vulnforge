import urllib.request, json, subprocess, sys

target = "http://127.0.0.1:3001"
findings = []

# === SQLMap against login endpoint ===
print("=== SQLMap: Login endpoint SQL injection ===")
cmd = [sys.executable, "-m", "sqlmap", "-u", target + "/rest/user/login",
       "--data-raw", '{"email":"test@test.com","password":"test"}',
       "--headers", "Content-Type: application/json",
       "--batch", "--level", "3", "--risk", "2",
       "--output-dir", "sqlmap_login",
       "--flush-session", "--answers", "follow=N"]
try:
    r = subprocess.run(cmd, capture_output=True, timeout=300)
    out = (r.stdout + r.stderr).decode("utf-8", "replace")
    for line in out.split("\n"):
        l = line.strip().lower()
        if any(kw in l for kw in ["parameter:", "injectable", "vulnerable", "payload:", "type:"]):
            print("  %s" % line.strip()[:120])
            if "injectable" in l or "vulnerable" in l or "payload" in l:
                findings.append({
                    "scanner": "sqlmap", "type": "sql_injection", "severity": "critical",
                    "url": target + "/rest/user/login",
                    "desc": "SQL injection confirmed by SQLMap: %s" % line.strip()[:80],
                    "evidence": line.strip()
                })
except subprocess.TimeoutExpired:
    print("  SQLMap timed out")
except Exception as e:
    print("  Error: %s" % e)

# Print summary
print()
print("=" * 60)
print("FINAL FINDINGS")
print("=" * 60)
for f in findings:
    print("  [%s] %s | %s" % (f["scanner"], f["type"], f["desc"][:80]))

# Save
with open("scripts/experiment/real_findings_sqlmap.json", "w", encoding="utf-8") as f:
    json.dump(findings, f, indent=2, ensure_ascii=False)
print("\nSaved to: scripts/experiment/real_findings_sqlmap.json")
