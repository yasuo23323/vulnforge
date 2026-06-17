# VulnForge Project State
> Last updated: 2026-06-17 19:30 UTC+1
> This file records the current progress so work can be resumed after session breaks.

## Project Overview
AI-Enhanced Automated Web Vulnerability Discovery: A Hybrid Framework Integrating LLMs with Traditional Scanners.
Master's thesis project. Built by Codex (GPT-5 based coding agent).

---


## TODAY'S WORK (2026-06-17 Final)

### Project Complete - Pushed to GitHub
- Repository: https://github.com/yasuo23323/vulnforge
- Verified running on Kali Linux via Docker
- Tool downloads fixed with retry + graceful fallback
- Removed pywin32 (Windows-only, broke Linux builds)
- Deployed with: bash final_version/start.sh (one-click setup)

### Production Deployment (final_version/)
- docker-compose.yml — services: postgres, redis, backend, frontend
- .env.example — API key configuration
- start.sh — auto-creates .env, prompts for API key, starts Docker
- start.bat — Windows equivalent
- Orchestrator uses Docker for nuclei scanning (no local install needed)

### What's Working
- Backend: 16 API routes, scanner engine, LLM analysis (3 strategies)
- Frontend: 6 pages (Dashboard, Scan Tasks, Scan Detail, Results, Settings)
- Scanners: nuclei (via Docker), ffuf, dalfox, sqlmap
- Real dataset: 88 findings across Juice Shop + DVWA
- LLM analysis: 255 DeepSeek API calls with ground truth metrics
## PENDING / NEXT STEPS

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








