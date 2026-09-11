import pytest

from app import llm_config


def test_get_google_api_key_reads_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-test-key")

    assert llm_config.get_google_api_key() == "fake-test-key"


def test_is_configured_true_when_key_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-test-key")

    assert llm_config.is_configured() is True


def test_is_configured_false_when_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    assert llm_config.is_configured() is False


def test_is_configured_false_when_key_blank(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "   ")

    assert llm_config.is_configured() is False


def test_missing_api_key_raises_missing_api_key_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(llm_config.MissingAPIKeyError) as exc_info:
        llm_config.get_google_api_key()

    assert "GOOGLE_API_KEY" in str(exc_info.value)
