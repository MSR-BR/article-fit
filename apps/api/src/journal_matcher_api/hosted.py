"""Small server-only Supabase boundary for hosted persistence and queues."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException


@dataclass(frozen=True)
class SupabaseSettings:
    url: str
    service_role_key: str

    def __post_init__(self) -> None:
        if not self.url.startswith("https://"):
            raise ValueError("SUPABASE_URL must use HTTPS")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")


class SupabaseHttpClient:
    """Use PostgREST and Storage without exposing privileged credentials."""

    def __init__(self, settings: SupabaseSettings, timeout: float = 30.0) -> None:
        self._base_url = settings.url.rstrip("/")
        self._key = settings.service_role_key
        self._timeout = timeout

    def table(
        self,
        name: str,
        *,
        method: str = "GET",
        query: dict[str, str] | None = None,
        payload: object | None = None,
        prefer: str | None = None,
    ) -> object:
        return self._json_request(
            f"/rest/v1/{quote(name, safe='')}", method=method, query=query, payload=payload, prefer=prefer
        )

    def rpc(self, function: str, payload: dict[str, object], *, schema: str = "public") -> object:
        return self._json_request(
            f"/rest/v1/rpc/{quote(function, safe='')}",
            method="POST",
            payload=payload,
            extra_headers={"Accept-Profile": schema, "Content-Profile": schema},
        )

    def upload(self, bucket: str, object_key: str, content: bytes, media_type: str) -> None:
        self._request(
            f"/storage/v1/object/{quote(bucket, safe='')}/{quote(object_key, safe='/')}",
            method="POST",
            body=content,
            content_type=media_type,
            extra_headers={"x-upsert": "false"},
        )

    def download(self, bucket: str, object_key: str) -> bytes:
        return self._request(
            f"/storage/v1/object/authenticated/{quote(bucket, safe='')}/{quote(object_key, safe='/')}",
            method="GET",
        )

    def delete_objects(self, bucket: str, object_keys: list[str]) -> None:
        if object_keys:
            self._json_request(
                f"/storage/v1/object/{quote(bucket, safe='')}",
                method="DELETE",
                payload={"prefixes": object_keys},
            )

    def _json_request(
        self,
        path: str,
        *,
        method: str,
        query: dict[str, str] | None = None,
        payload: object | None = None,
        prefer: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> object:
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        raw = self._request(
            path,
            method=method,
            query=query,
            body=body,
            content_type="application/json",
            extra_headers={**(extra_headers or {}), **({"Prefer": prefer} if prefer else {})},
        )
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise HTTPException(status_code=502, detail="Hosted persistence returned invalid JSON") from error

    def _request(
        self,
        path: str,
        *,
        method: str,
        query: dict[str, str] | None = None,
        body: bytes | None = None,
        content_type: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> bytes:
        suffix = f"?{urlencode(query)}" if query else ""
        headers = {"apikey": self._key, "Authorization": f"Bearer {self._key}", **(extra_headers or {})}
        if content_type:
            headers["Content-Type"] = content_type
        request = Request(f"{self._base_url}{path}{suffix}", data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self._timeout) as response:  # noqa: S310 - fixed trusted base URL
                return cast(bytes, response.read())
        except HTTPError as error:
            # Do not include response bodies: upstream errors can echo private data.
            if error.code in {401, 403}:
                raise HTTPException(status_code=503, detail="Hosted persistence authorization failed") from None
            if error.code == 404:
                raise HTTPException(status_code=404, detail="Hosted resource not found") from None
            if error.code == 409:
                raise HTTPException(status_code=409, detail="Hosted persistence conflict") from None
            raise HTTPException(status_code=502, detail=f"Hosted persistence failed ({error.code})") from None
        except (TimeoutError, URLError) as error:
            raise HTTPException(status_code=503, detail="Hosted persistence is temporarily unavailable") from error


def require_rows(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise HTTPException(status_code=502, detail="Hosted persistence returned an invalid row set")
    return value
