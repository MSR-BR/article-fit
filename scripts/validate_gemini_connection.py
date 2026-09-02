"""Run one bounded Gemini contract check without private manuscript content."""

from __future__ import annotations

import os
from pathlib import Path

from journal_matcher_api.gemini import GeminiEditorialClient


def load_local_env(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> None:
    load_local_env(Path(__file__).resolve().parents[1] / ".env")
    prompt = """Return one editorial proposal as JSON using the supplied schema.
This is a connection test with no manuscript or private content.
Use anchor connection:test, category language, priority low, basis expert-suggestion,
no source IDs, scientificImpact false, authorValidationRequired false.
Explain that the test sentence 'This sentence are unclear.' should be grammatically revised.
Include a short summary and the limitation 'Connection test only.'"""
    result = GeminiEditorialClient(timeout=60).generate(prompt)
    print(f"Gemini validation succeeded: model={result.model}; proposals={len(result.response.proposals)}")


if __name__ == "__main__":
    main()
