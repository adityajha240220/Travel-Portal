from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def parse_summary(html, base_url=None, destination=None, budget=None):
    """
    Parses raw HTML to extract a readable summary + relevant categorized links.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tags
    for tag in soup(["script", "style", "noscript", "footer", "header", "form", "nav", "aside"]):
        tag.decompose()

    # Try to get main content
    main = soup.find("main") or soup.find("article") or soup.body

    # Get clean text
    text = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{2,}", "\n", text)  # Collapse multiple newlines
    text = re.sub(r"\s{2,}", " ", text)   # Collapse extra spaces
    summary = text[:1000] + "..." if len(text) > 1000 else text

    # Extract and categorize links
    categories = {
        "hotels": ["booking.com", "expedia.com", "hotels.com", "agoda.com", "airbnb.com"],
        "flights": ["skyscanner.com", "kayak.com", "expedia.com", "trip.com"],
        "food": ["zomato.com", "tripadvisor.com", "yelp.com", "ubereats.com", "swiggy.com"],
        "general": []
    }

    found_links = {cat: [] for cat in categories}

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base_url, href) if base_url else href
        href_lower = full_url.lower()

        matched = False
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in href_lower:
                    if destination and destination.lower() in href_lower:
                        found_links[cat].append(full_url)
                    elif not destination:  # No filter
                        found_links[cat].append(full_url)
                    matched = True
                    break
            if matched:
                break

        # Store general links if not matched but looks useful
        if not matched and re.search(r"https?://", href_lower):
            found_links["general"].append(full_url)

    # Optional budget filter: only keep links mentioning budget
    if budget:
        budget_str = str(budget)
        for cat in found_links:
            found_links[cat] = [link for link in found_links[cat] if budget_str in link or "cheap" in link.lower()]

    return {
        "summary": summary,
        "links": found_links
    }
