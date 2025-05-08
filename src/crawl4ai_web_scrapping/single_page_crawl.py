import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://github.com/unclecode/crawl4ai")
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
