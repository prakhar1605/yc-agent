from langgraph.graph import StateGraph, END
from state import AgentState
from agents.web_search_agent import web_search_agent
from agents.yc_scraper_agent import yc_scraper_agent
from agents.website_scraper_agent import website_scraper_agent
from agents.email_guesser_agent import email_guesser_agent
from agents.validator_agent import validator_agent


def build_graph():
    """
    Build the LangGraph agent pipeline.

    Flow:
    web_search → yc_scraper → website_scraper → email_guesser → validator → END
    """
    graph = StateGraph(AgentState)

    # Add all agent nodes
    graph.add_node("web_search", web_search_agent)
    graph.add_node("yc_scraper", yc_scraper_agent)
    graph.add_node("website_scraper", website_scraper_agent)
    graph.add_node("email_guesser", email_guesser_agent)
    graph.add_node("validator", validator_agent)

    # Define edges (sequential pipeline)
    graph.set_entry_point("web_search")
    graph.add_edge("web_search", "yc_scraper")
    graph.add_edge("yc_scraper", "website_scraper")
    graph.add_edge("website_scraper", "email_guesser")
    graph.add_edge("email_guesser", "validator")
    graph.add_edge("validator", END)

    return graph.compile()


def run_extraction(company_name: str, founder_name: str = "") -> AgentState:
    """
    Run the full email extraction pipeline.
    Returns final AgentState with all results.
    """
    graph = build_graph()

    initial_state: AgentState = {
        "company_name": company_name,
        "founder_name": founder_name if founder_name else None,
        "company_website": None,
        "yc_profile_url": None,
        "raw_emails": [],
        "guessed_emails": [],
        "scraped_pages": [],
        "verified_emails": [],
        "final_emails": [],
        "current_step": "start",
        "errors": [],
        "messages": [],
    }

    final_state = graph.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    # Quick test
    result = run_extraction("Airbnb", "Brian Chesky")
    print("\n=== RESULTS ===")
    for email in result["final_emails"]:
        print(f"  [{email['confidence'].upper()}] {email['email']} — source: {email['source']}")
    print("\n=== LOGS ===")
    for msg in result["messages"]:
        print(f"  {msg}")