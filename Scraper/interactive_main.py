"""
Interactive Scraper:
- Allows users to manually select academic sources (conferences, journals, etc.).
- Users can specify the years of interest for paper retrieval.
- Supports topic extraction from user input to refine search criteria.
- Uses predefined keywords, augmented with related terms for comprehensive search.
"""

from config import PROCEEDINGS
from keyword_handling import augment_keywords, extract_topics


def main():
    # Display available sources
    print("\nAvailable sources:")
    for _, acr, title, _ in PROCEEDINGS:
        print(f"- {acr}: '{title}'")

    # Prompt user for sources
    norm_proceedings = [(url, acr.strip().lower(), title, spider) for url, acr, title, spider in PROCEEDINGS]
    selected_acronyms = []
    while True:
        user_input = input("\nEnter acronym or press Enter to finish / 'all' for all: ").strip().lower()
        if not user_input:
            print("Selection confirmed!")
            break
        elif user_input == "all":
            selected_acronyms = [acr for _, acr, _, _ in norm_proceedings]
            print("All sources selected!")
            break
        elif user_input in [acr for _, acr, _, _ in norm_proceedings]:
            if user_input not in selected_acronyms:
                selected_acronyms.append(user_input)
                print(f"{user_input.upper()} added!")
            else:
                print(f"{user_input.upper()} already selected.")
        else:
            print(f"{user_input.upper()} not valid. Try again.")

    if not selected_acronyms:
        print("\nNo sources selected. Exiting.")
        return

    selected_acronyms = sorted(selected_acronyms, key=str.lower)
    print("\nSelected sources:", ", ".join(acr.upper() for acr in selected_acronyms))

    # Prompt user for years
    all_years = list(range(1950, 2050))
    selected_years = []
    while True:
        year_input = input("\nEnter a year or press Enter to finish / 'all' for all years: ").strip()
        if not year_input:
            print("Selection confirmed!")
            break
        elif year_input.lower() == "all":
            selected_years = all_years
            print("All years selected!")
            break
        elif year_input.isdigit() and len(year_input) == 4 and int(year_input) in all_years:
            y = int(year_input)
            if y not in selected_years:
                selected_years.append(y)
                print(f"Year {y} added!")
            else:
                print(f"Year {y} already selected.")
        else:
            print(f"Year {year_input} not valid. Try again.")

    if not selected_years:
        print("\nNo years selected. Exiting.")
        return

    selected_years = sorted(selected_years, reverse=True)
    print("\nSelected years:", selected_years)

    user_query = input("\nSpecify the topics you are most interested in: ").strip()
    print(f"User query: {user_query}")

    extracted_topics = extract_topics(user_query)
    print(f"\nExtracted topics: {extracted_topics}")

    selected_keywords = augment_keywords(extracted_topics)
    print(f"\nSelected keywords: {selected_keywords}")

    # Perform scraping
    for url, acr, title, SpiderClass in PROCEEDINGS:
        if acr.lower() in selected_acronyms:
            spider_instance = SpiderClass(headless=False)
            print(f"\n--- Analyzing {acr}: '{title}' ---")
            spider_instance.scrape_papers(url, selected_years, selected_keywords)
            spider_instance.cleanup()


if __name__ == "__main__":
    main()
