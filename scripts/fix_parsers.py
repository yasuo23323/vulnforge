# This Python script writes the full parsers.py
content = r'''
import json
import re
from typing import Optional
from app.scanner.base import ScanResult

def parse_nuclei_output(raw_output: str) -> list:
    results = []
    for line in raw_output.strip().split("\n"):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            entry = json.loads(line)
            sev = entry.get("info", {}).get("severity", "info").lower()
            results.append(ScanResult(
                scanner_name="nuclei",
                vulnerability_type=entry.get("info", {}).get("name", "unknown"),
                severity=sev if sev in ("critical","high","medium","low","info") else "info",
                url=entry.get("matched-at", entry.get("host", "")),
                request_data=entry.get("request", ""),
                response_data=entry.get("response", ""),
                raw_evidence=entry.get("matched-at", ""),
                description=entry.get("info", {}).get("description", ""),
                extra_data={
                    "template_id": entry.get("template-id", ""),
                    "template_url": entry.get("template-url", ""),
                    "tags": entry.get("info", {}).get("tags", []),
                },
            ))
        except (json.JSONDecodeError, KeyError):
            continue
    return results

def parse_sqlmap_output(raw_output: str, target_url: str) -> list:
    results = []
    for line in raw_output.split("\n"):
        line = line.strip()
        if "Parameter:" in line and ("GET" in line or "POST" in line or "custom" in line):
            results.append(ScanResult(
                scanner_name="sqlmap", vulnerability_type="sql_injection",
                severity="high", url=target_url, raw_evidence=line,
                description=line[:100],
                extra_data={"sqlmap_line": line}))
        if "is vulnerable" in line.lower():
            results.append(ScanResult(
                scanner_name="sqlmap", vulnerability_type="sql_injection",
                severity="critical", url=target_url, raw_evidence=line,
                description="SQL injection confirmed: " + line[:80]))
    return results

def parse_dalfox_output(raw_output: str) -> list:
    results = []
    for line in raw_output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if "XSS" in line and ("Issue" in line or "found" in line.lower() or "VULN" in line):
            url = line
            for part in line.split():
                if part.startswith("http://") or part.startswith("https://"):
                    url = part; break
            results.append(ScanResult(
                scanner_name="dalfox", vulnerability_type="xss",
                severity="medium", url=url, raw_evidence=line,
                description=line[:100]))
    if not results and "XSS found" in raw_output and "0 XSS" not in raw_output:
        for line in reversed(raw_output.strip().split("\n")):
            if "XSS found" in line and "0 XSS" not in line:
                results.append(ScanResult(
                    scanner_name="dalfox", vulnerability_type="xss",
                    severity="medium", url="", raw_evidence=line,
                    description="XSS detected: " + line[:80]))
                break
    return results

def parse_ffuf_output(raw_output: str) -> list:
    results = []
    for line in raw_output.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("::") or line.startswith("["):
            continue
        results.append(ScanResult(
            scanner_name="ffuf", vulnerability_type="directory_enumeration",
            severity="info", url=line, raw_evidence=line,
            description="Discovered path: " + line,
            extra_data={"path": line}))
    return results

SCANNER_PARSERS = {
    "nuclei": parse_nuclei_output,
    "sqlmap": parse_sqlmap_output,
    "dalfox": parse_dalfox_output,
    "ffuf": parse_ffuf_output,
}
'''

import os
outpath = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'scanner', 'parsers.py')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(content.strip())
print("Written parsers.py successfully")
