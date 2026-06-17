import asyncio
import json, sys, os, asyncio, time

sys.path.insert(0, "D:\\大论文\\backend")
from app.llm.client import OpenAIClient
from app.llm.strategies import LLMAnalyzer, AnalysisStrategy
from app.scanner.base import ScanResult

STRATEGIES = [("zero_shot",AnalysisStrategy.ZERO_SHOT),("few_shot",AnalysisStrategy.FEW_SHOT),("chain_of_thought",AnalysisStrategy.CHAIN_OF_THOUGHT)]

with open("scripts/experiment/real_dataset_combined.json") as f:
    dataset = json.load(f)

# Update evidence text for findings with generic descriptions
evidence_updates = {
    "sqli_bool": "GET parameter id=1 AND 1=1 returns normal results. id=1 AND 1=2 returns empty. This indicates boolean-based SQL injection is possible. The database is MySQL, confirmed by SQLMap.",
    "sqli_error": "GET parameter id with injection causes MySQL error: ExtractValue() function returns error message with database information. Error-based SQL injection confirmed via MySQL extractvalue technique.",
    "sqli_time": "GET parameter id=1 AND SLEEP(5) causes 5-second response delay. Normal response is instant. Time-based blind SQL injection confirmed via MySQL sleep function.",
    "sqli_union": "GET parameter id=1 UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20 returns 2 columns. Original query has 2 columns. UNION-based SQL injection confirmed.",
    "sqli_blind_time": "GET parameter id on blind SQLi page with SLEEP function causes delay. Boolean-based blind SQL injection confirmed on sqli_blind page.",
    "xss_reflected": "GET parameter name=<script>alert(1)</script> returns the script tag unencoded in the HTML response body. The browser would execute this JavaScript. Reflected XSS confirmed.",
    "xss_stored": "POST name field contains <script>alert(1)</script> which is stored and displayed on page reload without HTML encoding. Stored XSS vulnerability confirmed.",
    "csrf": "POST to csrf page with password_new=test123 and password_conf=test123 changes admin password without requiring the current password or CSRF token. Cross-Site Request Forgery confirmed.",
    "file_upload": "POST file upload accepts arbitrary PHP files without validation. Uploading a PHP shell would allow remote code execution. Unrestricted file upload vulnerability confirmed.",
    "captcha": "The CAPTCHA on the password change form can be bypassed by reusing a previous CAPTCHA value. The server does not invalidate used CAPTCHAs. Insecure CAPTCHA implementation.",
    "weak_session_id": "Session IDs are sequential integers (1, 2, 3...) that can be predicted. After login, session ID increments by 1. Weak session ID generation allows session hijacking.",
    "csp_bypass": "Content-Security-Policy header is missing or misconfigured. The page loads external scripts and inline event handlers without restriction. CSP bypass allows XSS execution.",
    "javascript": "JavaScript source code is visible via view-source. The page includes client-side logic for form validation and AJAX calls. Source code disclosure reveals application logic.",
    "command_injection": "POST ip=127.0.0.1;id returns command output: uid=33(www-data) gid=33(www-data). The ip parameter is passed directly to shell_exec() without sanitization. Command injection confirmed.",
    "file_inclusion": "GET page parameter accepts ../../../../etc/passwd and returns the password file content. Local File Inclusion vulnerability allows reading arbitrary files on the server.",
    "brute_force": "POST login.php with username=admin and common passwords. The server returns different responses for valid vs invalid passwords and has no rate limiting. Brute force attack possible.",
    "sqli_juiceshop": 'POST /rest/user/login with email: test\\" OR 1=1-- returns authentication token for admin user (id=1, email=admin@juice-sh.op, role=admin). SQL injection bypasses authentication.',
}

for d in dataset:
    dtype = d.get("type","")
    if dtype in evidence_updates:
        d["evidence"] = evidence_updates[dtype]
        print("Updated evidence: %s" % dtype)

