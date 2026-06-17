import sys, asyncio, os, time, logging
sys.path.insert(0, "D:\\大论文\\backend")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
os.environ["RUNTIME_LOG_LEVEL"] = "ERROR"

from app.database import async_session_factory, init_db
from app.models import Severity
from app.llm.client import OpenAIClient
from app.llm.strategies import LLMAnalyzer, AnalysisStrategy
from app.scanner.base import ScanResult

SCAN_RESULTS = [
    {"scanner": "nuclei", "type": "sql_injection", "sev": "high",
     "url": "http://testphp.vulnweb.com/products.php?cat=1",
     "desc": "SQL injection in cat parameter via error-based technique",
     "evidence": "MySQL Error: You have an error in your SQL syntax...mysql_fetch_array()...",
     "gt": "true_positive"},
    {"scanner": "dalfox", "type": "xss", "sev": "medium",
     "url": "http://testphp.vulnweb.com/search.php?test=query",
     "desc": "Reflected XSS - input reflected without encoding",
     "evidence": "<script>alert(1)</script> in response body, no encoding applied",
     "gt": "true_positive"},
    {"scanner": "nuclei", "type": "xss", "sev": "medium",
     "url": "http://testphp.vulnweb.com/search.php?q=hello",
     "desc": "Potential XSS - parameter reflected in response",
     "evidence": "Input value 'hello' found in response, but properly HTML-encoded",
     "gt": "false_positive"},
    {"scanner": "sqlmap", "type": "sql_injection", "sev": "high",
     "url": "http://testphp.vulnweb.com/artists.php?artist=1",
     "desc": "Possible SQL injection - error message detected",
     "evidence": "Generic error page, no SQL syntax in response, standard 500 handler",
     "gt": "false_positive"},
]

async def demo():
    print("=" * 65)
    print("  VulnForge - Full Pipeline Demonstration")
    print("  Scanner + LLM Hybrid Vulnerability Analysis")
    print("=" * 65)

    await init_db()
    with open("D:\\大论文\\backend\\.env") as f:
        api_key = f.read().split("OPENAI_API_KEY=")[1].split("\n")[0].strip()

    client = OpenAIClient("deepseek-chat", api_key, base_url="https://api.deepseek.com")
    analyzer = LLMAnalyzer(client)

    predictions = {"zero_shot": [], "few_shot": [], "chain_of_thought": []}
    latencies = {"zero_shot": [], "few_shot": [], "chain_of_thought": []}
    tokens = {"zero_shot": [], "few_shot": [], "chain_of_thought": []}

    for i, r in enumerate(SCAN_RESULTS):
        print(f"\n{'-' * 50}")
        print(f"Finding #{i+1}: [{r['scanner']}] {r['type']}  |  GT: {r['gt']}")

        sr = ScanResult(scanner_name=r["scanner"], vulnerability_type=r["type"],
            severity=r["sev"], url=r["url"], description=r["desc"], raw_evidence=r["evidence"])

        for sn, st in [("zero_shot", AnalysisStrategy.ZERO_SHOT),
                       ("few_shot", AnalysisStrategy.FEW_SHOT),
                       ("chain_of_thought", AnalysisStrategy.CHAIN_OF_THOUGHT)]:
            start = time.monotonic()
            resp = await analyzer.analyze_scan_result(sr, st)
            elapsed = time.monotonic() - start

            predictions[sn].append(resp.verdict)
            latencies[sn].append(elapsed)
            tokens[sn].append(resp.prompt_tokens + resp.completion_tokens)

            ok = "[OK]" if resp.verdict == r["gt"] else "[NO]"
            print(f"  [{sn:>16}] {ok} {resp.verdict:20s}  "
                  f"conf={resp.confidence:.2f}  {elapsed:.1f}s  "
                  f"tok={resp.prompt_tokens}+{resp.completion_tokens}")
            print(f"        Reasoning: {resp.reasoning[:100]}...")

    print(f"\n{'=' * 65}")
    print("  METRICS SUMMARY")
    print(f"{'=' * 65}")
    print(f"{'Strategy':<20} {'Prec':<8} {'Rec':<8} {'F1':<8} {'Acc':<8} {'Lat(s)':<8} {'Tokens'}")
    print("-" * 65)

    for strategy in ["zero_shot", "few_shot", "chain_of_thought"]:
        preds, gt = predictions[strategy], [r["gt"] for r in SCAN_RESULTS]
        tp = sum(1 for p,g in zip(preds,gt) if p=="true_positive" and g=="true_positive")
        fp = sum(1 for p,g in zip(preds,gt) if p=="true_positive" and g=="false_positive")
        fn = sum(1 for p,g in zip(preds,gt) if p=="false_positive" and g=="true_positive")
        tn = sum(1 for p,g in zip(preds,gt) if p=="false_positive" and g=="false_positive")
        uc = sum(1 for p in preds if p=="uncertain")
        pr = tp/(tp+fp) if (tp+fp)>0 else 0
        re = tp/(tp+fn) if (tp+fn)>0 else 0
        f1 = 2*pr*re/(pr+re) if (pr+re)>0 else 0
        ac = (tp+tn)/len(gt)
        al = sum(latencies[strategy])/len(latencies[strategy])
        at = sum(tokens[strategy])/len(tokens[strategy])
        print(f"{strategy:<20} {pr:<8.3f} {re:<8.3f} {f1:<8.3f} {ac:<8.3f} {al:<8.2f} {at:<8.0f}")
        print(f"{'':20} TP={tp} FP={fp} FN={fn} TN={tn} Unc={uc}")

    print(f"\n{'=' * 65}")
    print("  DEMO COMPLETE - Full LLM pipeline verified!")
    print(f"{'=' * 65}")

asyncio.run(demo())
