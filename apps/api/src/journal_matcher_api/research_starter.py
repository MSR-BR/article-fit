"""Server-side Research Starter v1 adapter with strict secret and contract boundaries."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fastapi import HTTPException

API_VERSION = "v1"
CONTRACT_VERSION = "2026-07-27.c84"
REPORTS_PATH = "/api/v1/reports"


@dataclass(frozen=True)
class ResearchStarterResult:
    report_id: str
    contract_version: str
    references: list[dict[str, Any]]
    top_papers: list[dict[str, Any]]
    coverage: dict[str, Any]
    warnings: list[str]
    ai_use_disclosure: dict[str, Any] | None
    source_rights_summary: dict[str, Any] | None


class ResearchStarterClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 45.0) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("Research Starter base URL must be public HTTPS")
        if len(api_key.strip()) < 16:
            raise ValueError("Research Starter API key is invalid")
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.timeout = timeout

    def report(self, topic: str, max_references: int = 30, max_top_papers: int = 20) -> ResearchStarterResult:
        normalized_topic = " ".join(topic.split())
        if not 1 <= len(normalized_topic) <= 180:
            raise HTTPException(status_code=422, detail="Research Starter topic must contain 1 to 180 characters")
        if not 1 <= max_references <= 80 or not 1 <= max_top_papers <= 50:
            raise HTTPException(status_code=422, detail="Research Starter result limits are outside the v1 contract")
        body = json.dumps(
            {
                "topic": normalized_topic,
                "publicationInterval": {"kind": "last-5-years"},
                "maxReferences": max_references,
                "maxTopPapers": max_top_papers,
                "includeMarkdown": False,
            }
        ).encode()
        request = Request(
            f"{self.base_url}{REPORTS_PATH}",
            method="POST",
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
            data=body,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310 - fixed validated HTTPS base
                payload = json.loads(response.read())
        except HTTPError as error:
            status_code = 401 if error.code == 401 else 502
            raise HTTPException(status_code=status_code, detail="Research Starter request failed") from error
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            raise HTTPException(status_code=502, detail="Research Starter could not return a valid response") from error
        if not isinstance(payload, dict) or payload.get("ok") is not True:
            raise HTTPException(status_code=502, detail="Research Starter returned a failed report")
        if payload.get("apiVersion") not in (None, API_VERSION):
            raise HTTPException(status_code=502, detail="Unsupported Research Starter API version")
        coverage_value = payload.get("coverage")
        coverage = (
            {str(key): value for key, value in coverage_value.items()} if isinstance(coverage_value, dict) else {}
        )
        return ResearchStarterResult(
            report_id=str(payload.get("reportId", "")),
            contract_version=str(payload.get("contractVersion", "unknown")),
            references=_dict_list(payload.get("references")),
            top_papers=_dict_list(payload.get("topPapers")),
            coverage=coverage,
            warnings=[str(item) for item in payload.get("warnings", []) if isinstance(item, str)],
            ai_use_disclosure=(
                payload.get("aiUseDisclosure") if isinstance(payload.get("aiUseDisclosure"), dict) else None
            ),
            source_rights_summary=(
                payload.get("sourceRightsSummary") if isinstance(payload.get("sourceRightsSummary"), dict) else None
            ),
        )


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
