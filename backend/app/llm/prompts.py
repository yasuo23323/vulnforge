from app.models.finding import Finding

SYSTEM_PROMPT = """You are a web security expert analyzing vulnerability scanner results.
Your task is to determine if each finding is a true positive or false positive.
Be critical: many scanner outputs are false positives."""


class PromptBuilder:

    @staticmethod
    def build_zero_shot(finding: Finding) -> tuple[str, str]:
        system = SYSTEM_PROMPT
        user = f"""Please analyze this finding from a web vulnerability scan:

Scanner: {finding.scanner_name}
Vulnerability Type: {finding.vulnerability_type}
Severity: {finding.severity}
URL: {finding.url}
Description: {finding.description or "(no description)"}

Request:
{finding.request_data or "(not captured)"}

Response:
{finding.response_data or "(not captured)"}

Evidence:
{finding.raw_evidence or "(no evidence)"}

Is this a true positive or false positive? Respond in JSON format."""
        return system, user

    @staticmethod
    def build_few_shot(finding: Finding) -> tuple[str, str]:
        system = SYSTEM_PROMPT
        examples = """Here are three annotated examples to guide your analysis:

Example 1 (TRUE POSITIVE - SQL Injection):
- Scanner: sqlmap
- URL: http://testapp.com/products?id=1
- Evidence: Parameter: id (GET). Technique: Error-based.
- Analysis: Response contains MySQL error message with injected payload.
- Verdict: true_positive (confidence: 0.95)

Example 2 (FALSE POSITIVE - Reflected XSS):
- Scanner: dalfox
- URL: http://testapp.com/search?q=test
- Evidence: Parameter q reflected but properly HTML-encoded.
- Analysis: Input reflected but properly encoded. No XSS vector.
- Verdict: false_positive (confidence: 0.90)

Example 3 (TRUE POSITIVE - Reflected XSS):
- Scanner: nuclei
- URL: http://testapp.com/error?msg=<script>alert(1)</script>
- Evidence: Response contains unencoded <script>alert(1)</script>
- Analysis: Input reflected without sanitization.
- Verdict: true_positive (confidence: 0.98)

Now analyze this finding:"""
        user = f"""{examples}

Scanner: {finding.scanner_name}
Vulnerability Type: {finding.vulnerability_type}
Severity: {finding.severity}
URL: {finding.url}
Description: {finding.description or "(no description)"}

Request:
{finding.request_data or "(not captured)"}

Response:
{finding.response_data or "(not captured)"}

Evidence:
{finding.raw_evidence or "(no evidence)"}

Is this a true positive or false positive? Respond in JSON format."""
        return system, user

    @staticmethod
    def build_chain_of_thought(finding: Finding) -> tuple[str, str]:
        system = SYSTEM_PROMPT
        user = f"""Please reason step-by-step:

1. What is the scanner claiming?
2. What does the evidence actually show?
3. Is the evidence consistent with the claimed vulnerability?
4. Could normal behavior produce similar patterns?
5. Is there evidence of actual exploitation impact?

Scanner: {finding.scanner_name}
Vulnerability Type: {finding.vulnerability_type}
Severity: {finding.severity}
URL: {finding.url}
Description: {finding.description or "(no description)"}

Request:
{finding.request_data or "(not captured)"}

Response:
{finding.response_data or "(not captured)"}

Evidence:
{finding.raw_evidence or "(no evidence)"}

After your reasoning, provide your final verdict in JSON format."""
        return system, user