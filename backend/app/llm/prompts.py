from app.llm.client import BaseLLMClient, LLMResponse
from app.models.finding import Finding
from typing import Optional


class PromptBuilder:
    """Builds prompts for LLM vulnerability analysis."""

    SYSTEM_PROMPT = """You are a security expert specializing in web application vulnerability verification.
Your task is to analyze HTTP request/response pairs produced by automated vulnerability scanners
and determine whether each finding is a TRUE POSITIVE or FALSE POSITIVE.

A true positive means the vulnerability genuinely exists and is exploitable.
A false positive means the scanner incorrectly flagged benign behavior.

**Confidence scale (use the FULL range, not just 0.9-1.0):**
0.0-0.2: Pure guess, no real evidence
0.2-0.4: Weak signal, mostly inconclusive
0.4-0.6: Moderate evidence, plausible but uncertain
0.6-0.8: Strong evidence, likely correct
0.8-0.95: Very strong evidence, nearly certain
0.95-1.0: Absolutely certain, undeniable evidence

Analyze carefully:
1. Is the evidence in the response consistent with the claimed vulnerability type?
2. Could the response pattern be caused by normal application behavior?
3. Is there sufficient evidence of actual exploitation potential?

Output your analysis as valid JSON with this exact schema:
{
  "verdict": "true_positive" | "false_positive" | "uncertain",
  "confidence": <float between 0 and 1>,
  "reasoning": "<detailed step-by-step explanation>",
  "severity_reassessment": "critical" | "high" | "medium" | "low" | "info" | null
}"""

    @staticmethod
    def build_zero_shot(finding: Finding) -> tuple[str, str]:
        """Build system and user prompts for zero-shot analysis."""
        user_prompt = f"""Please analyze this finding from a web vulnerability scan:

Scanner: {finding.scanner_name}
Vulnerability Type: {finding.vulnerability_type}
Severity: {finding.severity.value}
URL: {finding.url}
Description: {finding.description or "(no description)"}

Evidence:
{finding.raw_evidence or "(no evidence)"}

Request:
{finding.request_data or "(not captured)"}

Response:
{finding.response_data or "(not captured)"}

Is this a true positive or false positive? Respond in JSON format. Use the full confidence scale."""
        return PromptBuilder.SYSTEM_PROMPT, user_prompt

    @staticmethod
    def build_few_shot(finding: Finding) -> tuple[str, str]:
        """Build system and user prompts for few-shot analysis with examples."""
        examples = """Here are annotated examples covering different confidence levels:

Example 1 (TRUE POSITIVE - SQL Injection, very confident):
- Scanner: sqlmap | URL: http://testapp.com/products?id=1
- Evidence: Parameter id (GET) error-based SQLi. Response contains MySQL error with injected payload.
- Verdict: true_positive (confidence: 0.97) - Clear SQL syntax error confirming injection

Example 2 (FALSE POSITIVE - Technology info, moderately confident):
- Scanner: nuclei | URL: http://testapp.com/
- Evidence: Response header has `Server: Apache/2.4.41` and `X-Powered-By: PHP/7.4`
- Verdict: false_positive (confidence: 0.85) - Standard server headers, informational only, not a vuln

Example 3 (FALSE POSITIVE - phpinfo exposure, uncertain):
- Scanner: nuclei | URL: http://testapp.com/phpinfo.php
- Evidence: 200 OK response with `PHP Version 7.4.30`. No sensitive data visible in snippet.
- Verdict: false_positive (confidence: 0.55) - Possible minor info disclosure but insufficient evidence of harm

Example 4 (UNCERTAIN - Weak XSS evidence):
- Scanner: dalfox | URL: http://testapp.com/search?q=test
- Evidence: Input reflected in response but no unencoded script tags or event handlers observed.
- Verdict: uncertain (confidence: 0.35) - Reflection exists but no exploitation vector confirmed

Example 5 (TRUE POSITIVE - Missing security headers, moderately confident):
- Scanner: nuclei | URL: http://testapp.com/
- Evidence: Missing X-Frame-Options, X-Content-Type-Options, CSP headers
- Verdict: true_positive (confidence: 0.72) - Real missing headers but low direct exploitation risk
"""

        user_prompt = f"""Now analyze this finding:

Scanner: {finding.scanner_name}
Vulnerability Type: {finding.vulnerability_type}
Severity: {finding.severity.value}
URL: {finding.url}
Description: {finding.description or "(no description)"}

Evidence:
{finding.raw_evidence or "(no evidence)"}

Request:
{finding.request_data or "(not captured)"}

Response:
{finding.response_data or "(not captured)"}

Is this a true positive or false positive? Respond in JSON format. Use the full confidence scale."""
        return PromptBuilder.SYSTEM_PROMPT, user_prompt
    @staticmethod
    def build_chain_of_thought(finding: Finding) -> tuple[str, str]:
        """Build system and user prompts for Chain-of-Thought analysis."""
        user_prompt = f"""Analyze this vulnerability finding step by step.

Scanner: {finding.scanner_name}
Vulnerability Type: {finding.vulnerability_type}
Severity: {finding.severity.value}
URL: {finding.url}
Description: {finding.description or "(no description)"}

Evidence:
{finding.raw_evidence or "(no evidence)"}

Request:
{finding.request_data or "(not captured)"}

Response:
{finding.response_data or "(not captured)"}

Please reason step-by-step:

1. What is the scanner claiming? What vulnerability type and where?
2. What does the evidence actually show? Look at the raw request/response data.
3. Is the evidence consistent with the claimed vulnerability? Why or why not?
4. Could normal application behavior produce similar patterns?
5. Is there evidence of actual exploitation impact?

After your reasoning, provide your final verdict in JSON format. Use the full confidence scale."""
        return PromptBuilder.SYSTEM_PROMPT, user_prompt
