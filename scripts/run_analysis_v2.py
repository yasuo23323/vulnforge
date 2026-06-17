import json, sys, os, asyncio, time
sys.path.insert(0, "D:\\大论文\\backend")
from app.llm.client import OpenAIClient
from app.llm.strategies import LLMAnalyzer, AnalysisStrategy
from app.scanner.base import ScanResult

STRATEGIES = [("zero_shot", AnalysisStrategy.ZERO_SHOT), ("few_shot", AnalysisStrategy.FEW_SHOT), ("chain_of_thought", AnalysisStrategy.CHAIN_OF_THOUGHT)]

with open("scripts/experiment/real_dataset_combined.json") as f:
    dataset = json.load(f)

api_key = open("D:\\大论文\\backend\\.env").read().split("OPENAI_API_KEY=")[1].split("\n")[0].strip()
client = OpenAIClient("deepseek-chat", api_key, base_url="https://api.deepseek.com")
analyzer = LLMAnalyzer(client)

async def analyze_one(sr, sname, sval, sem):
    async with sem:
        try:
            resp = await asyncio.wait_for(analyzer.analyze_scan_result(sr, sval), timeout=30)
            return sname, resp.verdict
        except:
            return sname, "uncertain"

async def main():
    sem = asyncio.Semaphore(3)
    all_results = {s:[] for s,_ in STRATEGIES}
    for i, f in enumerate(dataset):
        sr = ScanResult(scanner_name=f.get("scanner","?"), vulnerability_type=f.get("type","?"),
            severity=f.get("severity","info"), url=f.get("url",""),
            description=f.get("desc",""), raw_evidence=f.get("evidence",""))
        tasks = [analyze_one(sr, s, v, sem) for s, v in STRATEGIES]
        results = await asyncio.gather(*tasks)
        for sname, verdict in results:
            all_results[sname].append(verdict)
        if (i+1) % 10 == 0:
            print("  " + str(i+1) + "/" + str(len(dataset)) + " done")
    
    output = {"dataset_size": len(dataset), "findings": []}
    for i, f in enumerate(dataset):
        entry = dict(f)
        for sname,_ in STRATEGIES:
            entry[sname] = all_results[sname][i]
        output["findings"].append(entry)
    
    for sname, _ in STRATEGIES:
        tp=fp=fn=tn=unc=0
        for i, f in enumerate(dataset):
            gt = f.get("ground_truth", "uncertain")
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
        output[sname] = {"metrics": {"Precision": pr, "Recall": re, "F1": f1, "Accuracy": acc, "FPR": fpr}}
    
    with open("scripts/experiment/real_analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("")
    print("="*70)
    print("  FINAL METRICS (" + str(len(dataset)) + " findings)")
    gt_tp = sum(1 for f in dataset if f.get("ground_truth")=="true_positive")
    gt_fp = sum(1 for f in dataset if f.get("ground_truth")=="false_positive")
    print("  GT: TP=" + str(gt_tp) + ", FP=" + str(gt_fp))
    print("="*70)
    h = "  %-15s %-8s %-8s %-8s %-8s %-8s" % ("Strategy", "Prec", "Rec", "F1", "Acc", "FPR")
    print(h)
    print("  " + "-"*63)
    for sname,_ in STRATEGIES:
        m = output[sname]["metrics"]
        line = "  %-15s %-8.3f %-8.3f %-8.3f %-8.3f %-8.3f" % (sname, m["Precision"], m["Recall"], m["F1"], m["Accuracy"], m["FPR"])
        print(line)

asyncio.run(main())