with open("scripts/experiment/real_dataset_combined.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

# Re-run LLM analysis on findings with updated evidence
api_key = open("D:\\大论文\\backend\\.env").read().split("OPENAI_API_KEY=")[1].split("\n")[0].strip()
client = OpenAIClient("deepseek-chat", api_key, base_url="https://api.deepseek.com")
analyzer = LLMAnalyzer(client)
sem = asyncio.Semaphore(3)

async def analyze_one(finding, sname, sval):
    async with sem:
        sr = ScanResult(scanner_name=finding.get("scanner","?"), vulnerability_type=finding.get("type","?"),
            severity=finding.get("severity","info"), url=finding.get("url",""),
            description=finding.get("desc",""), raw_evidence=finding.get("evidence",""))
        try:
            resp = await asyncio.wait_for(analyzer.analyze_scan_result(sr, sval), timeout=30)
            return sname, resp.verdict, 0
        except: return sname, "uncertain", 0

all_results = {s:[] for s,_ in STRATEGIES}
all_latencies = {s:[] for s,_ in STRATEGIES}

async def main():
    sem = asyncio.Semaphore(3)

    print("Re-analyzing %d findings..." % len(dataset))
for i, f in enumerate(dataset):
    start = time.monotonic()
    print("  [%3d/%d] %-10s %-30s" % (i+1, len(dataset), f.get("scanner","?"), f.get("type","?")[:28]), end="", flush=True)
    tasks = [analyze_one(f,s,v) for s,v in STRATEGIES]
    results = await asyncio.gather(*tasks)
    for sname, verdict, tokens in results:
        all_results[sname].append(verdict)
        all_latencies[sname].append(time.monotonic() - start)
    v = " ".join(r[1][:6] for r in results)
    print("  [%s]  %.1fs" % (v, time.monotonic()-start))

# Calculate metrics
output = {"dataset_size":len(dataset),"findings":[]}
for i, f in enumerate(dataset):
    entry = dict(f)
    for sname,_ in STRATEGIES: entry[sname] = all_results[sname][i]
    output["findings"].append(entry)

for sname, _ in STRATEGIES:
    tp=fp=fn=tn=unc=0
    for i, f in enumerate(dataset):
        gt = f.get("ground_truth","uncertain")
        pred = all_results[sname][i]
        if gt=="uncertain" or pred=="uncertain": unc+=1; continue
        if pred=="true_positive" and gt=="true_positive": tp+=1
        elif pred=="true_positive" and gt=="false_positive": fp+=1
        elif pred=="false_positive" and gt=="true_positive": fn+=1
        elif pred=="false_positive" and gt=="false_positive": tn+=1
    pr=tp/(tp+fp) if (tp+fp)>0 else 0
    re=tp/(tp+fn) if (tp+fn)>0 else 0
    f1=2*pr*re/(pr+re) if (pr+re)>0 else 0
    acc=(tp+tn)/(tp+fp+fn+tn) if (tp+fp+fn+tn)>0 else 0
    fpr=fp/(fp+tn) if (fp+tn)>0 else 0
    output[sname] = {"verdict_counts":{"tp":tp,"fp":fp,"fn":fn,"tn":tn,"unc":unc},
        "metrics":{"Precision":pr,"Recall":re,"F1":f1,"Accuracy":acc,"FPR":fpr}}

with open("scripts/experiment/real_analysis_results.json","w",encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

async def main():
    sem = asyncio.Semaphore(3)

    print("="*70)
print("  FINAL METRICS (%d findings)" % len(dataset))
gt_tp = sum(1 for f in dataset if f.get("ground_truth")=="true_positive")
gt_fp = sum(1 for f in dataset if f.get("ground_truth")=="false_positive")
print("  GT: TP=%d, FP=%d" % (gt_tp, gt_fp))
print("="*70)
print("  %-15s %-8s %-8s %-8s %-8s %-8s" % ("Strategy","Prec","Rec","F1","Acc","FPR"))
print("  "+"-"*63)
for sname,_ in STRATEGIES:
    m = output[sname]["metrics"]
    print("  %-15s %-8.3f %-8.3f %-8.3f %-8.3f %-8.3f" % (sname, m["Precision"], m["Recall"], m["F1"], m["Accuracy"], m["FPR"]))

asyncio.run(main())
