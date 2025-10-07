import validators

from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel


def get_filtered_results(results, filter_list):
    if not filter_list:
        return results
    filtered_results = []
    for result in results:
        url = result.get("url") or result.get("link", "")
        if not validators.url(url):
            continue
        domain = urlparse(url).netloc
        if any(domain.endswith(filtered_domain) for filtered_domain in filter_list):
            filtered_results.append(result)
    return filtered_results


def get_favicon_url(url: str) -> str:
    """Generate favicon URL for a given website URL using Google's favicon service"""
    try:
        domain = urlparse(url).netloc
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
    except:
        return None


def get_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    try:
        return urlparse(url).netloc
    except:
        return url


class SearchResult(BaseModel):
    link: str
    title: Optional[str]
    snippet: Optional[str]
    engine: Optional[str] = None
    favicon_url: Optional[str] = None
    domain: Optional[str] = None
