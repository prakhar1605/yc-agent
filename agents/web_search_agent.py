import os
import requests
from state import AgentState


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_openrouter(prompt: str, model: str = "perplexity/sonar") -> str:
    """Call OpenRouter API with given model."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://email-extractor.app",
        "X-Title": "Email Extractor",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {str(e)}"


def web_search_agent(state: AgentState) -> AgentState:
    """
    Uses OpenRouter (Perplexity Sonar) to search the web for:
    - Company official website
    - Founder email if publicly available
    - Contact page URLs
    """
    company = state["company_name"]
    founder = state.get("founder_name", "")

    query = f"""
Search for the following and return ONLY a JSON object with these exact keys:
{{
  "official_website": "https://...",
  "contact_page": "https://.../contact",
  "emails_found": ["email1@domain.com", "email2@domain.com"],
  "founder_linkedin": "https://linkedin.com/in/...",
  "notes": "any relevant info"
}}

Search query: Find official website and contact email for company "{company}"
{f'Founder name: {founder}' if founder else ''}

Search for:
1. Official website of {company}
2. Contact or team page emails
3. {f"{founder}'s email or LinkedIn" if founder else "founder/CEO email"}

Return ONLY the JSON, no explanation.
"""

    result = call_openrouter(query)

    # Parse result
    import json, re
    emails_found = []
    website = None

    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            website = data.get("official_website")
            for email in data.get("emails_found", []):
                if "@" in email and "." in email:
                    emails_found.append({
                        "email": email.strip().lower(),
                        "source": "web_search",
                        "confidence": "high"
                    })
    except Exception as e:
        pass

    # Fallback: extract emails from raw text
    if not emails_found:
        raw_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', result)
        for email in raw_emails:
            emails_found.append({
                "email": email.strip().lower(),
                "source": "web_search_raw",
                "confidence": "medium"
            })

    return {
        **state,
        "company_website": website,
        "raw_emails": emails_found,
        "messages": [f"🔍 Web search done. Found {len(emails_found)} emails, website: {website}"],
        "current_step": "web_search_done"
    }