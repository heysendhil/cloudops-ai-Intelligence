"""Secure loading of LLM configuration from environment variables.

No secret is ever hard-coded here or included in an exception message beyond
the name of the missing environment variable.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

GOOGLE_API_KEY_ENV_VAR = "GOOGLE_API_KEY"
DEFAULT_GEMINI_MODEL = "gemini/gemini-3.6-flash"

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE)


class MissingAPIKeyError(RuntimeError):
    """Raised when a required LLM API key is not set in the environment."""


def is_configured() -> bool:
    """Return whether GOOGLE_API_KEY is set to a non-empty value."""
    return bool(os.environ.get(GOOGLE_API_KEY_ENV_VAR, "").strip())


def get_google_api_key() -> str:
    """Return the Google API key from the environment.

    Raises:
        MissingAPIKeyError: if GOOGLE_API_KEY is unset or empty.
    """
    api_key = os.environ.get(GOOGLE_API_KEY_ENV_VAR, "").strip()
    if not api_key:
        raise MissingAPIKeyError(
            f"{GOOGLE_API_KEY_ENV_VAR} is not set. "
            "Copy backend/.env.example to backend/.env and set it there."
        )
    return api_key
