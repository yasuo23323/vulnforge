import sys, subprocess, json, os, time, re
sys.path.insert(0, "D:\\大论文")
sys.path.insert(0, "D:\\大论文\\backend")

from app.scanner.base import ScanResult
from app.scanner.parsers import parse_nuclei_output, parse_dalfox_output, parse_ffuf_output
from app.scanner.parsers import parse_sqlmap_output

TOOLS_DIR = "D:\\大论文\\tools"
TARGETS = {
    "juice-shop": "http://127.0.0.1:3001",
    "dvwa": "http://127.0.0.1:3002",
    "webgoat": "http://127.0.0.1:3003",
}

def run_cmd(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        return ""

results = {}

for target_name, target_url in TARGETS.items():
    print("\n" + "=" * 70)
    print("  Scanning: %s (%s)" % (target_name, target_url))
    print("=" * 70)
    results[target_name] = {}

    # 1. Dalfox - XSS scan
    print("  [dalfox] Running XSS scan...", end="", flush=True)
    out = run_cmd([os.path.join(TOOLS_DIR, "dalfox.exe"), "url", "--url", target_url, "--silence"])
    findings = parse_dalfox_output(out)
    results[target_name]["dalfox"] = [vars(f) for f in findings]
    print(" %d findings" % len(findings))

    # 2. FFUF - directory brute-force
    print("  [ffuf] Running directory scan...", end="", flush=True)
    wordlist = os.path.join(TOOLS_DIR, "common.txt")
    if not os.path.exists(wordlist):
        # Create a minimal wordlist for testing
        with open(wordlist, "w") as f:
            f.write("\n".join(["admin", "login", "api", "rest", "search", "users",
                               ".git", ".env", "config", "backup", "robots.txt",
                               "sitemap.xml", "swagger", "docs"]))
    out = run_cmd([os.path.join(TOOLS_DIR, "ffuf.exe"), "-u", target_url + "/FUZZ",
                   "-w", wordlist, "-c", "-t", "10", "-ac"])
    findings = parse_ffuf_output(out)
    results[target_name]["ffuf"] = [vars(f) for f in findings]
    print(" %d findings" % len(findings))

    # 3. Nuclei - general vuln scan (skip if localhost has resolution issues)
    print("  [nuclei] Running vulnerability scan...", end="", flush=True)
    # Try with -j flag for JSONL output
    out = run_cmd([os.path.join(TOOLS_DIR, "nuclei.exe"), "-u", target_url, "-j",
                   "-timeout", "5", "-retries", "1"], timeout=60)
    findings = parse_nuclei_output(out)
    results[target_name]["nuclei"] = [vars(f) for f in findings]
    print(" %d findings" % len(findings))

# Print summary
print("\n" + "=" * 70)
print("  SCAN SUMMARY")
print("=" * 70)
total = 0
for target_name, scanners in results.items():
    print("\n  %s:" % target_name)
    for scanner_name, findings in scanners.items():
        print("    %s: %d findings" % (scanner_name, len(findings)))
        total += len(findings)
        for f in findings[:5]:  # Show first 5
            print("      - %s | %s | %s" % (f["vulnerability_type"], f["severity"], f["url"][:60]))
print("\n  Total findings: %d" % total)

# Save all results
with open("scripts/experiment/real_scan_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("\n  Saved to: scripts/experiment/real_scan_results.json")
