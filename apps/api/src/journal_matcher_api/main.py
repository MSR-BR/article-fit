"""Article Fit API foundation."""

from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from journal_matcher_api import __version__
from journal_matcher_api.foundation import FoundationStore, Principal, validate_and_extract
from journal_matcher_api.gemini import (
    GeminiConfigurationError,
    GeminiEditorialClient,
    GeminiProviderError,
    build_editorial_prompt,
    proposals_as_recommendations,
)
from journal_matcher_api.hosted import (
    HostedAnalysisRepository,
    HostedFoundationStore,
    HostedJournalProfileRepository,
    SupabaseHttpClient,
    SupabaseSettings,
)
from journal_matcher_api.journal_research import (
    ArticleCandidate,
    JournalProfileRepository,
    PoliteHttpClient,
    derive_profile,
    html_to_text,
    make_evidence,
    select_articles,
    validate_public_https_url,
)
from journal_matcher_api.journal_resolution import (
    JournalResolutionError,
    discover_official_guidance,
    resolve_openalex_sources,
)
from journal_matcher_api.manuscript_analysis import (
    AnalysisRepository,
    annotate_docx,
    build_recommendations,
    create_docx,
    create_pdf,
    extract_official_rules,
    scientific_invariants,
    store_artifact_set,
    validate_artifacts,
    validate_invariant_preservation,
    validate_proposal_parity,
)
from journal_matcher_api.research_starter import ResearchStarterClient


class HealthResponse(BaseModel):
    service: str
    status: str
    version: str


class ProjectCreate(BaseModel):
    journal_candidate: str = Field(alias="journalCandidate", min_length=2, max_length=300)


class JournalConfirmation(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    issn: str = Field(pattern=r"^\d{4}-\d{3}[\dXx]$")
    official_domain: str = Field(alias="officialDomain", pattern=r"^[a-z0-9.-]+$")


class JournalResolveRequest(BaseModel):
    candidate: str = Field(min_length=2, max_length=300)


class StartJob(BaseModel):
    idempotency_key: str = Field(alias="idempotencyKey", min_length=8, max_length=128)


class ResearchRequest(BaseModel):
    scope_url: str = Field(alias="scopeUrl", pattern=r"^https://")
    guide_url: str = Field(alias="guideUrl", pattern=r"^https://")
    expected_profile_version: int = Field(alias="expectedProfileVersion", ge=0, default=0)
    scope_snapshot: str | None = Field(alias="scopeSnapshot", default=None, min_length=500, max_length=200_000)
    guide_snapshot: str | None = Field(alias="guideSnapshot", default=None, min_length=500, max_length=200_000)
    assisted_capture_confirmed: bool = Field(alias="assistedCaptureConfirmed", default=False)


class AnalysisRequest(BaseModel):
    profile_version_id: str = Field(alias="profileVersionId", min_length=16, max_length=64)


class ResearchStarterRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=180)
    max_references: int = Field(alias="maxReferences", ge=1, le=80, default=30)
    max_top_papers: int = Field(alias="maxTopPapers", ge=1, le=50, default=20)


class DecisionRequest(BaseModel):
    decision: Literal["accepted", "rejected", "modified"]
    modified_text: str | None = Field(alias="modifiedText", default=None, max_length=20_000)


class WorkflowRequest(BaseModel):
    idempotency_key: str = Field(alias="idempotencyKey", min_length=8, max_length=128)
    scope_url: str | None = Field(alias="scopeUrl", default=None, pattern=r"^https://")
    guide_url: str | None = Field(alias="guideUrl", default=None, pattern=r"^https://")
    scope_snapshot: str | None = Field(alias="scopeSnapshot", default=None, min_length=500, max_length=200_000)
    guide_snapshot: str | None = Field(alias="guideSnapshot", default=None, min_length=500, max_length=200_000)

    def has_assisted_guidance(self) -> bool:
        values = (self.scope_url, self.guide_url, self.scope_snapshot, self.guide_snapshot)
        if any(values) and not all(values):
            raise HTTPException(status_code=422, detail="The complete assisted-guidance package is required")
        return all(values)


Store = FoundationStore | HostedFoundationStore
ProfileRepository = JournalProfileRepository | HostedJournalProfileRepository
AnalysisStore = AnalysisRepository | HostedAnalysisRepository


