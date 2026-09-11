"""Minimal LLM service: builds a Gemini-backed CrewAI LLM client and offers
a connectivity check. No CloudOps agents, tasks, crew, or flow live here.
"""

from dataclasses import dataclass

from crewai import LLM

from app.llm_config import DEFAULT_GEMINI_MODEL, MissingAPIKeyError, get_google_api_key


@dataclass(frozen=True)
class ConnectivityResult:
    ok: bool
    message: str


def _redact(text: str, secret: str) -> str:
    return text.replace(secret, "****") if secret else text


def get_llm(model: str = DEFAULT_GEMINI_MODEL) -> LLM:
    """Build a CrewAI LLM client configured for Gemini.

    Raises:
        MissingAPIKeyError: if GOOGLE_API_KEY is not set.
    """
    api_key = get_google_api_key()
    return LLM(model=model, api_key=api_key)


def check_connectivity(model: str = DEFAULT_GEMINI_MODEL) -> ConnectivityResult:
    """Perform a minimal round-trip call to verify the LLM is reachable.

    Never raises for expected failure modes (missing key, network/auth errors)
    and never includes the API key value in the returned message.
    """
    try:
        api_key = get_google_api_key()
    except MissingAPIKeyError as exc:
        return ConnectivityResult(ok=False, message=str(exc))

    llm = LLM(model=model, api_key=api_key)

    try:
        response = llm.call("Respond with the single word: pong")
    except Exception as exc:  # network/auth/provider errors
        return ConnectivityResult(ok=False, message=_redact(f"LLM call failed: {exc}", api_key))

    return ConnectivityResult(ok=bool(response), message="LLM responded successfully.")


if __name__ == "__main__":
    result = check_connectivity()
    status = "OK" if result.ok else "FAILED"
    print(f"LLM connectivity: {status} - {result.message}")
