"""
Automatic Scraper:
- Selects all available academic sources (conferences, journals, etc.).
- Defines a predefined range of years for paper retrieval.
- Uses a fixed set of predefined keywords for filtering relevant research.
- Expands keywords with related terms for improved search accuracy.
"""

from config import PROCEEDINGS, INITIAL_KEYWORDS
from keyword_handling import augment_keywords


def main():
    # Display available sources
    print("\nAvailable sources:")
    for _, acr, title, _ in PROCEEDINGS:
        print(f"- {acr}: '{title}'")

    # Automatically select all sources
    selected_acronyms = [acr.lower() for _, acr, _, _ in PROCEEDINGS]
    selected_acronyms = sorted(selected_acronyms, key=str.lower)
    print("\nAll sources selected!")
    print("Selected sources:", ", ".join(acr.upper() for acr in selected_acronyms))

    # Select years
    selected_years = list(range(1950, 2024 + 1))
    print("\nSelected years:", selected_years)

    # Initial keywords
    print("\nInitial keywords:", INITIAL_KEYWORDS)

    # Select keywords
    selected_keywords = augment_keywords(INITIAL_KEYWORDS)
    print("\nSelected keywords:", selected_keywords)

    # Perform scraping
    for url, acr, title, SpiderClass in PROCEEDINGS:
        if acr.lower() in selected_acronyms:
            spider_instance = SpiderClass(headless=True)
            print(f"\n--- Analyzing {acr}: '{title}' ---")
            spider_instance.scrape_papers(url, selected_years, selected_keywords)
            spider_instance.cleanup()


if __name__ == "__main__":
    main()
