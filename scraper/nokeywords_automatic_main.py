"""
No-Keywords Automatic scraper:
- Selects all available academic sources without manual input.
- Allows user to specify a range of years for paper retrieval.
- Downloads all available papers without filtering by keywords.
"""

from config import PROCEEDINGS


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

    # Prompt user for years
    all_years = list(range(1950, 2050))
    selected_years = []
    while True:
        year_input = input("\nEnter a year or press Enter to finish / 'all' for all years: ").strip()
        if not year_input:
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

    # Perform scraping
    for url, acr, title, SpiderClass in PROCEEDINGS:
        if acr.lower() in selected_acronyms:
            spider_instance = SpiderClass(headless=True)
            print(f"\n--- Analyzing {acr}: '{title}' ---")
            spider_instance.scrape_papers(url, selected_years, None)
            spider_instance.cleanup()


if __name__ == "__main__":
    main()
