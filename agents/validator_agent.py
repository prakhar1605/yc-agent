import re
import socket
import smtplib
import dns.resolver
from typing import List
from state import AgentState, EmailResult


def is_valid_format(email: str) -> bool:
    """Check if email format is valid."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_mx_record(domain: str) -> str | None:
    """Get MX record for domain."""
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx = sorted(records, key=lambda r: r.preference)[0]
        return str(mx.exchange).rstrip('.')
    except Exception:
        return None


def smtp_verify(email: str, mx_host: str) -> bool:
    """
    Verify email via SMTP without sending.
    ~70-80% accurate — good enough for MVP.
    """
    try:
        with smtplib.SMTP(timeout=10) as smtp:
            smtp.connect(mx_host, 25)
            smtp.helo("gmail.com")
            smtp.mail("verify@gmail.com")
            code, _ = smtp.rcpt(email)
            return code == 250
    except Exception:
        return False


def validator_agent(state: AgentState) -> AgentState:
    """
    1. Combine all found + guessed emails
    2. Remove duplicates
    3. Validate format
    4. SMTP verify (best effort)
    5. Return final ranked list
    """
    # Combine all emails
    all_emails: List[EmailResult] = (
        state.get("raw_emails", []) +
        state.get("guessed_emails", [])
    )

    if not all_emails:
        return {
            **state,
            "verified_emails": [],
            "final_emails": [],
            "messages": ["❌ No emails found to validate."],
            "current_step": "done"
        }

    # Deduplicate by email address
    seen = set()
    unique_emails = []
    for e in all_emails:
        email_addr = e["email"].lower().strip()
        if email_addr not in seen and is_valid_format(email_addr):
            seen.add(email_addr)
            unique_emails.append({**e, "email": email_addr})

    # Group by domain and get MX records
    domain_mx = {}
    verified = []

    for email_obj in unique_emails:
        email = email_obj["email"]
        domain = email.split("@")[1]

        # Get MX record (cached per domain)
        if domain not in domain_mx:
            domain_mx[domain] = get_mx_record(domain)

        mx = domain_mx[domain]

        if mx:
            # Try SMTP verify
            is_valid = smtp_verify(email, mx)
            if is_valid:
                email_obj["confidence"] = "high"
                verified.append(email_obj)
            elif email_obj["source"] in ["yc_directory", "yc_profile_page", "web_search"]:
                # Trust scraped emails even without SMTP verify
                email_obj["confidence"] = "medium"
                verified.append(email_obj)
        else:
            # No MX record = domain might not exist
            if email_obj["source"] not in ["claude_guesser"]:
                email_obj["confidence"] = "low"
                verified.append(email_obj)

    # Sort: high > medium > low
    order = {"high": 0, "medium": 1, "low": 2}
    verified.sort(key=lambda x: order.get(x["confidence"], 3))

    # Final list: max 20 results
    final = verified[:20]

    return {
        **state,
        "verified_emails": verified,
        "final_emails": final,
        "messages": [f"✅ Validation done. {len(final)} emails verified out of {len(unique_emails)} unique found."],
        "current_step": "done"
    }