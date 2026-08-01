"""Minimal worker process shell."""

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

from journal_matcher_api.foundation import FoundationStore

from journal_matcher_worker import __version__


def health_payload() -> dict[str, str]:
    """Return the worker health contract without external side effects."""
    return {"service": "worker", "status": "ok", "version": __version__}


def main(argv: Sequence[str] | None = None) -> int:
    """Run a one-shot health check or report the intentionally idle shell."""
    parser = argparse.ArgumentParser(description="Journal Matcher worker shell")
    parser.add_argument("--health-check", action="store_true")
    parser.add_argument("--purge-expired", action="store_true")
    args = parser.parse_args(argv)

    if args.health_check:
        print(json.dumps(health_payload(), sort_keys=True))
        return 0

    if args.purge_expired:
        data_root = Path(os.getenv("JOURNAL_MATCHER_DATA_ROOT", "/tmp/journal-matcher"))
        count = FoundationStore(data_root / "metadata.sqlite3", data_root / "objects").purge_expired()
        print(json.dumps({"purgedProjects": count}, sort_keys=True))
        return 0

    print("Journal Matcher ingestion worker is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
