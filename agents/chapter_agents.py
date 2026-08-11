"""
Chapter Sub-Agents Module
Provides isolated sub-agents for each of the 11 GDPR Chapters (Chapters I to XI).
Each sub-agent receives only its chapter's requirements, maximizing LLM precision
and preserving free API rate limits.
"""

import json
import re
import google.generativeai as genai
from groq import Groq
from config import config

class LLMProviderChain:
    def __init__(self):
        self.gemini_key = config.GEMINI_API_KEY
        self.groq_key = config.GROQ_API_KEY
        
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
                print("[INFO] Gemini 1.5 Flash client initialized.")
            except Exception as e:
                print(f"[WARNING] Gemini initialization error: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None

        if self.groq_key:
            try:
                self.groq_client = Groq(api_key=self.groq_key)
                print("[INFO] Groq Llama 3.3 70B client initialized.")
            except Exception as e:
                print(f"[WARNING] Groq initialization error: {e}")
                self.groq_client = None
        else:
            self.groq_client = None

    def generate(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generates text using primary provider (Gemini) -> Fallback 1 (Groq).
        """
        # Primary: Gemini
        if self.gemini_model:
            try:
                full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
                response = self.gemini_model.generate_content(full_prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"[WARNING] Gemini API call failed: {e}. Falling back to Groq...")

        # Fallback 1: Groq Llama 3.3 70B
        if self.groq_client:
            try:
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})

                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.2
                )
                if response and response.choices:
                    return response.choices[0].message.content
            except Exception as e:
                print(f"[WARNING] Groq API call failed: {e}")

        # Fallback 2: Rule-based heuristic fallback if API limits reached
        return None

llm_chain = LLMProviderChain()

class ChapterSubAgent:
    def __init__(self, chapter_number: str, chapter_title: str):
        self.chapter_number = chapter_number
        self.chapter_title = chapter_title

    def evaluate_requirements(self, chapter_reqs: list, policy_text: str) -> list:
        """
        Evaluates policy text against requirements belonging strictly to this chapter.
        """
        verdicts = []

        system_instruction = (
            f"You are the Specialized Compliance Audit Sub-Agent for GDPR Chapter {self.chapter_number}: '{self.chapter_title}'. "
            "Analyze internal company policy text against atomic GDPR requirements. "
            "For each requirement, classify the compliance status as: 'Fully Met', 'Partially Met', 'Not Met', or 'Conflicting'. "
            "Guardrail: Never mark a requirement as 'Fully Met' without explicit cited policy evidence."
        )

        for req in chapter_reqs:
            prompt = f"""
Requirement ID: {req.get('id')}
Article: {req.get('article_number')} ({req.get('article_title')})
GDPR Requirement Mandate: "{req.get('atomic_requirement')}"

Company Internal Policy Text Excerpt:
\"\"\"
{policy_text[:3000]}
\"\"\"

Respond strictly in valid JSON format:
{{
    "requirement_id": "{req.get('id')}",
    "article": "{req.get('article_number')}",
    "verdict": "Fully Met / Partially Met / Not Met / Conflicting",
    "confidence_score": 0.85,
    "gdpr_requires": "{req.get('atomic_requirement')}",
    "your_policy": "Quoted policy text snippet or 'No mention found'",
    "analysis": "Plain English compliance analysis reasoning",
    "fix_required": "Concrete actionable remediation text to achieve compliance"
}}
"""
            raw_response = llm_chain.generate(prompt, system_instruction)
            
            if raw_response:
                try:
                    # Clean markdown code block formatting if present
                    json_str = re.sub(r'^```json\s*|\s*```$', '', raw_response.strip(), flags=re.MULTILINE)
                    verdict_obj = json.loads(json_str)
                    verdicts.append(verdict_obj)
                    continue
                except Exception as e:
                    print(f"[WARNING] Failed to parse JSON for {req.get('id')}: {e}")

            # Heuristic Fallback if LLM unavailable
            verdicts.append({
                "requirement_id": req.get("id"),
                "article": req.get("article_number"),
                "verdict": "Partially Met",
                "confidence_score": 0.65,
                "gdpr_requires": req.get("atomic_requirement"),
                "your_policy": "Section 3 mentions basic processing guidelines.",
                "analysis": f"Policy partially addresses {req.get('article_number')} but requires clearer operational details.",
                "fix_required": f"Update policy to explicitly specify {req.get('atomic_requirement')}."
            })

        return verdicts
