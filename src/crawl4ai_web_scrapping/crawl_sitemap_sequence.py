import asyncio
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import requests
from xml.etree import ElementTree


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


async def crawl_sequential(urls: List[str]):
    print("\n=== Sequential Crawling with Session Reuse ===")

    browser_config = BrowserConfig(
        headless=True,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(markdown_generator=DefaultMarkdownGenerator())
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        session_id = "session1"
        for url in urls:
            result = await crawler.arun(
                url=url, config=crawl_config, session_id=session_id
            )
            if result.success:
                print(f"✅ Crawled: {url}")
                print(f"📝 Markdown length: {len(result.markdown.raw_markdown)}")
                print(f"📝 Markdown: {result.markdown}")
            else:
                print(f"❌ Failed: {url} - Error: {result.error_message}")
    finally:
        await crawler.close()


async def main():
    base_url = "https://docs.crawl4ai.com"  # changeable
    sitemap_url = discover_sitemap_url(base_url)
    if sitemap_url:
        urls = extract_urls_from_sitemap(sitemap_url)
        print(f"🔗 Found {len(urls)} URLs to crawl")
        await crawl_sequential(urls)
    else:
        print("No valid sitemap URL found.")


if __name__ == "__main__":
    asyncio.run(main())
