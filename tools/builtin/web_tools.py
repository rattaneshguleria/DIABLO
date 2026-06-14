"""Built-in web search and page fetching tools."""

from __future__ import annotations

from typing import Any

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from tools.base import RiskLevel, Tool, ToolParameter, ToolResult


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web using DuckDuckGo and return result titles, URLs, and snippets."
    risk_level = RiskLevel.MEDIUM
    parameters = [
        ToolParameter(
            name="query",
            type="string",
            description="Search query",
        ),
        ToolParameter(
            name="max_results",
            type="integer",
            description="Maximum number of results (default 5)",
            required=False,
        ),
    ]

    def run(self, **kwargs: Any) -> ToolResult:
        query = str(kwargs.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, output="", error="Query cannot be empty")

        max_results = int(kwargs.get("max_results") or 5)
        results: list[str] = []

        with DDGS() as ddgs:
            for index, item in enumerate(ddgs.text(query, max_results=max_results), start=1):
                title = item.get("title", "Untitled")
                url = item.get("href", "")
                snippet = item.get("body", "")
                results.append(f"{index}. {title}\n   URL: {url}\n   {snippet}")

        if not results:
            return ToolResult(success=True, output="No search results found.")
        return ToolResult(success=True, output="\n\n".join(results))


class FetchUrlTool(Tool):
    name = "fetch_url"
    description = "Fetch a web page and return extracted text content."
    risk_level = RiskLevel.MEDIUM
    parameters = [
        ToolParameter(
            name="url",
            type="string",
            description="HTTP or HTTPS URL to fetch",
        ),
        ToolParameter(
            name="max_chars",
            type="integer",
            description="Maximum characters to return (default 4000)",
            required=False,
        ),
    ]

    def run(self, **kwargs: Any) -> ToolResult:
        url = str(kwargs.get("url", "")).strip()
        if not url.startswith(("http://", "https://")):
            return ToolResult(success=False, output="", error="URL must start with http:// or https://")

        max_chars = int(kwargs.get("max_chars") or 4000)
        try:
            response = httpx.get(url, timeout=20.0, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return ToolResult(success=False, output="", error=f"Failed to fetch URL: {exc}")

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = " ".join(soup.get_text(separator=" ", strip=True).split())
        if len(text) > max_chars:
            text = text[:max_chars] + "... [truncated]"
        return ToolResult(success=True, output=text or "(empty page)")