@lru_cache
def get_store() -> Store:
    if os.getenv("JOURNAL_MATCHER_PERSISTENCE", "local") == "supabase":
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("Hosted persistence requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        return HostedFoundationStore(SupabaseHttpClient(SupabaseSettings(url, key)))
    data_root = Path(os.getenv("JOURNAL_MATCHER_DATA_ROOT", "/tmp/journal-matcher"))
    return FoundationStore(data_root / "metadata.sqlite3", data_root / "objects")


def profile_repository(store: Store) -> ProfileRepository:
    if isinstance(store, HostedFoundationStore):
        return HostedJournalProfileRepository(store.client)
    return JournalProfileRepository(str(store.database_path))


def analysis_repository(store: Store) -> AnalysisStore:
    if isinstance(store, HostedFoundationStore):
        return HostedAnalysisRepository(store.client)
    return AnalysisRepository(store.database_path)


def authenticate(
    authorization: Annotated[str | None, Header()] = None,
    workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> Principal:
    expected = os.getenv("JOURNAL_MATCHER_INVITE_TOKEN", "local-invite-token")
    if authorization != f"Bearer {expected}" or not workspace_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid invitation")
    try:
        normalized_workspace = str(__import__("uuid").UUID(workspace_id))
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid workspace identifier") from error
    return Principal(user_id="invited-pilot-user", workspace_id=normalized_workspace)


PrincipalDependency = Annotated[Principal, Depends(authenticate)]
StoreDependency = Annotated[Store, Depends(get_store)]

app = FastAPI(
    title="Article Fit API",
    version=__version__,
    description="Invitation-only project and secure ingestion foundation.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("JOURNAL_MATCHER_WEB_ORIGIN", "http://localhost:3000")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Workspace-Id", "X-Document-Media-Type"],
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(service="api", status="ok", version=__version__)


@app.post("/v1/journals/resolve", tags=["journals"])
async def resolve_journal(payload: JournalResolveRequest, principal: PrincipalDependency) -> dict[str, object]:
    contact = os.getenv("JOURNAL_MATCHER_PROVIDER_EMAIL")
    if not contact:
        raise HTTPException(status_code=503, detail="Provider contact email is not configured")
    client = PoliteHttpClient(contact)
    query = urlencode({"search": payload.candidate, "filter": "type:journal", "per-page": "10", "mailto": contact})
    try:
        metadata = json.loads(client.get(f"https://api.openalex.org/sources?{query}"))
        if not isinstance(metadata, dict):
            raise JournalResolutionError("Journal metadata provider returned an invalid response")
        journal = resolve_openalex_sources(payload.candidate, metadata)
        homepage = client.get(journal.homepage_url, allowed_domain=journal.official_domain).decode(
            "utf-8", errors="replace"
        )
        guidance = discover_official_guidance(journal.homepage_url, journal.official_domain, homepage)
    except (json.JSONDecodeError, JournalResolutionError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    return {
        "title": journal.title,
        "issn": journal.issn,
        "officialDomain": journal.official_domain,
        "homepageUrl": journal.homepage_url,
        "scopeUrl": guidance.scope_url,
        "guideUrl": guidance.guide_url,
        "evidence": {"provider": "OpenAlex", "sourceId": journal.source_id, "confidence": journal.confidence},
    }


@app.post("/v1/projects", status_code=201, tags=["projects"])
async def create_project(
    payload: ProjectCreate, principal: PrincipalDependency, store: StoreDependency
) -> dict[str, object]:
    return store.create_project(principal, payload.journal_candidate)


@app.get("/v1/projects/{project_id}", tags=["projects"])
async def get_project(project_id: str, principal: PrincipalDependency, store: StoreDependency) -> dict[str, object]:
    return store.get_project(principal, project_id)


@app.put("/v1/projects/{project_id}/journal", tags=["journals"])
async def confirm_journal(
    project_id: str,
    payload: JournalConfirmation,
    principal: PrincipalDependency,
    store: StoreDependency,
) -> dict[str, object]:
    return store.confirm_journal(principal, project_id, payload.title, payload.issn.upper(), payload.official_domain)


@app.put("/v1/projects/{project_id}/documents/{slot}", tags=["documents"])
async def upload_document(
    project_id: str,
    slot: Literal["manuscript", "reference-1", "reference-2", "reference-3"],
    principal: PrincipalDependency,
    store: StoreDependency,
    content: Annotated[bytes, Body(media_type="application/octet-stream")],
    filename: Annotated[str, Query(min_length=1, max_length=255)],
    content_type: Annotated[str, Header(alias="X-Document-Media-Type")],
) -> dict[str, object]:
    return store.store_document(principal, project_id, slot, filename, content_type, content)


@app.post("/v1/projects/{project_id}/jobs", status_code=202, tags=["jobs"])
async def start_ingestion_job(
    project_id: str,
    payload: StartJob,
    principal: PrincipalDependency,
    store: StoreDependency,
) -> dict[str, object]:
    return store.start_job(principal, project_id, payload.idempotency_key)


@app.post("/v1/projects/{project_id}/run", tags=["workflow"], response_model=None)
async def run_project_workflow(
    project_id: str,
    payload: WorkflowRequest,
    principal: PrincipalDependency,
    store: StoreDependency,
) -> dict[str, object] | JSONResponse:
    """Run the bounded MVP workflow from verified journal identity through artifacts."""
    project = store.get_project(principal, project_id)
    if {str(item.get("slot")) for item in cast(list[dict[str, object]], project["documents"])} != {
        "manuscript",
        "reference-1",
        "reference-2",
        "reference-3",
    }:
        raise HTTPException(status_code=409, detail="The complete upload package is required")
    if isinstance(store, HostedFoundationStore):
        job = store.start_job(
            principal,
            project_id,
            payload.idempotency_key,
            {"workflow": payload.model_dump(by_alias=True, exclude_none=True)},
        )
        _trigger_cloud_run_worker()
        return JSONResponse(status_code=202, content=job)
    return await execute_project_workflow(project_id, payload, principal, store)


async def execute_project_workflow(
    project_id: str,
    payload: WorkflowRequest,
    principal: Principal,
    store: Store,
) -> dict[str, object]:
    project = store.get_project(principal, project_id)
    if {str(item.get("slot")) for item in cast(list[dict[str, object]], project["documents"])} != {
        "manuscript",
        "reference-1",
        "reference-2",
        "reference-3",
    }:
        raise HTTPException(status_code=409, detail="The complete upload package is required")
    assisted = payload.has_assisted_guidance()
    resolved: dict[str, object]
    if assisted:
        contact = os.getenv("JOURNAL_MATCHER_PROVIDER_EMAIL")
        if not contact:
            raise HTTPException(status_code=503, detail="Provider contact email is not configured")
        client = PoliteHttpClient(contact)
        query = urlencode(
            {
                "search": str(project["journalCandidate"]),
                "filter": "type:journal",
                "per-page": "10",
                "mailto": contact,
            }
        )
        try:
            metadata = json.loads(client.get(f"https://api.openalex.org/sources?{query}"))
            if not isinstance(metadata, dict):
                raise JournalResolutionError("Journal metadata provider returned an invalid response")
            identity = resolve_openalex_sources(str(project["journalCandidate"]), metadata)
            validate_public_https_url(str(payload.scope_url), identity.official_domain)
            validate_public_https_url(str(payload.guide_url), identity.official_domain)
        except (json.JSONDecodeError, JournalResolutionError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from None
        resolved = {
            "title": identity.title,
            "issn": identity.issn,
            "officialDomain": identity.official_domain,
            "homepageUrl": identity.homepage_url,
            "scopeUrl": payload.scope_url,
            "guideUrl": payload.guide_url,
            "evidence": {"provider": "OpenAlex", "sourceId": identity.source_id, "confidence": identity.confidence},
        }
    else:
        resolved = await resolve_journal(JournalResolveRequest(candidate=str(project["journalCandidate"])), principal)
    store.confirm_journal(
        principal,
        project_id,
        str(resolved["title"]),
        str(resolved["issn"]),
        str(resolved["officialDomain"]),
    )
    ingestion = store.start_job(principal, project_id, payload.idempotency_key)
    research = await research_journal(
        project_id,
        ResearchRequest(
            scopeUrl=str(resolved["scopeUrl"]),
            guideUrl=str(resolved["guideUrl"]),
            expectedProfileVersion=0,
            scopeSnapshot=payload.scope_snapshot,
            guideSnapshot=payload.guide_snapshot,
            assistedCaptureConfirmed=assisted,
        ),
        principal,
        store,
    )
    profile = research.get("profileVersion")
    if not isinstance(profile, dict) or not profile.get("id"):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Journal research was incomplete; analysis cannot safely continue",
                "limitations": research.get("limitations", []),
                "warnings": research.get("warnings", []),
            },
        )
    analysis = await create_analysis(project_id, AnalysisRequest(profileVersionId=str(profile["id"])), principal, store)
    enriched = await create_ai_review(str(analysis["id"]), principal, store)
    artifact_result = await generate_artifacts(str(analysis["id"]), principal, store)
    return {
        "state": "succeeded",
        "stage": "artifacts-ready",
        "journal": resolved,
        "ingestion": ingestion,
        "research": research,
        "analysisId": analysis["id"],
        "recommendationCount": len(cast(list[object], enriched["recommendations"])),
        "artifacts": artifact_result["artifacts"],
    }


def _trigger_cloud_run_worker() -> None:
    run_url = os.getenv("CLOUD_RUN_WORKER_RUN_URL")
    if not run_url:
        return
    expected_prefix = "https://run.googleapis.com/v2/projects/"
    if not run_url.startswith(expected_prefix) or not run_url.endswith(":run"):
        raise HTTPException(status_code=503, detail="Worker trigger is misconfigured")
    token_request = Request(
        "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
        headers={"Metadata-Flavor": "Google"},
    )
    try:
        with urlopen(token_request, timeout=5) as response:  # noqa: S310 - fixed metadata service URL
            token_payload = json.loads(response.read())
        access_token = token_payload.get("access_token") if isinstance(token_payload, dict) else None
        if not isinstance(access_token, str) or not access_token:
            raise ValueError("missing access token")
        run_request = Request(
            run_url,
            data=b"{}",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(run_request, timeout=10):  # noqa: S310 - validated Google Cloud Run API URL
            return
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=503, detail="Worker could not be started") from error


@app.get("/v1/jobs/{job_id}", tags=["jobs"])
async def get_job(job_id: str, principal: PrincipalDependency, store: StoreDependency) -> dict[str, object]:
    return store.get_job(principal, job_id)


@app.post("/v1/jobs/{job_id}/cancel", tags=["jobs"])
async def cancel_job(job_id: str, principal: PrincipalDependency, store: StoreDependency) -> dict[str, object]:
    return store.cancel_job(principal, job_id)


@app.post("/v1/projects/{project_id}/research", tags=["research"])
async def research_journal(
    project_id: str,
    payload: ResearchRequest,
    principal: PrincipalDependency,
    store: StoreDependency,
) -> dict[str, object]:
    """Acquire bounded evidence and publish only a complete validated profile."""
    project = store.get_project(principal, project_id)
    journal = project.get("journal")
    if not project["readyForResearch"] or not isinstance(journal, dict):
        raise HTTPException(status_code=409, detail="The complete ingestion package is required before research")
    contact = os.getenv("JOURNAL_MATCHER_PROVIDER_EMAIL")
    if not contact:
        raise HTTPException(status_code=503, detail="Provider contact email is not configured")
    client = PoliteHttpClient(contact)
    official_domain = str(journal["officialDomain"])
    scope_text, scope_access = _acquire_official_text(
        client,
        payload.scope_url,
        official_domain,
        payload.scope_snapshot,
        payload.assisted_capture_confirmed,
    )
    guide_text, guide_access = _acquire_official_text(
        client,
        payload.guide_url,
        official_domain,
        payload.guide_snapshot,
        payload.assisted_capture_confirmed,
    )
    evidence = [
        make_evidence(
            "official-scope",
            payload.scope_url,
            "Official journal scope",
            scope_text,
            locator="page body",
            access_status=scope_access,
        ),
        make_evidence(
            "official-guide",
            payload.guide_url,
            "Official guide for authors",
            guide_text,
            locator="page body",
            access_status=guide_access,
        ),
    ]
    now = datetime.now(UTC).date()
    candidates = client.crossref_candidates(
        str(journal["issn"]), f"{now.year - 5}-{now.month:02d}-{now.day:02d}", now.isoformat()
    )
    preselected, _ = select_articles(candidates, str(journal["issn"]), set(), set(), today=now)
    if len(preselected) < 3:
        candidates.extend(
            client.openalex_candidates(
                str(journal["issn"]), f"{now.year - 5}-{now.month:02d}-{now.day:02d}", now.isoformat()
            )
        )
        preselected, _ = select_articles(candidates, str(journal["issn"]), set(), set(), today=now)
    hydrated: list[ArticleCandidate] = []
    limitations: list[str] = []
    warnings: list[str] = []
    for candidate in preselected:
        full_text, open_url = _acquire_open_text(client, candidate)
        hydrated.append(
            ArticleCandidate(
                title=candidate.title,
                doi=candidate.doi,
                issns=candidate.issns,
                published=candidate.published,
                authors=candidate.authors,
                canonical_url=candidate.canonical_url,
                open_url=open_url,
                full_text=full_text,
            )
        )
    selected, selection_limitations = select_articles(hydrated, str(journal["issn"]), set(), set(), today=now)
    warnings.extend(selection_limitations)
    for article in selected:
        if article.full_text and article.open_url:
            evidence.append(
                make_evidence(
                    "article",
                    article.open_url,
                    article.title,
                    article.full_text,
                    identifier=article.doi,
                    published_at=article.published.isoformat(),
                    locator="full text",
                )
            )
    private_texts = store.reference_texts(principal, project_id)
    for index, text in enumerate(private_texts, 1):
        if len(text.strip()) < 500:
            limitations.append(f"Uploaded reference {index} lacks sufficient extracted text")
            continue
        evidence.append(
            make_evidence(
                "article",
                None,
                f"Private uploaded reference {index}",
                text,
                locator="workspace-private extraction anchors",
                access_status="private-derived",
            )
        )
    claims, derivation_limitations = derive_profile(evidence)
    limitations.extend(item for item in derivation_limitations if item not in limitations)
    result: dict[str, object] = {
        "status": "degraded" if limitations else "complete",
        "selectedArticles": [
            {"title": item.title, "doi": item.doi, "publishedAt": item.published.isoformat(), "openUrl": item.open_url}
            for item in selected
        ],
        "sources": [
            {
                "sourceId": item.source_id,
                "sourceType": item.source_type,
                "canonicalUrl": item.canonical_url,
                "retrievedAt": item.retrieved_at,
                "contentHash": item.content_hash,
                "locator": item.locator,
                "accessStatus": item.access_status,
            }
            for item in evidence
            if item.access_status != "private-derived"
        ],
        "limitations": limitations,
        "warnings": warnings,
        "profilePreview": claims,
        "profileVersion": None,
    }
    if not limitations:
        repository = profile_repository(store)
        repository.migrate()
        result["profileVersion"] = repository.publish(
            str(journal["issn"]), evidence, claims, limitations, payload.expected_profile_version
        )
    store.audit(principal, "journal.researched", "project", project_id, {"status": str(result["status"])})
    return result


def _acquire_official_text(
    client: PoliteHttpClient,
    url: str,
    official_domain: str,
    assisted_snapshot: str | None,
    assisted_capture_confirmed: bool,
) -> tuple[str, str]:
    try:
        return html_to_text(client.get(url, allowed_domain=official_domain)), "open"
    except HTTPException as error:
        if not assisted_snapshot or not assisted_capture_confirmed:
            raise
        validate_public_https_url(url, official_domain)
        normalized = "\n".join(line.strip() for line in assisted_snapshot.splitlines() if line.strip())
        if len(normalized) < 500:
            raise HTTPException(
                status_code=422, detail="Assisted official-page snapshot has insufficient content"
            ) from error
        return normalized, "browser-assisted"


def _acquire_open_text(client: PoliteHttpClient, candidate: ArticleCandidate) -> tuple[str | None, str | None]:
    if not candidate.doi:
        return None, None
    url = f"https://api.unpaywall.org/v2/{candidate.doi}?email={client.contact_email}"
    try:
        record = json.loads(client.get(url))
        location = record.get("best_oa_location") or {}
        open_url = location.get("url_for_pdf") or location.get("url")
        if isinstance(open_url, str) and open_url.startswith("https://"):
            text = _extract_open_payload(client.get(open_url))
            if text:
                return text, open_url
    except HTTPException:
        pass
    return _acquire_arxiv_text(client, candidate)


def _extract_open_payload(payload: bytes) -> str | None:
    if payload.startswith(b"%PDF-"):
        try:
            extracted = validate_and_extract("reference-1", "open-source.pdf", "application/pdf", payload)
        except HTTPException:
            return None
        segments = cast(list[dict[str, object]], extracted["segments"])
        text = "\n".join(str(segment["text"]) for segment in segments)
    else:
        text = html_to_text(payload)
    return text if len(text.strip()) >= 500 else None


def _normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _acquire_arxiv_text(client: PoliteHttpClient, candidate: ArticleCandidate) -> tuple[str | None, str | None]:
    query = urlencode({"search_query": f'ti:"{candidate.title}"', "start": 0, "max_results": 5})
    try:
        feed = ET.fromstring(client.get(f"https://export.arxiv.org/api/query?{query}"))
    except (HTTPException, ET.ParseError):
        return None, None
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    expected = _normalized_title(candidate.title)
    matches: list[tuple[float, ET.Element]] = []
    for entry in feed.findall("atom:entry", namespace):
        title = _normalized_title(entry.findtext("atom:title", default="", namespaces=namespace))
        matches.append((SequenceMatcher(None, expected, title).ratio(), entry))
    if not matches:
        return None, None
    score, entry = max(matches, key=lambda item: item[0])
    if score < 0.93:
        return None, None
    pdf_url = next(
        (
            link.get("href")
            for link in entry.findall("atom:link", namespace)
            if link.get("type") == "application/pdf" and str(link.get("href", "")).startswith("https://")
        ),
        None,
    )
    if not pdf_url:
        identifier = entry.findtext("atom:id", default="", namespaces=namespace)
        arxiv_id = identifier.rsplit("/abs/", 1)[-1]
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id != identifier else None
    if not pdf_url:
        return None, None
    try:
        return _extract_open_payload(client.get(pdf_url)), pdf_url
    except HTTPException:
        return None, None


@app.get("/v1/journal-profiles/{version_id}", tags=["research"])
async def get_journal_profile_version(
    version_id: str, principal: PrincipalDependency, store: StoreDependency
) -> dict[str, object]:
    del principal  # Authentication is required; profiles contain shared, non-private derived knowledge.
    repository = profile_repository(store)
    repository.migrate()
    return repository.get(version_id)


@app.post("/v1/projects/{project_id}/research-starter", tags=["research"])
async def discover_with_research_starter(
    project_id: str,
    payload: ResearchStarterRequest,
    principal: PrincipalDependency,
    store: StoreDependency,
) -> dict[str, object]:
    store.get_project(principal, project_id)
    base_url = os.getenv("RESEARCH_STARTER_BASE_URL")
    api_key = os.getenv("RESEARCH_STARTER_API_KEY")
    if not base_url or not api_key:
        raise HTTPException(status_code=503, detail="Research Starter is not configured")
    result = ResearchStarterClient(base_url, api_key).report(
        payload.topic, payload.max_references, payload.max_top_papers
    )
    store.audit(
        principal,
        "research-starter.completed",
        "project",
        project_id,
        {"reportId": result.report_id, "contractVersion": result.contract_version},
    )
    return {
        "reportId": result.report_id,
        "contractVersion": result.contract_version,
        "references": result.references,
        "topPapers": result.top_papers,
        "coverage": result.coverage,
        "warnings": result.warnings,
        "aiUseDisclosure": result.ai_use_disclosure,
        "sourceRightsSummary": result.source_rights_summary,
        "candidateStatus": "unverified-until-journal-matcher-validation",
    }


@app.post("/v1/projects/{project_id}/analyses", status_code=201, tags=["analysis"])
async def create_analysis(
    project_id: str,
    payload: AnalysisRequest,
    principal: PrincipalDependency,
    store: StoreDependency,
) -> dict[str, object]:
    project = store.get_project(principal, project_id)
    journal = project.get("journal")
    if not project["readyForResearch"] or not isinstance(journal, dict):
        raise HTTPException(status_code=409, detail="A complete project is required")
    profiles = profile_repository(store)
    profiles.migrate()
    profile = profiles.get(payload.profile_version_id)
    if profile["journalIssn"] != journal["issn"] or profile["status"] != "published" or profile["limitations"]:
        raise HTTPException(status_code=409, detail="A complete validated profile for this journal is required")
    snapshots = profiles.official_snapshots(payload.profile_version_id)
    if {item["source_type"] for item in snapshots} != {"official-guide", "official-scope"}:
        raise HTTPException(status_code=409, detail="Official guide and scope snapshots are required")
    manuscript = store.manuscript_record(principal, project_id)
    manuscript_text = str(manuscript["text"])
    if len(manuscript_text.strip()) < 100:
        raise HTTPException(status_code=422, detail="Manuscript extraction is insufficient for anchored analysis")
    rules = extract_official_rules(snapshots)
    anchors = manuscript["anchors"]
    anchor = str(anchors[0]) if isinstance(anchors, list) and anchors else "document"
    segments = cast(list[dict[str, str]], manuscript.get("segments", []))
    recommendations = build_recommendations(manuscript_text, profile, rules, anchor, segments)
    limitations = ["Heuristic qualitative review is enabled; expert scientific validation remains required."]
    repository = analysis_repository(store)
    repository.migrate()
    result = repository.create(
        principal,
        project_id,
        payload.profile_version_id,
        str(manuscript["contentHash"]),
        scientific_invariants(manuscript_text),
        rules,
        recommendations,
        limitations,
    )
    store.audit(principal, "manuscript.analyzed", "analysis", str(result["id"]))
    return result


@app.get("/v1/analyses/{analysis_id}", tags=["analysis"])
async def get_analysis(analysis_id: str, principal: PrincipalDependency, store: StoreDependency) -> dict[str, object]:
    repository = analysis_repository(store)
    repository.migrate()
    return repository.get(principal, analysis_id)


@app.get("/v1/projects/{project_id}/latest-analysis", tags=["analysis"])
async def get_latest_project_analysis(
    project_id: str, principal: PrincipalDependency, store: StoreDependency
) -> dict[str, object]:
    store.get_project(principal, project_id)
    repository = analysis_repository(store)
    repository.migrate()
    return repository.latest_for_project(principal, project_id)


@app.post("/v1/analyses/{analysis_id}/ai-review", tags=["analysis"])
async def create_ai_review(
    analysis_id: str, principal: PrincipalDependency, store: StoreDependency
) -> dict[str, object]:
    repository = analysis_repository(store)
    repository.migrate()
    analysis = repository.get(principal, analysis_id)
    project = store.get_project(principal, str(analysis["projectId"]))
    manuscript = store.manuscript_record(principal, str(analysis["projectId"]))
    profiles = profile_repository(store)
    profile = profiles.get(str(analysis["profileVersionId"]))
    prompt, allowed_source_ids = build_editorial_prompt(
        journal_title=str(cast(dict[str, object], project["journal"])["title"]),
        manuscript_segments=cast(list[dict[str, object]], manuscript["segments"]),
        profile_claims=cast(list[dict[str, object]], profile["claims"]),
        official_rules=cast(list[dict[str, object]], analysis["rules"]),
        deterministic_recommendations=cast(list[dict[str, object]], analysis["recommendations"]),
    )
    try:
        result = GeminiEditorialClient().generate(prompt)
        recommendations = proposals_as_recommendations(
            result.response,
            profile_version_id=str(analysis["profileVersionId"]),
            allowed_source_ids=allowed_source_ids,
        )
    except GeminiConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    except GeminiProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    enriched = repository.add_ai_review(principal, analysis_id, recommendations, result.response.limitations)
    store.audit(
        principal,
        "analysis.ai-review.completed",
        "analysis",
        analysis_id,
        {"model": result.model, "proposalCount": str(len(recommendations))},
    )
    return enriched


@app.post("/v1/analyses/{analysis_id}/recommendations/{recommendation_id}/decision", tags=["analysis"])
async def decide_recommendation(
    analysis_id: str,
    recommendation_id: str,
    payload: DecisionRequest,
    principal: PrincipalDependency,
    store: StoreDependency,
) -> dict[str, object]:
    repository = analysis_repository(store)
    repository.migrate()
    result = repository.decide(principal, analysis_id, recommendation_id, payload.decision, payload.modified_text)
    store.audit(
        principal, "recommendation.decided", "recommendation", recommendation_id, {"decision": payload.decision}
    )
    return result


@app.post("/v1/analyses/{analysis_id}/artifacts", status_code=201, tags=["artifacts"])
async def generate_artifacts(
    analysis_id: str, principal: PrincipalDependency, store: StoreDependency
) -> dict[str, object]:
    repository = analysis_repository(store)
    repository.migrate()
    analysis = repository.get(principal, analysis_id)
    manuscript = store.manuscript_record(principal, str(analysis["projectId"]))
    recommendations = analysis["recommendations"]
    assert isinstance(recommendations, list)
    text = str(manuscript["text"])
    reconstructed = manuscript["mediaType"] == "application/pdf"
    original = store.read_private_object(principal, str(manuscript["objectKey"]))
    docx = (
        create_docx(text, recommendations, reconstructed) if reconstructed else annotate_docx(original, recommendations)
    )
    revision_lines = [text, "", "Accepted revision notes:"] + [
        f"[{item['category']}] {item.get('modifiedText') or item.get('proposedText') or item['rationale']}"
        for item in recommendations
        if isinstance(item, dict) and item.get("decision") in {"accepted", "modified"}
    ]
    revised_pdf = create_pdf("Revised manuscript - review copy", revision_lines)
    validate_invariant_preservation(text, "\n".join(revision_lines))
    validate_proposal_parity(docx, revised_pdf, recommendations)
    limitation_items = analysis["limitations"]
    if not isinstance(limitation_items, list):
        raise HTTPException(status_code=500, detail="Stored analysis limitations are invalid")
    report_lines = [
        "1. Executive summary",
        "No journal acceptance is guaranteed.",
        f"Analysis: {analysis_id}",
        f"Profile version: {analysis['profileVersionId']}",
        "2. Inputs and source coverage",
        f"Manuscript hash: {manuscript['contentHash']}",
        "Official guidance and journal-pattern evidence are identified in each recommendation.",
        "3. Guide compliance matrix",
        "Required items originate only from validated official-guide rules.",
        "4. Scientific and methodological review",
        "Scientific-impact proposals require explicit author-modified text and are never auto-applied.",
        "5. Article architecture and journal fit",
        "Observed patterns are advisory and never presented as official requirements.",
        "6. Presentation, language, and layout",
        "Category names accompany color annotations so meaning does not depend on color.",
        "7. Change ledger",
        *[f"Limitation: {item}" for item in limitation_items],
        *[
            f"{item['id']} | {item['severity']} | {item['basis']} | {item['decision']} | {item['rationale']}"
            for item in recommendations
            if isinstance(item, dict)
        ],
        "8. Unresolved items and author actions",
        *[
            f"Pending: {item['id']} | {item['rationale']}"
            for item in recommendations
            if isinstance(item, dict) and item.get("decision") == "pending"
        ],
        "9. Sources and reproducibility",
        f"Profile version: {analysis['profileVersionId']}; deterministic template: c4-standard-business-brief-1.",
    ]
    report_pdf = create_pdf("Article Fit revision report", report_lines)
    manifest_payload = {
        "schemaVersion": "1.0",
        "analysisId": analysis_id,
        "projectId": analysis["projectId"],
        "manuscriptHash": manuscript["contentHash"],
        "profileVersionId": analysis["profileVersionId"],
        "templateVersion": "c4-standard-business-brief-1",
        "model": None,
        "recommendationDecisions": [
            {"id": item["id"], "decision": item["decision"]} for item in recommendations if isinstance(item, dict)
        ],
        "generatedAt": datetime.now(UTC).isoformat(),
    }
    manifest = json.dumps(manifest_payload, indent=2, sort_keys=True).encode()
    validation = validate_artifacts(docx, revised_pdf, report_pdf, manifest)
    artifact_set = {
        "revised-manuscript.docx": docx,
        "revised-manuscript.pdf": revised_pdf,
        "revision-report.pdf": report_pdf,
        "provenance-manifest.json": manifest,
    }
    if isinstance(repository, HostedAnalysisRepository):
        result = repository.store_artifacts(principal, analysis_id, artifact_set, validation)
    else:
        if not isinstance(store, FoundationStore):  # pragma: no cover - factory invariant
            raise RuntimeError("Local analysis repository requires local foundation storage")
        result = store_artifact_set(store, repository, principal, analysis_id, artifact_set, validation)
    store.audit(principal, "artifacts.generated", "analysis", analysis_id)
    return result


@app.get("/v1/analyses/{analysis_id}/artifacts/{kind}", tags=["artifacts"])
async def download_artifact(
    analysis_id: str,
    kind: Literal[
        "revised-manuscript.docx", "revised-manuscript.pdf", "revision-report.pdf", "provenance-manifest.json"
    ],
    principal: PrincipalDependency,
    store: StoreDependency,
) -> Response:
    repository = analysis_repository(store)
    repository.migrate()
    key = repository.artifact_key(principal, analysis_id, kind)
    content = store.read_private_object(principal, key)
    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if kind.endswith(".docx")
        else "application/pdf"
        if kind.endswith(".pdf")
        else "application/json"
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{kind}"'},
    )


@app.delete("/v1/projects/{project_id}", status_code=204, tags=["projects"])
async def delete_project(project_id: str, principal: PrincipalDependency, store: StoreDependency) -> Response:
    store.delete_project(principal, project_id)
    return Response(status_code=204)
