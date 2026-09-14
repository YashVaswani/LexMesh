import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import centralized logger (must come after load_dotenv so LOG_LEVEL env var is available)
from logger import get_logger
logger = get_logger("config")


class Config:
    @staticmethod
    def _parse_keys(primary_var: str, prefix: str) -> list:
        keys = []
        # Check primary var (supports comma-separated: KEY1,KEY2)
        val = os.getenv(primary_var, "").strip()
        if val:
            for k in val.split(","):
                k = k.strip()
                if k and k not in keys:
                    keys.append(k)

        # Check numbered vars: GEMINI_API_KEY_2, GEMINI_API_KEY_3, etc.
        for i in range(2, 6):
            k_var = f"{prefix}_{i}"
            val_i = os.getenv(k_var, "").strip()
            if val_i and val_i not in keys:
                keys.append(val_i)

        return keys

    GEMINI_API_KEYS = _parse_keys.__func__("GEMINI_API_KEY", "GEMINI_API_KEY")
    GROQ_API_KEYS   = _parse_keys.__func__("GROQ_API_KEY",   "GROQ_API_KEY")

    # Backward compatibility properties
    GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""
    GROQ_API_KEY   = GROQ_API_KEYS[0]   if GROQ_API_KEYS   else ""

    SUPABASE_URL          = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY          = os.getenv("SUPABASE_KEY", "")
    EMBEDDING_MODEL_NAME  = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    @classmethod
    def validate(cls):
        missing = []
        if not cls.GEMINI_API_KEYS:
            missing.append("GEMINI_API_KEY")
        if not cls.GROQ_API_KEYS:
            missing.append("GROQ_API_KEY")
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")

        if missing:
            logger.warning(
                "Missing environment variables: %s", ", ".join(missing)
            )
        else:
            logger.info(
                "Config initialized with %d Gemini key(s) & %d Groq key(s).",
                len(cls.GEMINI_API_KEYS),
                len(cls.GROQ_API_KEYS),
            )
        return len(missing) == 0


config = Config()
