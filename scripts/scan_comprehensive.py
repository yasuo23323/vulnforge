import json, subprocess, os, sys

TOOLS = "D:\\大论文\\tools"
WORDLIST = os.path.join(TOOLS, "common.txt")
TARGETS = {
    "juice-shop": "http://127.0.0.1:3001",
    "dvwa": "http://127.0.0.1:3002",
    "webgoat": "http://127.0.0.1:3003/WebGoat"
}
ALL_FINDINGS = []

def run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return r.stdout.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return ""

for target_name, target_url in TARGETS.items():
    print("\n" + "=" * 60)
    print("  TARGET: %s (%s)" % (target_name, target_url))
    print("=" * 60)

    # 1. NUCLEI - with -j flag for v3.9.0 JSONL output  
    print("\n  [NUCLEI] Scanning %s ..." % target_url, end=" ", flush=True)
    nuclei_out = run([os.path.join(TOOLS, "nuclei.exe"),
                      "-u", target_url, "-j",
                      "-severity", "critical,high,medium",
                      "-timeout", "5", "-retries", "1"], timeout=120)
    n_findings = 0
    for line in nuclei_out.strip().split("\n"):
        line = line.strip()
        if line.startswith("{"):
            try:
                entry = json.loads(line)
                severity = entry.get("info", {}).get("severity", "info")
                ALL_FINDINGS.append({
                    "target": target_name,
                    "scanner": "nuclei",
                    "type": entry.get("info", {}).get("name", "unknown"),
                    "severity": severity if severity in ("critical","high","medium","low","info") else "info",
                    "url": entry.get("matched-at", entry.get("host", target_url)),
                    "evidence": json.dumps(entry, ensure_ascii=False)[:500],
                    "desc": entry.get("info", {}).get("description", ""),
                    "request": entry.get("request", ""),
                    "response_snippet": entry.get("response", "")[:200]
                })
                n_findings += 1
            except json.JSONDecodeError:
                pass
    print("%d findings" % n_findings)
    for f in ALL_FINDINGS:
        if f["target"] == target_name and f["scanner"] == "nuclei":
            print("      %-12s | %s" % (f["type"][:30], f["url"][:60]))

    # 2. FFUF - directory scan
    print("\n  [FFUF] Directory scanning %s ..." % target_url, end=" ", flush=True)
    ffuf_out = run([os.path.join(TOOLS, "ffuf.exe"), "-u", target_url.rstrip("/") + "/FUZZ",
                    "-w", WORDLIST, "-t", "10", "-s", "-ac"], timeout=30)
    ffuf_findings = 0
    for line in ffuf_out.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("::") and not line.startswith("["):
            ffuf_findings += 1
            ALL_FINDINGS.append({
                "target": target_name,
                "scanner": "ffuf",
                "type": "directory_enumeration",
                "severity": "info",
                "url": target_url.rstrip("/") + "/" + line,
                "evidence": line,
                "desc": "Discovered path via directory brute-force"
            })
    print("%d findings" % ffuf_findings)

    # 3. DALFOX - XSS scan  
    print("\n  [DALFOX] XSS scanning %s ..." % target_url, end=" ", flush=True)
    if target_name == "juice-shop":
        # Try search endpoint (known to reflect input)
        dalfox_out = run([os.path.join(TOOLS, "dalfox.exe"), "url", "--url",
                          target_url + "/rest/products/search?q=", "--silence"], timeout=60)
        dalfox_findings = 0
        for line in dalfox_out.strip().split("\n"):
            if line.strip() and "XSS" in line:
                dalfox_findings += 1
                ALL_FINDINGS.append({
                    "target": target_name, "scanner": "dalfox", "type": "xss",
                    "severity": "medium", "url": target_url + "/rest/products/search?q=",
                    "evidence": line, "desc": "XSS vulnerability detected"
                })
        print("%d findings" % dalfox_findings)
    else:
        print("skipped (need login/auth)")

# SUMMARY
print("\n\n" + "=" * 60)
print("COMPREHENSIVE SCAN SUMMARY")
print("=" * 60)
from collections import Counter
target_counts = Counter(f["target"] for f in ALL_FINDINGS)
scanner_counts = Counter(f["scanner"] for f in ALL_FINDINGS)
type_counts = Counter(f["type"] for f in ALL_FINDINGS)

for t in sorted(target_counts):
    print("\n  %s (%d findings):" % (t, target_counts[t]))
    for f in ALL_FINDINGS:
        if f["target"] == t:
            print("    [%s] %s | %s" % (f["scanner"], f["type"][:25], f["url"][:60]))

print("\n  Total findings: %d" % len(ALL_FINDINGS))
print("  By tool: %s" % dict(scanner_counts))
print("  By type: %s" % dict(type_counts))

outpath = "scripts/experiment/real_findings_comprehensive.json"
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(ALL_FINDINGS, f, indent=2, ensure_ascii=False)
print("\n  Saved to: %s" % outpath)
