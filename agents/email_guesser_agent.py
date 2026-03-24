import os
import re
import json
import anthropic
from state import AgentState


CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def email_guesser_agent(state: AgentState) -> AgentState:
    """
    Uses Claude to:
    1. Guess email patterns from company domain
    2. Generate likely founder/contact emails
    """
    company = state["company_name"]
    founder = state.get("founder_name", "")
    website = state.get("company_website", "")

    if not website:
        return {
            **state,
            "messages": ["⚠️ No domain available for email guessing, skipping..."],
            "current_step": "guesser_done"
        }

    # Extract domain from website
    domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/\s]+)', website)
    domain = domain_match.group(1) if domain_match else None

    if not domain:
        return {
            **state,
            "messages": ["⚠️ Could not extract domain, skipping guesser..."],
            "current_step": "guesser_done"
        }

    prompt = f"""You are an email pattern expert. Given a company and founder info, generate the most likely email addresses.

Company: {company}
Domain: {domain}
{f"Founder name: {founder}" if founder else ""}

Generate the top 5 most likely email addresses for this company's founder/CEO/contact.

Common patterns:
- firstname@domain.com
- firstname.lastname@domain.com
- f.lastname@domain.com
- flastname@domain.com
- hello@domain.com
- contact@domain.com
- info@domain.com

Return ONLY a JSON array like this:
["email1@domain.com", "email2@domain.com", "email3@domain.com"]

No explanation, just the JSON array."""

    guessed = []
    try:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text

        # Parse JSON array
        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
        if json_match:
            emails_list = json.loads(json_match.group())
            for email in emails_list:
                if "@" in email and domain in email:
                    guessed.append({
                        "email": email.strip().lower(),
                        "source": "claude_guesser",
                        "confidence": "low"
                    })
    except Exception as e:
        return {
            **state,
            "errors": [f"Claude guesser error: {str(e)}"],
            "messages": ["⚠️ Email guesser failed, continuing..."],
            "current_step": "guesser_done"
        }

    return {
        **state,
        "guessed_emails": guessed,
        "messages": [f"🤖 Claude guessed {len(guessed)} potential emails for domain {domain}"],
        "current_step": "guesser_done"
    }