"""Makes tests/ importable as a plain directory (e.g. `import
_fixtures_root_cause`) from any test module under tests/, including nested
ones like tests/evaluation/. pytest only auto-adds a test file's own
directory to sys.path, not its ancestors, so tests/evaluation/*.py cannot
otherwise reach shared helpers living directly in tests/. This file is
located via pytest's own rootdir-relative discovery, so it works regardless
of the invocation directory (repo root or backend/).

Also separates quota-blocked live-LLM evaluations (tests/evaluation/,
marked `live_llm`) from the normal test run: a plain `pytest` invocation
skips them automatically -- so "run the tests" never silently burns real
API quota or produces the cascading-429 failures seen when the whole
suite fires ~20+ live calls back to back -- and `pytest --run-live`
opts back in. Tests already skip individually via `is_configured()` when
no GOOGLE_API_KEY is set (see each tests/evaluation/*.py module); this is
an independent, coarser gate for quota, not a replacement for that check.
"""

import sys
from pathlib import Path

import pytest

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Also run tests marked 'live_llm' (tests/evaluation/) -- these make real "
        "LLM API calls and consume real, often quota-limited, API usage. Skipped by "
        "default so a normal test run never burns quota unexpectedly.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live_llm: makes a real call to a live LLM API and consumes real quota; "
        "skipped by default, use --run-live to include it",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-live"):
        return
    skip_live = pytest.mark.skip(
        reason="live-LLM test skipped by default (consumes real, quota-limited API "
        "usage) -- pass --run-live to include it"
    )
    for item in items:
        if "live_llm" in item.keywords:
            item.add_marker(skip_live)
