import os
import sys
import psutil
import asyncio
import requests
from typing import List
from xml.etree import ElementTree
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    MemoryAdaptiveDispatcher,
)

COMMON_SITEMAP_PATHS = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap/sitemap.xml"]


def discover_sitemap_url(base_url: str) -> str | None:
    for path in COMMON_SITEMAP_PATHS:
        sitemap_url = base_url.rstrip("/") + path
        try:
            response = requests.get(sitemap_url, timeout=5)
            if response.status_code == 200 and "xml" in response.headers.get(
                "Content-Type", ""
            ):
                print(f"✅ Sitemap found: {sitemap_url}")
                return sitemap_url
        except Exception as e:
            print(f"Error checking {sitemap_url}: {e}")
    print("❌ No sitemap found.")
    return None


def extract_urls_from_sitemap(sitemap_url: str) -> List[str]:
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()

        root = ElementTree.fromstring(response.content)
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [loc.text for loc in root.findall(".//ns:loc", namespace)]

        return urls
    except Exception as e:
        print(f"Error parsing sitemap: {e}")
        return []


async def crawl_parallel(urls: List[str], max_concurrent: int = 10):
    print("\n=== Parallel Crawling with arun_many + Dispatcher ===")

    peak_memory = 0
    process = psutil.Process(os.getpid())

    def log_memory(prefix: str = ""):
        nonlocal peak_memory
        current_mem = process.memory_info().rss
        if current_mem > peak_memory:
            peak_memory = current_mem
        print(
            f"{prefix} Memory - Current: {current_mem // (1024 * 1024)} MB, Peak: {peak_memory // (1024 * 1024)} MB"
        )

    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )

    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=max_concurrent,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        log_memory("📊 Before crawling:")
        results = await crawler.arun_many(
            urls=urls, config=crawl_config, dispatcher=dispatcher
        )

        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count

        for result in results:
            if not result.success:
                print(f"❌ Error crawling {result.url}: {result.error_message}")

        print(f"\n✅ Crawled {success_count} URLs successfully")
        print(f"❌ Failed to crawl {fail_count} URLs")
        log_memory("📊 After crawling:")
        print(f"\n📈 Peak Memory Usage: {peak_memory // (1024 * 1024)} MB")


async def main():
    base_url = "https://ai.pydantic.dev"  # can be replaced dynamically
    sitemap_url = discover_sitemap_url(base_url)
    if sitemap_url:
        urls = extract_urls_from_sitemap(sitemap_url)
        if urls:
            print(f"🔗 Found {len(urls)} URLs to crawl")
            await crawl_parallel(urls, max_concurrent=10)
        else:
            print("⚠️ Sitemap found but no URLs extracted.")
    else:
        print("🚫 No sitemap found.")


if __name__ == "__main__":
    asyncio.run(main())
