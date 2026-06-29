from app.scanner.base import ScanResult


def parse_nuclei_output(raw: str) -> list[ScanResult]:
    results = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            results.append(ScanResult(
                vulnerability_type=parts[1] if len(parts) > 1 else parts[0],
                url=parts[0],
                severity="high",
                raw_evidence=line,
            ))
    return results


def parse_dalfox_output(raw: str) -> list[ScanResult]:
    results = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if "XSS" in line or "VULN" in line:
            results.append(ScanResult(
                vulnerability_type="xss",
                url=line,
                severity="high",
                raw_evidence=line,
            ))
    return results


def parse_ffuf_output(raw: str) -> list[ScanResult]:
    results = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        results.append(ScanResult(
            vulnerability_type="directory_enumeration",
            url=line,
            severity="info",
            raw_evidence=line,
            description=f"Discovered path: {line}",
        ))
    return results


def parse_sqlmap_output(raw: str) -> list[ScanResult]:
    results = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if "Parameter:" in line:
            results.append(ScanResult(
                vulnerability_type="sql_injection",
                url=line,
                severity="critical",
                raw_evidence=line,
                description=f"SQL injection confirmed: {line}",
            ))
    return results


SCANNER_PARSERS = {
    "nuclei": parse_nuclei_output,
    "dalfox": parse_dalfox_output,
    "ffuf": parse_ffuf_output,
    "sqlmap": parse_sqlmap_output,
}