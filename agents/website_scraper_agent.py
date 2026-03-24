import re
import asyncio
from state import AgentState


CONTACT_PATHS = [
    "/contact", "/contact-us", "/about", "/team",
    "/about-us", "/people", "/founders", "/hire",
]


def website_scraper_agent(state: AgentState) -> AgentState:
    """
    Scrapes company official website for emails.
    Tries homepage + common contact/about pages.
    """
    website = state.get("company_website")
    if not website:
        return {
            **state,
            "messages": ["⚠️ No website found to scrape, skipping..."],
            "current_step": "website_done"
        }

    try:
        result = asyncio.run(_scrape_website(website))
        emails = result["emails"]
    except Exception as e:
        return {
            **state,
            "errors": [f"Website scraper error: {str(e)}"],
            "messages": ["⚠️ Website scraper failed, continuing..."],
            "current_step": "website_done"
        }

    return {
        **state,
        "raw_emails": emails,
        "messages": [f"🌐 Website scrape done. Found {len(emails)} emails from {website}"],
        "current_step": "website_done"
    }


async def _scrape_website(base_url: str) -> dict:
    """Scrape homepage + contact pages for emails."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"emails": []}

    # Clean URL
    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    emails = []
    seen = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        urls_to_try = [base_url] + [base_url.rstrip("/") + path for path in CONTACT_PATHS]

        for url in urls_to_try[:5]:  # Max 5 pages
            try:
                await page.goto(url, timeout=12000, wait_until="domcontentloaded")
                await page.wait_for_timeout(1500)
                html = await page.content()

                # Extract emails
                found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
                for email in found:
                    email = email.lower()
                    # Filter out common junk
                    if (email not in seen and
                        not any(x in email for x in ["example", "test@", "noreply", "no-reply", "sentry", "wixpress", "schema"])):
                        seen.add(email)
                        emails.append({
                            "email": email,
                            "source": f"website:{url}",
                            "confidence": "high" if "/contact" in url or "/team" in url else "medium"
                        })

                if len(emails) >= 10:
                    break

            except Exception:
                continue

        await browser.close()

    return {"emails": emails}