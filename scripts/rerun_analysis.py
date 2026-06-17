import json, sys, os, asyncio, time

sys.path.insert(0, "D:\\大论文\\backend")
from app.llm.client import OpenAIClient
from app.llm.strategies import LLMAnalyzer, AnalysisStrategy
from app.scanner.base import ScanResult

STRATEGIES = [("zero_shot", AnalysisStrategy.ZERO_SHOT),("few_shot", AnalysisStrategy.FEW_SHOT),("chain_of_thought", AnalysisStrategy.CHAIN_OF_THOUGHT)]

# Load existing analysis results
with open("scripts/experiment/real_analysis_results.json") as f:
    results = json.load(f)

existing_findings = results.get("findings", [])

# Fix robots.txt: uncertain -> false_positive
for f in existing_findings:
    if "robots.txt" in f.get("type","").lower():
        f["ground_truth"] = "false_positive"
        print("Fixed robots.txt -> FP")

# Add 3 new findings with ground_truth = true_positive
new_raw = [
    {"scanner":"dalfox","type":"xss","severity":"high",
     "url":"http://127.0.0.1:3002/vulnerabilities/xss_r/",
     "desc":"Reflected XSS confirmed by Dalfox",
     "evidence":"Dalfox detected XSS payload reflection on DVWA xss_r page"},
    {"scanner":"sqlmap","type":"sql_injection","severity":"critical",
     "url":"http://127.0.0.1:3002/vulnerabilities/sqli/",
     "desc":"SQL injection confirmed by SQLMap (4 techniques)",
     "evidence":"GET parameter id vulnerable: boolean+error+time+UNION on DVWA"},
    {"scanner":"manual","type":"sql_injection","severity":"critical",
     "url":"http://127.0.0.1:3001/rest/user/login",
     "desc":"SQL injection in email parameter - auth bypass as admin",
     "evidence":"email: test' OR 1=1-- returned admin JWT token with role=admin"},
]

print()
print("Analyzing 3 new findings...")

api_key = open("D:\\大论文\\backend\\.env").read().split("OPENAI_API_KEY=")[1].split("\n")[0].strip()
client = OpenAIClient("deepseek-chat", api_key, base_url="https://api.deepseek.com")
analyzer = LLMAnalyzer(client)

sem = asyncio.Semaphore(3)

async def analyze_one(raw, sname, sval):
    async with sem:
        sr = ScanResult(scanner_name=raw["scanner"], vulnerability_type=raw["type"],
            severity=raw["severity"], url=raw["url"], description=raw["desc"], raw_evidence=raw.get("evidence",""))
        try:
            resp = await asyncio.wait_for(analyzer.analyze_scan_result(sr, sval), timeout=30)
            return sname, resp.verdict, resp.prompt_tokens + resp.completion_tokens
        except:
            return sname, "uncertain", 0

async def main():
    for i, raw in enumerate(new_raw):
        entry = {"scanner":raw["scanner"],"type":raw["type"],"severity":raw["severity"],"url":raw["url"],
                 "desc":raw["desc"],"ground_truth":"true_positive"}
        tasks = [analyze_one(raw, s, v) for s, v in STRATEGIES]
        results = await asyncio.gather(*tasks)
        for sname, verdict, tokens in results:
            entry[sname] = verdict
        existing_findings.append(entry)
        print("  [%d/3] %s %s -> ZS=%s FS=%s CoT=%s" % (i+1, raw["scanner"], raw["type"],
            entry.get("zero_shot","?")[:6], entry.get("few_shot","?")[:6], entry.get("chain_of_thought","?")[:6]))

    # Rebuild output
    output = {"dataset_size":len(existing_findings),"findings":existing_findings}
    
    # Calculate metrics
    for sname, _ in STRATEGIES:
        tp=fp=fn=tn=unc=0
        for f in existing_findings:
            gt = f.get("ground_truth","uncertain")
            pred = f.get(sname,"uncertain")
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
        
        output[sname] = {"verdict_counts":{"true_positive":tp,"false_positive":fp,"uncertain":unc},
            "metrics":{"Precision":pr,"Recall":re,"F1":f1,"Accuracy":acc,"FPR":fpr}}
    
    with open("scripts/experiment/real_analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 70)
    print("  FINAL METRICS (%d findings)" % len(existing_findings))
    print("=" * 70)
    gts = {"true_positive":0,"false_positive":0,"uncertain":0}
    for f in existing_findings: gts[f.get("ground_truth","uncertain")] = gts.get(f.get("ground_truth","uncertain"),0)+1
    print("  Ground truth: TP=%d, FP=%d, Unc=%d" % (gts["true_positive"], gts["false_positive"], gts["uncertain"]))
    print()
    print("  %-12s %-8s %-8s %-8s %-8s %-8s" % ("Strategy","Prec","Rec","F1","Acc","FPR"))
    print("  " + "-" * 60)
    for sname, _ in STRATEGIES:
        m = output[sname]["metrics"]
        print("  %-12s %-8.3f %-8.3f %-8.3f %-8.3f %-8.3f" % (sname, m["Precision"], m["Recall"], m["F1"], m["Accuracy"], m["FPR"]))

asyncio.run(main())
