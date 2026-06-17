import sys, asyncio, os, time, json, math
sys.path.insert(0, "D:\\大论文")
sys.path.insert(0, "D:\\大论文\\scripts")
sys.path.insert(0, "D:\\大论文\\backend")
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)

from app.llm.client import OpenAIClient
from app.llm.strategies import LLMAnalyzer, AnalysisStrategy
from app.scanner.base import ScanResult
from scripts.experiment.dataset import DATASET

STRATEGIES = [
    ("zero_shot", AnalysisStrategy.ZERO_SHOT),
    ("few_shot", AnalysisStrategy.FEW_SHOT),
    ("chain_of_thought", AnalysisStrategy.CHAIN_OF_THOUGHT),
]

METRIC_LABELS = ["Precision", "Recall", "F1", "Accuracy", "FPR", "Specificity", "NPV"]


def confusion_matrix(verdicts, ground_truth):
    tp = sum(1 for v,g in zip(verdicts,ground_truth) if v=="true_positive" and g=="true_positive")
    fp = sum(1 for v,g in zip(verdicts,ground_truth) if v=="true_positive" and g=="false_positive")
    fn = sum(1 for v,g in zip(verdicts,ground_truth) if v=="false_positive" and g=="true_positive")
    tn = sum(1 for v,g in zip(verdicts,ground_truth) if v=="false_positive" and g=="false_positive")
    uc = sum(1 for v in verdicts if v=="uncertain")
    return tp, fp, fn, tn, uc


def calc_metrics(tp, fp, fn, tn):
    pr = tp/(tp+fp) if (tp+fp)>0 else 0
    re = tp/(tp+fn) if (tp+fn)>0 else 0
    f1 = 2*pr*re/(pr+re) if (pr+re)>0 else 0
    acc = (tp+tn)/(tp+fp+fn+tn) if (tp+fp+fn+tn)>0 else 0
    fpr = fp/(fp+tn) if (fp+tn)>0 else 0
    spec = tn/(tn+fp) if (tn+fp)>0 else 0
    npv = tn/(tn+fn) if (tn+fn)>0 else 0
    return pr, re, f1, acc, fpr, spec, npv


def mcnemar_test(v1, v2, gt):
    b = sum(1 for v1i, v2i, gi in zip(v1, v2, gt) if v1i != gi and v2i == gi)
    c = sum(1 for v1i, v2i, gi in zip(v1, v2, gt) if v1i == gi and v2i != gi)
    n = b + c
    if n < 10:
        from math import comb
        p = 2 * min(0.5**n * sum(comb(n,k) for k in range(min(b,c)+1)), 1)
        return 0.0, "exact binomial p=%.4f" % p
    chi2 = (abs(b - c) - 1) ** 2 / n
    p = 1 - math.erf(math.sqrt(chi2/2))
    return chi2, "chi2=%.3f, p=%.4f" % (chi2, p)


async def run_experiment():
    print("=" * 80)
    print("  VulnForge Experiment Framework v2")
    gt_tp = sum(1 for f in DATASET if f["gt"] == "true_positive")
    gt_fp = sum(1 for f in DATASET if f["gt"] == "false_positive")
    print("  Dataset: %d findings (TP=%d, FP=%d)" % (len(DATASET), gt_tp, gt_fp))
    print("=" * 80)

    api_key = open("D:\\大论文\\backend\\.env").read().split("OPENAI_API_KEY=")[1].split("\n")[0].strip()
    client = OpenAIClient("deepseek-chat", api_key, base_url="https://api.deepseek.com")
    analyzer = LLMAnalyzer(client)

    gt = [f["gt"] for f in DATASET]
    vuln_types = sorted(set(f["vuln_type"] for f in DATASET))
    all_results = {}
    all_latencies = {}
    all_tokens = {}

    for sname, _ in STRATEGIES:
        all_results[sname] = []
        all_latencies[sname] = []
        all_tokens[sname] = []

    sem = asyncio.Semaphore(3)

    async def analyze_one(finding, sname, sval):
        async with sem:
            sr = ScanResult(
                scanner_name=finding["scanner"],
                vulnerability_type=finding["vuln_type"],
                severity=finding["severity"],
                url=finding["url"],
                description=finding["desc"],
                raw_evidence=finding["evidence"]
            )
            try:
                resp = await asyncio.wait_for(analyzer.analyze_scan_result(sr, sval), timeout=30)
                return sname, resp.verdict, resp.prompt_tokens + resp.completion_tokens
            except asyncio.TimeoutError:
                return sname, "uncertain", 0
            except Exception as e:
                return sname, "uncertain", 0

    print()
    print("-" * 80)
    for i, f in enumerate(DATASET):
        start_time = time.monotonic()
        line = "  [%2d/%d] %8s | %-20s | " % (i+1, len(DATASET), f["scanner"], f["vuln_type"])
        print(line, end="", flush=True)

        tasks = [analyze_one(f, sname, sval) for sname, sval in STRATEGIES]
        results = await asyncio.gather(*tasks)

        for sname, verdict, tokens in results:
            all_results[sname].append(verdict)
            all_tokens[sname].append(tokens)

        elapsed = time.monotonic() - start_time
        for sname, _, _ in results:
            all_latencies[sname].append(elapsed)

        v_str = " ".join(r[1][:6] for r in results)
        gt_mark = f["gt"][:4]
        print("  %s  [%s]  %.1fs" % (gt_mark, v_str, elapsed))

        if (i + 1) % 12 == 0:
            _save_intermediate(all_results, all_latencies, all_tokens, gt, vuln_types)
            print("  -> intermediate results saved")

    _save_intermediate(all_results, all_latencies, all_tokens, gt, vuln_types)
    _print_and_export(all_results, all_latencies, all_tokens, gt, vuln_types)


