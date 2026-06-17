import json

with open("scripts/experiment/real_analysis_results.json") as f:
    data = json.load(f)

findings = data.get("findings", [])
print("=" * 80)
print("  GROUND TRUTH VERIFICATION - 85 findings")
print("=" * 80)

groups = {}
for f in findings:
    key = (f.get("scanner","?"), f.get("type","?"))
    groups.setdefault(key, []).append(f)

sorted_groups = sorted(groups.items(), key=lambda x: (0 if x[0][0]=="ffuf" else 1, x[0][1]))

for (scanner, ftype), items in sorted_groups:
    gt = items[0].get("ground_truth", "?") if items else "?"
    
    if scanner == "ffuf":
        sensitive = ["config", "phpinfo", ".git", "metrics", "admin", "backup", "database", "private", "secret"]
        sensitive_matched = [s for s in sensitive if any(s in item.get("url","").lower() for item in items)]
        if sensitive_matched:
            reason = "Sensitive path: " + ", ".join(sensitive_matched)
        else:
            reason = "Normal application path (info only)"
    else:
        tp_ks = ["default login", "prometheus", "sensitive config", "missing security", "httponly", "secure attribute", "samesite", "deprecated feature", "readme.md", "gitignore", "swagger"]
        fp_ks = ["dameng", "ikev2", "caa record", "waf detection", "dom eventlistener", "fingerprinthub", "wappalyzer", "security.txt", "x-recruiting", "owasp juice shop"]
        t = ftype.lower()
        if any(k in t for k in tp_ks):
            reason = "Security concern (info disclosure / misconfiguration)"
        elif any(k in t for k in fp_ks):
            reason = "Technology fingerprint / standard file / wrong protocol"
        else:
            reason = "Best guess - review needed"
    
    print()
    print("--- %s | %s ---" % (scanner, ftype[:50]))
    print("  GT: %s | %s" % (gt, reason))
    print("  Count: %d" % len(items))
    for i, item in enumerate(items):
        z = (item.get("zero_shot","?") or "?")[:6]
        fv = (item.get("few_shot","?") or "?")[:6]
        c = (item.get("chain_of_thought","?") or "?")[:6]
        url = item.get("url","") or ""
        if url:
            path_only = url.split("/", 3)[-1] if "//" in url else url[:40]
        else:
            path_only = (item.get("desc","") or "")[:40]
        print("    [%d] %-30s ZS=%-6s FS=%-6s CoT=%-6s" % (i, path_only[:30], z, fv, c))

print()
print("=" * 80)
print("  Say 'keep all' if correct.")
print("  Say 'change type \"name\" to TP/FP' for a group.")
print("  Say 'change finding N to TP/FP' for a single finding.")
print("=" * 80)
