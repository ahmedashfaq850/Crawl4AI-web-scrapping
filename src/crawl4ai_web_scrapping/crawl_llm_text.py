"""
4-crawl_and_chunk_markdown.py (Enhanced)
----------------------------------------
Scrapes a Markdown (.md or .txt) page using Crawl4AI, then splits the content into chunks based on # and ## headers.
Prints and optionally saves each chunk for further processing.
"""

import asyncio
import re
import time
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


async def scrape_and_chunk_markdown(url: str, save_to_file: bool = False):
    """
    Scrape a Markdown page and split into chunks by # and ## headers.
    Optionally saves chunks to a file.
    """
    print(f"🚀 Starting crawl: {url}")
    browser_config = BrowserConfig(headless=True)
    crawl_config = CrawlerRunConfig()

    start_time = time.time()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawl_config)
        if not result.success:
            print(f"❌ Failed to crawl {url}:\n  {result.error_message}")
            return

        markdown = result.markdown.strip()
        if not markdown:
            print("⚠️ Empty markdown content received.")
            return

        # Regex to find headers
        header_pattern = re.compile(r"^(# .+|## .+)$", re.MULTILINE)
        headers = [m.start() for m in header_pattern.finditer(markdown)] + [
            len(markdown)
        ]

        # Extract chunks between headers
        chunks = []
        for i in range(len(headers) - 1):
            chunk = markdown[headers[i] : headers[i + 1]].strip()
            if chunk:
                chunks.append(chunk)

        elapsed = time.time() - start_time
        print(f"✅ Split into {len(chunks)} chunks in {elapsed:.2f}s")

        for idx, chunk in enumerate(chunks):
            print(f"\n🔹 Chunk {idx + 1}:\n{chunk}\n{'-'*40}")

        if save_to_file:
            with open("markdown_chunks.txt", "w", encoding="utf-8") as f:
                for idx, chunk in enumerate(chunks):
                    f.write(f"--- Chunk {idx + 1} ---\n{chunk}\n\n")
            print("💾 Chunks saved to 'markdown_chunks.txt'")


if __name__ == "__main__":
    url = "https://ai.pydantic.dev/llms-full.txt"
    asyncio.run(scrape_and_chunk_markdown(url, save_to_file=True))
