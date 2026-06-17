import json, os

all_findings = []

# 1. Parse FFUF results
for target_tag, file in [("juice-shop","ffuf_juice.txt"),("dvwa","ffuf_dvwa.txt"),("webgoat","ffuf_webgoat.txt")]:
    path = "scripts/experiment/" + file
    if not os.path.exists(path): continue
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("::") and not line.startswith("["):
                port = {"juice-shop":"3001","dvwa":"3002","webgoat":"3003"}[target_tag]
                all_findings.append({
                    "target": target_tag, "scanner": "ffuf",
                    "type": "directory_enumeration", "severity": "info",
                    "url": "http://127.0.0.1:" + port + "/" + line,
                    "desc": "Discovered path: " + line,
                    "evidence": line
                })

# 2. Parse Nuclei results
for target_tag, file in [("juice-shop","nuclei_juice.jsonl"),("dvwa","nuclei_dvwa.jsonl")]:
    path = "scripts/experiment/" + file
    if not os.path.exists(path): continue
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("{"): continue
            try:
                e = json.loads(line)
                sev = e.get("info",{}).get("severity","info")
                all_findings.append({
                    "target": target_tag, "scanner": "nuclei",
                    "type": e.get("info",{}).get("name","unknown"),
                    "severity": sev if sev in ("critical","high","medium","low","info") else "info",
                    "url": e.get("matched-at",""),
                    "desc": (e.get("info",{}).get("description","") or "")[:100],
                    "evidence": json.dumps(e, ensure_ascii=False)[:300]
                })
            except: continue

print("Total raw findings: %d" % len(all_findings))
print()
severity_counts = {}
target_counts = {}
for f in all_findings:
    sev = f["severity"]
    tgt = f["target"]
    severity_counts[sev] = severity_counts.get(sev, 0) + 1
    target_counts[tgt] = target_counts.get(tgt, 0) + 1

print("By target:")
for t,c in sorted(target_counts.items()):
    print("  %s: %d" % (t, c))

print()
print("By severity:")
for s,c in sorted(severity_counts.items()):
    print("  %s: %d" % (s, c))

with open("scripts/experiment/all_raw_findings.json", "w", encoding="utf-8") as f:
    json.dump(all_findings, f, indent=2, ensure_ascii=False)
print()
print("Saved to scripts/experiment/all_raw_findings.json")
