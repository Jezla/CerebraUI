# backend/open_webui/routers/crawl.py
import sys, asyncio
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import APIRouter, Query, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

router = APIRouter(tags=["crawl"])

class CrawlItem(BaseModel):
    url: str
    title: Optional[str] = None
    success: bool
    markdown: Optional[str] = None
    error: Optional[str] = None


def _pick_markdown(res) -> Optional[str]:
    """Helper to select the best available markdown content from the crawl result."""
    md = getattr(res, "markdown", None)
    if md is None:
        return None
    fit = getattr(md, "fit_markdown", None)
    if isinstance(fit, str) and fit.strip():
        return fit
    raw = getattr(md, "raw_markdown", None)
    if isinstance(raw, str) and raw.strip():
        return raw
    if isinstance(md, str):
        return md
    return None


async def crawl_many(urls: List[str], timeout: int = 15) -> List[CrawlItem]:
    """Run concurrent crawling for multiple URLs with Crawl4AI."""
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        page_timeout=timeout * 1000,
        check_robots_txt=True,
        word_count_threshold=20,
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(urls, config=run_cfg)

    items: List[CrawlItem] = []
    for r in results:
        title = None
        meta = getattr(r, "metadata", None)
        if meta and isinstance(meta, dict):
            title = meta.get("title")

        items.append(
            CrawlItem(
                url=r.url,
                title=title,
                success=bool(getattr(r, "success", False)),
                markdown=_pick_markdown(r),
                error=None if getattr(r, "success", False) else getattr(r, "error_message", None),
            )
        )

    # Deduplicate results
    seen = set()
    deduped: List[CrawlItem] = []
    for it in items:
        key = (it.markdown or it.error or it.url)[:2000]
        if key not in seen:
            seen.add(key)
            deduped.append(it)

    return deduped


@router.get(
    "/crawl",
    response_model=List[CrawlItem],
    summary="Crawl one or more webpages"
)
async def crawl_endpoint(
    request: Request,
    url: Optional[str] = Query(None, description="Single URL, e.g. https://example.com"),
    urls: Optional[List[str]] = Query(None, description="Multiple URLs; can be added multiple times or comma-separated"),
    timeout: int = Query(15, ge=5, le=60, description="Request timeout in seconds"),
):
    targets: List[str] = []

    if urls:
        for v in urls:
            if v:
                if "," in v:
                    targets.extend([p.strip() for p in v.split(",") if p.strip()])
                else:
                    targets.append(v.strip())

    raw_list = request.query_params.getlist("urls")
    for v in raw_list:
        if v:
            if "," in v:
                targets.extend([p.strip() for p in v.split(",") if p.strip()])
            else:
                targets.append(v.strip())

    if not targets and url:
        targets = [url.strip()]

    # Filter valid schemes
    targets = [u for u in targets if u.startswith(("http://", "https://", "file://", "raw:"))]
    # Remove duplicates while preserving order
    targets = list(dict.fromkeys(targets))

    if not targets:
        raise HTTPException(400, "A valid url or urls must be provided (starting with http(s))")

    # Limit to 10 URLs per request
    if len(targets) > 10:
        targets = targets[:10]

    return await crawl_many(targets, timeout=timeout)
