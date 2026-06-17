import json, sys, os, asyncio, time, math, re

sys.path.insert(0, "D:\\大论文\\backend")
from app.llm.client import OpenAIClient
from app.llm.strategies import LLMAnalyzer, AnalysisStrategy
from app.scanner.base import ScanResult

STRATEGIES = [
    ("zero_shot", AnalysisStrategy.ZERO_SHOT),
    ("few_shot", AnalysisStrategy.FEW_SHOT),
    ("chain_of_thought", AnalysisStrategy.CHAIN_OF_THOUGHT),
]

with open("scripts/experiment/real_dataset_combined.json") as f:
    DATASET = json.load(f)

print("=" * 60)
print("  LLM Analysis on %d Real Scanner Findings" % len(DATASET))
print("=" * 60)

api_key = open("D:\\大论文\\backend\\.env").read().split("OPENAI_API_KEY=")[1].split("\n")[0].strip()
client = OpenAIClient("deepseek-chat", api_key, base_url="https://api.deepseek.com")
analyzer = LLMAnalyzer(client)

all_results = {s: [] for s, _ in STRATEGIES}
all_latencies = {s: [] for s, _ in STRATEGIES}
all_tokens = {s: [] for s, _ in STRATEGIES}

sem = asyncio.Semaphore(3)

async def analyze_one(finding, sname, sval):
    async with sem:
        sr = ScanResult(
            scanner_name=finding.get("scanner", "unknown"),
            vulnerability_type=finding.get("type", "unknown"),
            severity=finding.get("severity", "info"),
            url=finding.get("url", ""),
            description=finding.get("desc", ""),
            raw_evidence=finding.get("evidence", ""),
        )
        try:
            resp = await asyncio.wait_for(analyzer.analyze_scan_result(sr, sval), timeout=30)
            return sname, resp.verdict, resp.prompt_tokens + resp.completion_tokens
        except asyncio.TimeoutError:
            return sname, "uncertain", 0
        except Exception as e:
            return sname, "uncertain", 0

async def main():
    for i, f in enumerate(DATASET):
        start = time.monotonic()
        tag = "%s %s %s" % (f.get("scanner","?")[:6], f.get("type","?")[:28], f.get("severity","?")[:4])
        print("  [%3d/%d] %s" % (i+1, len(DATASET), tag), end="", flush=True)

        tasks = [analyze_one(f, s, v) for s, v in STRATEGIES]
        results = await asyncio.gather(*tasks)

        for sname, verdict, tokens in results:
            all_results[sname].append(verdict)
            all_tokens[sname].append(tokens)

        elapsed = time.monotonic() - start
        for sname, _, _ in results:
            all_latencies[sname].append(elapsed)

        v_str = " ".join(r[1][:6] for r in results)
        print("  [%s]  %.1fs" % (v_str, elapsed))

        if (i + 1) % 20 == 0:
            _save_intermediate()

    _save_final()

def _save_intermediate():
    output = _build_output()
    with open("scripts/experiment/real_analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print("    -> intermediate saved")

def _build_output():
    detailed = []
    for i, f in enumerate(DATASET):
        entry = {"index":i,"scanner":f.get("scanner"),"type":f.get("type"),"severity":f.get("severity"),"url":f.get("url")}
        for sname, _ in STRATEGIES:
            entry[sname] = all_results[sname][i] if i < len(all_results[sname]) else "pending"
        detailed.append(entry)
    output = {"dataset_size":len(DATASET),"findings":detailed}
    for sname, _ in STRATEGIES:
        output[sname] = {
            "verdict_counts":{
                "true_positive":all_results[sname].count("true_positive"),
                "false_positive":all_results[sname].count("false_positive"),
                "uncertain":all_results[sname].count("uncertain"),
            },
            "avg_latency": sum(all_latencies[sname]) / max(len(all_latencies[sname]), 1) if all_latencies[sname] else 0,
        }
    return output

def _save_final():
    output = _build_output()
    with open("scripts/experiment/real_analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print()
    print("=" * 60)
    print("  ANALYSIS COMPLETE")
    for sname, _ in STRATEGIES:
        tc = output[sname]["verdict_counts"]
        print("  %s: TP=%d FP=%d Unc=%d" % (sname, tc["true_positive"], tc["false_positive"], tc["uncertain"]))
    print("  Output: scripts/experiment/real_analysis_results.json")
    print("=" * 60)

asyncio.run(main())
