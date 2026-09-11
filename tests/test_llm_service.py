import pytest

from app import llm_service
from app.llm_config import MissingAPIKeyError


class _FakeLLM:
    """Stands in for crewai.LLM so tests never make real network calls."""

    def __init__(self, *, model: str, api_key: str) -> None:
        self.model = model
        self.api_key = api_key

    def call(self, *args: object, **kwargs: object) -> str:
        return "pong"


class _FakeFailingLLM:
    """Simulates a provider error that echoes the API key back, e.g. via a URL."""

    def __init__(self, *, model: str, api_key: str) -> None:
        self._api_key = api_key

    def call(self, *args: object, **kwargs: object) -> str:
        raise RuntimeError(
            f"upstream call failed for https://example.invalid/?key={self._api_key}"
        )


def test_get_llm_raises_when_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError):
        llm_service.get_llm()


def test_get_llm_builds_llm_with_configured_model_and_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-test-key")
    monkeypatch.setattr(llm_service, "LLM", _FakeLLM)

    llm = llm_service.get_llm()

    assert llm.model == llm_service.DEFAULT_GEMINI_MODEL
    assert llm.api_key == "fake-test-key"


def test_check_connectivity_fails_gracefully_when_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    result = llm_service.check_connectivity()

    assert result.ok is False
    assert "GOOGLE_API_KEY" in result.message


def test_check_connectivity_succeeds_when_llm_responds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-test-key")
    monkeypatch.setattr(llm_service, "LLM", _FakeLLM)

    result = llm_service.check_connectivity()

    assert result.ok is True


def test_check_connectivity_never_leaks_api_key_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_key = "super-secret-fake-key"
    monkeypatch.setenv("GOOGLE_API_KEY", fake_key)
    monkeypatch.setattr(llm_service, "LLM", _FakeFailingLLM)

    result = llm_service.check_connectivity()

    assert result.ok is False
    assert fake_key not in result.message