def _save_intermediate(all_results, all_latencies, all_tokens, gt, vuln_types):
    export = _build_export(all_results, all_latencies, all_tokens, gt, vuln_types)
    with open("scripts/experiment/results.json", "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)


def _build_export(all_results, all_latencies, all_tokens, gt, vuln_types):
    gt_tp = gt.count("true_positive")
    gt_fp = gt.count("false_positive")
    export = {
        "dataset_size": len(gt),
        "ground_truth_distribution": {"true_positive": gt_tp, "false_positive": gt_fp},
        "vulnerability_types": vuln_types,
        "results": {}
    }
    for sname, _ in STRATEGIES:
        v = all_results[sname]
        tp, fp, fn, tn, uc = confusion_matrix(v, gt)
        metrics = calc_metrics(tp, fp, fn, tn)
        ml = sum(all_latencies[sname]) / max(len(all_latencies[sname]), 1)
        mt = sum(all_tokens[sname]) / max(len(all_tokens[sname]), 1)
        export["results"][sname] = {
            "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
            "metrics": dict(zip(METRIC_LABELS, metrics)),
            "avg_latency": ml,
            "avg_tokens": mt,
        }
    return export


def _print_and_export(all_results, all_latencies, all_tokens, gt, vuln_types):
    print()
    print("=" * 80)
    print("  OVERALL METRICS")
    print("=" * 80)
    print("%-20s %-8s %-8s %-8s %-8s %-8s %-8s %-8s %-8s %-5s" % (
        "Strategy", "Prec", "Rec", "F1", "Acc", "FPR", "Spec", "NPV", "Avg Lat", "Unc"))
    print("-" * 80)

    for sname, _ in STRATEGIES:
        tp,fp,fn,tn,uc = confusion_matrix(all_results[sname], gt)
        m = calc_metrics(tp, fp, fn, tn)
        al = sum(all_latencies[sname]) / max(len(all_latencies[sname]), 1)
        print("%-20s %-8.3f %-8.3f %-8.3f %-8.3f %-8.3f %-8.3f %-8.3f %-8.2f %-5d" % (
            sname, m[0], m[1], m[2], m[3], m[4], m[5], m[6], al, uc))

    # McNemar's Test
    print()
    print("-" * 80)
    print("  MCNEMAR'S TEST")
    for i, (s1, _) in enumerate(STRATEGIES):
        for j, (s2, _) in enumerate(STRATEGIES):
            if i >= j:
                continue
            stat, desc = mcnemar_test(all_results[s1], all_results[s2], gt)
            print("  %18s vs %-18s  %s" % (s1, s2, desc))

    # Stratified Analysis
    print()
    print("-" * 80)
    print("  STRATIFIED ANALYSIS")
    print("-" * 80)
    for vtype in vuln_types:
        idx = [i for i,f in enumerate(DATASET) if f["vuln_type"] == vtype]
        v_gt = [gt[i] for i in idx]
        print()
        print("  [%s] (%d findings)" % (vtype, len(idx)))
        print("  %-20s %-8s %-8s %-8s %-8s" % ("Strategy", "Prec", "Rec", "F1", "Acc"))
        for sname, _ in STRATEGIES:
            vp = [all_results[sname][i] for i in idx]
            tp,fp,fn,tn,uc = confusion_matrix(vp, v_gt)
            m = calc_metrics(tp, fp, fn, tn)
            print("  %-20s %-8.3f %-8.3f %-8.3f %-8.3f" % (
                sname, m[0], m[1], m[2], m[3]))

    export = _build_export(all_results, all_latencies, all_tokens, gt, vuln_types)
    with open("scripts/experiment/results.json", "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)
    print()
    print("  Done -> scripts/experiment/results.json")
    print("=" * 80)


asyncio.run(run_experiment())
