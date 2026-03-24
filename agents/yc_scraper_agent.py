import re
import asyncio
from state import AgentState


def yc_scraper_agent(state: AgentState) -> AgentState:
    """
    Scrapes YC directory for company info and emails.
    Uses Playwright for JS-rendered pages.
    """
    company = state["company_name"]
    emails_found = []
    yc_url = None

    try:
        result = asyncio.run(_scrape_yc(company))
        emails_found = result["emails"]
        yc_url = result["url"]
    except Exception as e:
        return {
            **state,
            "errors": [f"YC scraper error: {str(e)}"],
            "messages": ["⚠️ YC scraper failed, continuing..."],
            "current_step": "yc_done"
        }

    return {
        **state,
        "yc_profile_url": yc_url,
        "raw_emails": emails_found,
        "messages": [f"🟠 YC scrape done. Found {len(emails_found)} emails."],
        "current_step": "yc_done"
    }


async def _scrape_yc(company_name: str) -> dict:
    """Async playwright scraping of YC directory."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"emails": [], "url": None}

    emails = []
    found_url = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Set user agent to avoid blocks
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        try:
            # Search YC directory
            search_url = f"https://www.ycombinator.com/companies?q={company_name.replace(' ', '+')}"
            await page.goto(search_url, timeout=20000)
            await page.wait_for_timeout(3000)

            # Get page HTML
            html = await page.content()

            # Extract emails from page
            raw = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
            for email in raw:
                if not any(x in email for x in ["ycombinator", "example", "test"]):
                    emails.append({
                        "email": email.lower(),
                        "source": "yc_directory",
                        "confidence": "high"
                    })

            # Try to find company link and visit it
            company_link = await page.query_selector(f'a[href*="/companies/"]')
            if company_link:
                href = await company_link.get_attribute("href")
                if href:
                    found_url = f"https://www.ycombinator.com{href}" if href.startswith("/") else href
                    await page.goto(found_url, timeout=15000)
                    await page.wait_for_timeout(2000)
                    html2 = await page.content()
                    more_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html2)
                    for email in more_emails:
                        if not any(x in email for x in ["ycombinator", "example"]):
                            emails.append({
                                "email": email.lower(),
                                "source": "yc_profile_page",
                                "confidence": "high"
                            })

        except Exception as e:
            pass
        finally:
            await browser.close()

    # Deduplicate
    seen = set()
    unique = []
    for e in emails:
        if e["email"] not in seen:
            seen.add(e["email"])
            unique.append(e)

    return {"emails": unique, "url": found_url}