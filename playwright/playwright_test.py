import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://tago.kr/service/ioniq6_monthly.htm")
        print(f"title: {await page.title()}")
        print(f"content: {await page.content()}")
        await browser.close()

asyncio.run(main())