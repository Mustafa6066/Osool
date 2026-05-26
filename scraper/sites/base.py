"""Abstract base class shared by all site spiders."""
from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class SpiderResult:
    raw_properties: list[dict] = field(default_factory=list)
    pages_fetched: int = 0
    pages_failed: int = 0


class SiteSpider(abc.ABC):
    """Each site spider returns a list of dicts shaped for RawScrapedProperty."""

    name: str = "base"

    @abc.abstractmethod
    async def crawl_area(self, area_slug: str, dry_run: bool = False) -> SpiderResult:
        """Scrape every listing under one Egyptian zone slug."""

    @abc.abstractmethod
    async def crawl_compound(self, compound_slug: str, dry_run: bool = False) -> SpiderResult:
        """Scrape a single compound/listing by slug. Used by the on-demand worker."""
