# VulnForge Project State
> Last updated: 2026-06-17 19:30 UTC+1
> This file records the current progress so work can be resumed after session breaks.

## Project Overview
AI-Enhanced Automated Web Vulnerability Discovery: A Hybrid Framework Integrating LLMs with Traditional Scanners.
Master's thesis project. Built by Codex (GPT-5 based coding agent).

---


## TODAY'S WORK (2026-06-17)

### Bug #1 Fixed: DVWA Authentication (P0)
- **Root cause**: CSRF token extraction created a new PHP session, but login used the old session cookie -> token/session mismatch -> login silently rejected
- **Fix**: Extract token and submit login in the SAME HTTP session (same PHPSESSID)
- **Verification**: curl.exe with -c and -b on same cookie file confirmed login works
- **DVWA scan results**: 6 vulnerability types accessible (SQLi, SQLi Blind, XSS Reflected, Command Injection, File Inclusion, Brute Force), 4 confirmed injectable with payloads

### Bug #2 Fixed: Nuclei localhost resolution (P0)
- **Root cause**: Nuclei v3.9.0 health check on Windows/Docker marks localhost:port as "unresponsive" and skips target
- **Fix**: Run nuclei INSIDE the Docker network via docker run projectdiscovery/nuclei --network vulnforge_default
- **Verification**: Juice Shop: Prometheus Metrics (medium). DVWA: Default Login (critical) + Config Listing (medium). No skip issues.
- **Reliable methodology**: docker run --rm --network vulnforge_default projectdiscovery/nuclei -u http://CONTAINER_NAME:PORT -j -severity critical,high,medium




### End-to-End Pipeline (NEW - Verified 2026-06-17)
- [x] Create scan via API (POST /api/scans) — triggers background execution
- [x] Background scanner execution (via asyncio.create_task, 180s timeout)
- [x] Scanner subprocess (ffuf, nuclei, dalfox, sqlmap) with proper parsers
- [x] Status updates: pending -> running -> completed/failed
- [x] Findings stored in DB, retrievable via API
- [x] All scanner commands fixed:
  - nuclei: -j (not -json), -severity critical,high,medium for speed
  - dalfox: --url flag, --headers (not --header)
  - ffuf: silent mode with common.txt wordlist
  - sqlmap: uses sqlmap.exe (not python -m sqlmap)
- [x] Parser fixes:
  - All parsers accept 	arget_url as optional 2nd arg (matching orchestrator call convention)
  - dalfox parser detects "XSS" instead of "VULNERABLE"
  - ffuf parser handles silent mode output (plain paths)
  - sqlmap parser detects "Parameter:" and "is vulnerable"## PENDING / NEXT STEPS

### Immediate Fixes Needed
- [x] ~~DVWA authentication~~ FIXED 2026-06-17: CSRF token extracted in wrong session; must use same PHPSESSID for token extraction and login
- [ ] Nuclei localhost resolution (in progress): v3.9.0 skips localhost targets as "unresponsive" when scanning all 10364 templates. Workaround: use `-severity` flag to limit templates; still inconsistent
- [ ] SQLMap JSON body: does not natively support JSON POST bodies. Juice Shop login API requires JSON; workaround: use manual curl/requests library

### Phase 3 Continued: Experiments
- [ ] Run additional rounds with different LLM providers (GPT-4o, Claude) for comparison
- [ ] Add Cohen"s Kappa inter-rater reliability analysis  
- [ ] Full experiment: all targets x all scanners x all strategies (requires DVWA auth fix)
- [ ] Run scanner tools WITHIN Docker network (nuclei from inside Docker can resolve container names)
- [ ] Statistical analysis report — export proper LaTeX-friendly tables

### Phase 4: Thesis Writing
- [ ] System architecture diagrams (backend/frontend/scanner/LLM flow)
- [ ] Experiment methodology write-up (dataset construction, strategy design, metrics)
- [ ] Results discussion with comparison tables and charts
- [ ] Related work comparison (existing vulnerability scanners + LLM approaches)

### Phase 5: Release
- [ ] GitHub open-source repo
- [ ] Docker one-command deployment
- [ ] Reproducible data package (all experiment exports + scripts)

### Known Issues
1. Nuclei v3.9.0 + localhost: template scan sometimes skips target; use `-severity` to limit templates
2. DVWA Docker container: PHP session login doesn"t persist across requests via Python requests library
3. Dalfox: Juice Shop requires authenticated POST-based XSS; default GET scan finds nothing
4. SQLMap: doesn"t support JSON POST body natively; use `--data-raw` for limited support
5. Windows GBK encoding: set `PYTHONIOENCODING=utf-8` for emoji/Unicode output







