import json
from app.scanner.base import ScanResult

def parse_nuclei_output(raw):
    r = []
    for l in raw.split(chr(10)):
        if not l.startswith("{"): continue
        try:
            e = json.loads(l)
            r.append(ScanResult(scanner_name="nuclei",
                vulnerability_type=e.get("info",{}).get("name",""),
                severity=e.get("info",{}).get("severity","info"),
                url=e.get("matched-at","")))
        except: continue
    return r

def parse_sqlmap_output(raw, url):
    r = []
    for l in raw.split(chr(10)):
        if "Parameter:" in l:
            r.append(ScanResult(scanner_name="sqlmap", vulnerability_type="sql_injection", severity="high", url=url))
    return r

# BUG: checks "VULNERABLE" but dalfox v3 outputs "XSS payload reflected"
def parse_dalfox_output(raw):
    r = []
    for l in raw.split(chr(10)):
        if "VULNERABLE" not in l: continue
        r.append(ScanResult(scanner_name="dalfox", vulnerability_type="xss", severity="medium", url=""))
    return r

# BUG: expects 3+ columns but silent mode is 1 path/line
def parse_ffuf_output(raw):
    r = []
    for l in raw.split(chr(10)):
        p = l.split()
        if len(p) < 3: continue
        try:
            if int(p[1]) in (200,301,302,403,500):
                r.append(ScanResult(scanner_name="ffuf", vulnerability_type="directory_enumeration", severity="info", url=p[-1]))
        except: continue
    return r

SCANNER_PARSERS = {
    "nuclei": parse_nuclei_output,
    "sqlmap": parse_sqlmap_output,
    "dalfox": parse_dalfox_output,
    "ffuf": parse_ffuf_output,
}