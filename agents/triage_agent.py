"""
Document Triage Agent — Policy-Only Gate
Uses Groq (fast inference) to classify whether an uploaded PDF
is a company policy document before running the expensive compliance pipeline.

Design: FAIL-OPEN — if Groq is unreachable, the document is allowed through.
"""

import json
from groq import Groq
from config import config
from logger import get_logger

logger = get_logger("agents.triage")

TRIAGE_SYSTEM_PROMPT = """You are a document classification expert. Your ONLY job is to determine whether the provided text is from a COMPANY POLICY document or not.

COMPANY POLICY documents include:
- Privacy Policies
- Security Policies
- Data Protection Policies
- Information Security Policies
- Acceptable Use Policies
- Incident Response Plans
- Access Control Policies
- Terms of Service / Terms of Use
- Cookie Policies
- Compliance Manuals
- Employee Handbooks (with policy sections)
- Risk Management Policies
- Business Continuity Policies

NON-POLICY documents include:
- Architecture / Design documents
- Technical specifications / Blueprints
- Resumes / CVs
- Marketing / Sales materials
- Code documentation / READMEs
- Academic papers / Research
- Financial reports / Invoices
- Meeting notes / Agendas
- Product manuals / User guides
- Project plans / Roadmaps
- Contracts / Agreements (unless they contain policy clauses)

Respond with ONLY a valid JSON object (no markdown, no code fences):
{
  "is_policy": true or false,
  "document_type": "short label of what the document actually is (e.g. 'Systems Architecture Document', 'Privacy Policy', 'Resume')",
  "confidence": "high" or "medium" or "low",
  "reason": "One sentence explaining your classification decision"
}"""

TRIAGE_USER_PROMPT_TEMPLATE = """Classify the following document text. Is this a company policy document?

--- DOCUMENT TEXT (first ~3000 characters) ---
{text_sample}
--- END ---

Respond with ONLY a valid JSON object."""


# Groq models to try for triage (preferred model first)
TRIAGE_GROQ_MODELS = [
    "openai/gpt-oss-120b",
]


def triage_document(policy_text: str) -> dict:
    """
    Classify whether the given text is from a company policy document.

    Args:
        policy_text: Full extracted text from the uploaded PDF.

    Returns:
        dict with keys:
            - is_policy (bool): True if the document is a policy, False otherwise.
            - document_type (str): What kind of document it is.
            - confidence (str): "high", "medium", or "low".
            - reason (str): One-sentence explanation.
    """
    # Default fail-open result
    fail_open_result = {
        "is_policy": True,
        "document_type": "Unknown",
        "confidence": "low",
        "reason": "Triage classification could not be performed; document allowed through (fail-open).",
    }

    if not policy_text or len(policy_text.strip()) < 50:
        logger.warning("Triage skipped: insufficient text (%d chars).", len(policy_text) if policy_text else 0)
        return fail_open_result

    # Take first ~3000 characters for classification (enough context, cheap on tokens)
    text_sample = policy_text[:3000].strip()
    user_prompt = TRIAGE_USER_PROMPT_TEMPLATE.format(text_sample=text_sample)

    # Try Groq clients
    groq_keys = config.GROQ_API_KEYS
    if not groq_keys:
        logger.warning("Triage skipped: no Groq API keys configured.")
        return fail_open_result

    for key_idx, api_key in enumerate(groq_keys):
        try:
            client = Groq(api_key=api_key)
        except Exception as e:
            logger.warning("Triage: Groq client #%d init failed: %s", key_idx + 1, e)
            continue

        for model_id in TRIAGE_GROQ_MODELS:
            try:
                logger.info(
                    "Triage: classifying document with Groq Key #%d, model=%s...",
                    key_idx + 1, model_id,
                )

                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                    max_tokens=256,
                )

                if not response or not response.choices:
                    continue

                raw = response.choices[0].message.content
                if not raw:
                    continue

                # Strip markdown code fences if present
                raw = raw.strip()
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[-1]  # remove first line
                    if raw.endswith("```"):
                        raw = raw[:-3]
                    raw = raw.strip()

                result = json.loads(raw)

                # Validate required fields
                if "is_policy" not in result:
                    logger.warning("Triage: response missing 'is_policy' field: %s", raw[:200])
                    continue

                # Ensure correct types
                result["is_policy"] = bool(result["is_policy"])
                result.setdefault("document_type", "Unknown")
                result.setdefault("confidence", "medium")
                result.setdefault("reason", "Classification completed.")

                logger.info(
                    "Triage result: is_policy=%s, type='%s', confidence=%s, reason='%s'",
                    result["is_policy"],
                    result["document_type"],
                    result["confidence"],
                    result["reason"],
                )
                return result

            except json.JSONDecodeError as e:
                logger.warning(
                    "Triage: JSON parse error from Groq Key #%d (%s): %s",
                    key_idx + 1, model_id, str(e)[:100],
                )
            except Exception as e:
                err = str(e)
                logger.warning(
                    "Triage: Groq Key #%d (%s) error: %s: %s",
                    key_idx + 1, model_id, type(e).__name__, err[:200],
                )
                # If rate limited on this key, break to next key
                if "429" in err or "rate_limit" in err.lower():
                    break

    # All providers failed — fail open
    logger.warning("Triage: all Groq providers failed. Failing open (allowing document through).")
    return fail_open_result
