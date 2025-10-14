import asyncio
import logging
from typing import Any, AsyncIterator, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from cerebraui.config import (
    ENABLE_DEEP_RESEARCH,
    DEEP_RESEARCH_BASE_URL,
    DEEP_RESEARCH_API_KEY,
    DEEP_RESEARCH_WORKFLOW_ID,
)
from cerebraui.constants import ERROR_MESSAGES
from cerebraui.utils.auth import get_verified_user


log = logging.getLogger(__name__)

router = APIRouter()


class DeepResearchNotEnabled(Exception):
    pass


def _ensure_enabled():
    if not ENABLE_DEEP_RESEARCH:
        raise DeepResearchNotEnabled("Deep research feature is disabled")
    if not DEEP_RESEARCH_BASE_URL:
        raise ValueError("DEEP_RESEARCH_BASE_URL is not configured")


def _build_headers(token: Optional[str] = None) -> Dict[str, str]:
    headers: Dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    api_key = DEEP_RESEARCH_API_KEY or token
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    return headers


def _workflow_id(workflow_id: Optional[str]) -> str:
    return workflow_id or DEEP_RESEARCH_WORKFLOW_ID or "wf_basic"


async def _raise_for_error(response: httpx.Response):
    if response.is_success:
        return

    try:
        detail = response.json()
    except Exception:  # pylint: disable=broad-except
        detail = {"detail": response.text or "Unknown error"}

    log.error("Deep research request failed: %s", detail)
    raise HTTPException(status_code=response.status_code, detail=detail)


async def _start_run(
    request: Request,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    _ensure_enabled()

    base_url = DEEP_RESEARCH_BASE_URL.rstrip("/")
    url = f"{base_url}/ai/agent/run"

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        headers = _build_headers(request.state.token.credentials if hasattr(request.state, "token") else None)
        response = await client.post(url, json=payload, headers=headers)
        await _raise_for_error(response)
        return response.json()


async def _get_json(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        response = await client.get(url, headers=headers)
        await _raise_for_error(response)
        return response.json()


async def _stream_events(
    url: str,
    headers: Dict[str, str],
) -> AsyncIterator[bytes]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(None, connect=10.0)) as client:
        async with client.stream("GET", url, headers=headers) as response:
            await _raise_for_error(response)
            async for chunk in response.aiter_raw():
                yield chunk


@router.post("/start")
async def start_deep_research(
    request: Request,
    body: Dict[str, Any],
    user=Depends(get_verified_user),
):
    try:
        workflow_id = _workflow_id(body.get("workflow_id"))
        payload = {
            "workflow_id": workflow_id,
            "inputs": body.get("inputs", {}),
            "params": body.get("params", {}),
        }

        run = await _start_run(request, payload)
        return run
    except DeepResearchNotEnabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Deep research is disabled",
        ) from None
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("Failed to start deep research run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(str(exc)),
        ) from exc


@router.get("/{run_id}/status")
async def get_run_status(
    request: Request,
    run_id: str,
    user=Depends(get_verified_user),
):
    try:
        _ensure_enabled()
        base_url = DEEP_RESEARCH_BASE_URL.rstrip("/")
        url = f"{base_url}/ai/agent/{run_id}/status"
        headers = _build_headers(request.state.token.credentials if hasattr(request.state, "token") else None)
        return await _get_json(url, headers)
    except DeepResearchNotEnabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Deep research is disabled",
        ) from None
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("Failed to fetch deep research status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(str(exc)),
        ) from exc


@router.get("/{run_id}/stream")
async def stream_run(
    request: Request,
    run_id: str,
    user=Depends(get_verified_user),
):
    try:
        _ensure_enabled()
        base_url = DEEP_RESEARCH_BASE_URL.rstrip("/")
        url = f"{base_url}/ai/agent/{run_id}/stream"
        headers = _build_headers(request.state.token.credentials if hasattr(request.state, "token") else None)

        async def event_generator():
            try:
                async for chunk in _stream_events(url, headers):
                    yield chunk
            except httpx.HTTPError as exc:
                log.error("Deep research stream error: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to stream deep research run",
                ) from exc

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except DeepResearchNotEnabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Deep research is disabled",
        ) from None


@router.post("/{run_id}/cancel")
async def cancel_run(
    request: Request,
    run_id: str,
    user=Depends(get_verified_user),
):
    try:
        _ensure_enabled()
        base_url = DEEP_RESEARCH_BASE_URL.rstrip("/")
        url = f"{base_url}/ai/agent/{run_id}/cancel"
        headers = _build_headers(request.state.token.credentials if hasattr(request.state, "token") else None)

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            response = await client.post(url, headers=headers)
            await _raise_for_error(response)
            return response.json()
    except DeepResearchNotEnabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Deep research is disabled",
        ) from None
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("Failed to cancel deep research run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(str(exc)),
        ) from exc


