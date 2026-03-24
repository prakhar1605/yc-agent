from typing import TypedDict, List, Optional, Annotated
import operator


class EmailResult(TypedDict):
    email: str
    source: str
    confidence: str  # high / medium / low


class AgentState(TypedDict):
    # Input
    company_name: str
    founder_name: Optional[str]

    # Intermediate results
    company_website: Optional[str]
    yc_profile_url: Optional[str]
    raw_emails: Annotated[List[EmailResult], operator.add]
    guessed_emails: Annotated[List[EmailResult], operator.add]
    scraped_pages: Annotated[List[str], operator.add]

    # Final output
    verified_emails: List[EmailResult]
    final_emails: List[EmailResult]

    # Control flow
    current_step: str
    errors: Annotated[List[str], operator.add]
    messages: Annotated[List[str], operator.add]