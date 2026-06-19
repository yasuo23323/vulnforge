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

Is this a true positive or false positive? Respond in JSON format."""
        return PromptBuilder.SYSTEM_PROMPT, user_prompt

    @staticmethod
    def build_few_shot(finding: Finding) -> tuple[str, str]:
        """Build system and user prompts for few-shot analysis with examples."""
        examples = """Here are three annotated examples to guide your analysis:

Example 1 (TRUE POSITIVE - SQL Injection):
- Scanner: sqlmap
- URL: http://testapp.com/products?id=1
- Evidence: Parameter: id (GET). Technique: Error-based. Title: MySQL >= 5.0 error-based.
- Analysis Result: The response contains a MySQL error message with the injected payload reflected, confirming SQL injection.
- Verdict: true_positive (confidence: 0.95)

Example 2 (FALSE POSITIVE - Reflected XSS):
- Scanner: dalfox
- URL: http://testapp.com/search?q=test
- Evidence: Parameter q reflected in response but properly HTML-encoded as &lt;script&gt;
- Analysis Result: The input is reflected, but the application properly encodes it. No XSS vector is possible.
- Verdict: false_positive (confidence: 0.90)

Example 3 (TRUE POSITIVE - Reflected XSS):
- Scanner: nuclei
- URL: http://testapp.com/error?msg=<script>alert(1)</script>
- Evidence: Response contains unencoded <script>alert(1)</script> in the body
- Analysis Result: Input is reflected without sanitization, allowing arbitrary JS execution.
- Verdict: true_positive (confidence: 0.98)"""

        user_prompt = f"""{examples}

Now analyze this finding:

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

Is this a true positive or false positive? Respond in JSON format."""
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

After your reasoning, provide your final verdict in JSON format."""
        return PromptBuilder.SYSTEM_PROMPT, user_prompt
