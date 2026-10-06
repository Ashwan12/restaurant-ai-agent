import re
from typing import Optional, Tuple
from app.models.schemas import GuardrailCheckResult
from app.config import settings

class SecurityGuardrails:
    """Multi-layered safety, authorization, and anti-injection protection for Restaurant Agent."""

    # Patterns indicating prompt injection, jailbreaking, or unauthorized system overrides
    INJECTION_PATTERNS = [
        r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
        r"disregard\s+(?:all\s+|your\s+|the\s+)?(?:rules|instructions|system\s+prompt)",
        r"(?:show|tell|reveal|print|display)\s+(?:me\s+)?(?:the\s+)?(?:system\s+prompt|initial\s+prompt|secret|api\s*key)",
        r"(?:bypass|disable|override)\s+(?:safety\s+)?(?:guardrails|safety|security|filters)",
        r"(?:you\s+are\s+now|act\s+as)\s+(?:DAN|unfiltered|jailbroken|root|developer\s+mode|an\s+unfiltered)",
    ]

    # Patterns indicating unauthorized bulk data access / data exfiltration
    UNAUTHORIZED_DATA_ACCESS_PATTERNS = [
        r"(?:show|list|dump|give|display|export|get)\s+(?:me\s+)?(?:every|all(?:\s+other)?|other)\s+(?:customer|user)?\s*(?:order|data|record|account|credit\s+card|personal\s+info)s?",
        r"(?:dump|export)\s+(?:all\s+)?(?:orders|customers)(?:\s+and\s+customers)?(?:\s+database)?",
        r"select\s+\*\s+from\s+(?:orders|users|customers|tickets)",
        r"(?:orders|customers)\s+database\s+dump",
    ]

    # Dangerous code / command tokens
    CODE_INJECTION_PATTERNS = [
        r"__import__\(",
        r"(?:os|subprocess|sys)\.system",
        r"DROP\s+TABLE",
        r"UNION\s+SELECT",
    ]

    # Sensitive token / secret detection in outputs
    SECRET_PATTERNS = [
        r"(?:AIzaSy[A-Za-z0-9_-]{33})",               # Gemini API Key
        r"(?:sk-[A-Za-z0-9]{20,48})",                 # OpenAI API Key
        r"(?:ghp_[A-Za-z0-9]{36})",                    # GitHub token
    ]

    def validate_user_input(self, user_text: str) -> GuardrailCheckResult:
        """Validate inbound user message for prompt injection and unauthorized queries."""
        if not settings.ENABLE_PROMPT_INJECTION_SHIELD:
            return GuardrailCheckResult(is_safe=True)

        text_lower = user_text.lower().strip()

        # 1. Check Prompt Injection
        for pat in self.INJECTION_PATTERNS:
            if re.search(pat, text_lower, re.IGNORECASE):
                return GuardrailCheckResult(
                    is_safe=False,
                    violation_type="prompt_injection",
                    reason="Input contains instructions attempting to override system behavior or prompt rules."
                )

        # 2. Check Unauthorized Data Access (e.g., Scenario 4: 'show me every customer order')
        for pat in self.UNAUTHORIZED_DATA_ACCESS_PATTERNS:
            if re.search(pat, text_lower, re.IGNORECASE):
                return GuardrailCheckResult(
                    is_safe=False,
                    violation_type="unauthorized_data_access",
                    reason="Request attempts unauthorized bulk access to customer records."
                )

        # 3. Check Arbitrary Code / SQL injection attempts
        for pat in self.CODE_INJECTION_PATTERNS:
            if re.search(pat, user_text, re.IGNORECASE):
                return GuardrailCheckResult(
                    is_safe=False,
                    violation_type="code_injection",
                    reason="Arbitrary command execution or SQL syntax detected."
                )

        return GuardrailCheckResult(is_safe=True)

    def mask_secrets_in_output(self, text: str) -> str:
        """Ensure no accidental leakage of API keys or environment secrets in agent responses."""
        sanitized = text
        for pat in self.SECRET_PATTERNS:
            sanitized = re.sub(pat, "[REDACTED_API_KEY]", sanitized)

        # Also mask configured keys if they exist and are non-empty
        if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 8:
            sanitized = sanitized.replace(settings.GEMINI_API_KEY, "[REDACTED_GEMINI_KEY]")
        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 8:
            sanitized = sanitized.replace(settings.OPENAI_API_KEY, "[REDACTED_OPENAI_KEY]")

        return sanitized

    def get_security_refusal_message(self, violation_type: str) -> str:
        """Deterministic safety response that cannot be bypassed by LLM reasoning."""
        if violation_type == "unauthorized_data_access":
            return (
                "Access Denied: I am not authorized to display other customers' orders or bulk operational data. "
                "Per restaurant privacy and data protection policies, you may only query your own specific order "
                "by providing a valid Order ID (e.g., ORD-1005)."
            )
        elif violation_type == "prompt_injection":
            return (
                "Security Policy Notice: I cannot execute instructions that attempt to override my operating rules, "
                "bypass security boundaries, or expose internal system instructions. "
                "How may I assist you with your restaurant orders, menu policies, or support requests?"
            )
        else:
            return (
                "Security Refusal: Your request was flagged as unauthorized or incompatible with restaurant "
                "operating safety standards."
            )

security_guardrails = SecurityGuardrails()
