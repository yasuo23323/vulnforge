# MSc Dissertation Plan: VulnForge
## AI-Enhanced Web Vulnerability Scanning with LLM-Based False Positive Analysis

**University:** University of Birmingham, School of Computer Science
**Degree:** MSc Computer Science
**Word Count Target:** ~15,000 words
**References:** 18-22 scholarly sources

---

## Proposed Title

**VulnForge: An AI-Enhanced Web Vulnerability Scanner with Multi-Strategy LLM Analysis for Automated False Positive Reduction**

---

## Dissertation Structure and Word Distribution

| Chapter | Title | Words |
|--------|-------|-------|
| 1 | Abstract | 300 |
| 2 | Introduction | 1,500 |
| 3 | Literature Review | 3,500 |
| 4 | System Design & Methodology | 3,000 |
| 5 | Implementation | 3,000 |
| 6 | Evaluation | 2,500 |
| 7 | Discussion | 1,200 |
| 8 | Conclusion & Future Work | 1,000 |
|  | **Total** | **~16,000** |

---

## Chapter-by-Chapter Breakdown

### 1. Abstract (300 words)
Background of web application security scanning problem.
Statement of approach: integrating 4 scanners with LLM analysis.
Key result: 3 prompting strategies compared, false positive reduction demonstrated.
Conclusion: multi-strategy LLM analysis improves vulnerability assessment reliability.

### 2. Introduction (1,500 words)
Sections:
- 2.1 Background: The growing web application attack surface
- 2.2 Problem Statement: False positives in automated scanning wastes analyst time
- 2.3 Proposed Solution: VulnForge - scanner integration + LLM analysis
- 2.4 Research Questions (3 RQs)
- 2.5 Contributions
- 2.6 Dissertation Outline

### 3. Literature Review (3,500 words)
Sections:
- 3.1 Web Application Vulnerabilities (OWASP Top 10, CVSS)
- 3.2 Automated Vulnerability Scanning Tools (nuclei, sqlmap, dalfox, ffuf)
- 3.3 The False Positive Problem in Security Scanning
- 3.4 Large Language Models for Code and Security Analysis
- 3.5 Prompt Engineering Strategies (Zero-shot, Few-shot, Chain-of-Thought)
- 3.6 Related Work on LLM-Enhanced Security Tools
- 3.7 Gaps in Existing Research

### 4. System Design & Methodology (3,000 words)
Sections:
- 4.1 Design Objectives
- 4.2 System Architecture Overview
- 4.3 Scanner Integration Layer
- 4.4 URL Discovery and Crawling
- 4.5 LLM Analysis Pipeline Design
- 4.6 Multi-Strategy Prompting Methodology
- 4.7 Database Schema and Data Flow

### 5. Implementation (3,000 words)
Sections:
- 5.1 Technology Stack Rationale
- 5.2 Backend Implementation (FastAPI, SQLAlchemy, Celery)
- 5.3 Frontend Implementation (React, TypeScript, Ant Design)
- 5.4 Scanner Orchestration and Docker Integration
- 5.5 LLM Client and Auto-Analysis Workflow
- 5.6 Cross-Platform Deployment
- 5.7 Implementation Challenges and Resolutions

### 6. Evaluation (2,500 words)
Sections:
- 6.1 Experimental Setup and Test Environment
- 6.2 Test Targets (OWASP Juice Shop, DVWA)
- 6.3 Scanner Results Comparison
- 6.4 LLM Analysis Accuracy by Strategy
- 6.5 False Positive Identification Case Studies
- 6.6 Performance and Scalability Analysis
- 6.7 Threats to Validity

### 7. Discussion (1,200 words)
Sections:
- 7.1 Interpretation of Key Findings
- 7.2 Comparison with Existing Approaches
- 7.3 Limitations of Current Implementation
- 7.4 Practical Implications for Security Practitioners

### 8. Conclusion & Future Work (1,000 words)
Sections:
- 8.1 Summary of Research Contributions
- 8.2 Answers to Research Questions
- 8.3 Future Work
- 8.4 Closing Remarks

---

## Research Questions

**RQ1:** How effectively can LLMs identify false positives from automated vulnerability scanners?

**RQ2:** Which prompting strategy (Zero-shot, Few-shot, or Chain-of-Thought) yields highest accuracy?

**RQ3:** Can multi-strategy LLM analysis improve reliability over single-strategy approaches?

---

## Initial Reference List (20 sources)

1. OWASP. (2021). OWASP Top 10 - 2021.
2. OWASP. (2024). Web Security Testing Guide v4.2.
3. Brown, T. et al. (2020). Language Models are Few-Shot Learners. NeurIPS.
4. Wei, J. et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in LLMs. NeurIPS.
5. Kojima, T. et al. (2022). Large Language Models are Zero-Shot Reasoners. NeurIPS.
6. OpenAI. (2023). GPT-4 Technical Report. arXiv:2303.08774.
7. ProjectDiscovery. (2024). Nuclei: Fast Vulnerability Scanner. GitHub.
8. Damele, B. (2024). sqlmap: Automatic SQL Injection Tool.
9. Hahwul. (2024). Dalfox: Fast XSS Scanner. GitHub.
10. Antunes, N. & Vieira, M. (2015). Assessing Vulnerability Detection Tools. IEEE TDSC.
11. Chapela, V. et al. (2024). LLMs for Cybersecurity: A Systematic Review. arXiv.
12. OWASP. (2024). OWASP Juice Shop Documentation.
13. Vaswani, A. et al. (2017). Attention Is All You Need. NeurIPS.
14. Goodfellow, I. et al. (2014). Generative Adversarial Nets. NeurIPS.
15. Radford, A. et al. (2019). Language Models are Unsupervised Multitask Learners.
16. Shostack, A. (2014). Threat Modeling: Designing for Security. Wiley.
17. Howard, M. & Lipner, S. (2006). The Security Development Lifecycle. Microsoft Press.
18. OWASP. (2023). Automated Threats to Web Applications.
19. Holz, T. et al. (2023). Machine Learning for Security: A Survey.
20. Wang, L. et al. (2023). Pre-trained Language Models for Security Tasks. arXiv.

---

## Writing Schedule

| Phase | Content | Days |
|-------|---------|------|
| 1 | Plan + Abstract + Introduction | 1-2 |
| 2 | Literature Review | 2-3 |
| 3 | Design & Methodology | 2-3 |
| 4 | Implementation | 2-3 |
| 5 | Evaluation + Discussion | 2-3 |
| 6 | Conclusion + References + Polish | 1-2 |