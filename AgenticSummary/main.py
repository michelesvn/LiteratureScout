from openai import AzureOpenAI
from AgenticSummary.agentic_summarization import Agentic_Summarization
from AgenticSummary.agentic_aggregation import Agentic_Aggregation
from AgenticSummary.config import (API_KEY, AZURE_ENDPOINT, DEPLOYMENT_NAME, API_VERSION, INPUT_PATH, OUTPUT_PATH,
                                   PDF_DPI, IMAGE_QUALITY, MAX_TOKENS, TEMPERATURE, TOP_P, FREQUENCY_PENALTY,
                                   PRESENCE_PENALTY, MAX_PDFS_PER_FILE)


def main():
    # Initialize the Azure OpenAI client with API credentials and configuration settings
    client = AzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        azure_deployment=DEPLOYMENT_NAME,
        api_key=API_KEY,
        api_version=API_VERSION
    )

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

    # Initialize the summarization module
    agentic_summarization = Agentic_Summarization(INPUT_PATH, OUTPUT_PATH, DEPLOYMENT_NAME, client, PDF_DPI,
                                                  IMAGE_QUALITY, MAX_TOKENS, TEMPERATURE, TOP_P, FREQUENCY_PENALTY,
                                                  PRESENCE_PENALTY)

    print("\nStarting PDF processing and summarization...")

    # Process PDFs by year, generating individual summaries
    agentic_summarization.process_pdfs_by_year(selected_years)
    print("\nPDF summarization completed.")

    # Initialize the aggregation module
    agentic_aggregation = Agentic_Aggregation(OUTPUT_PATH, DEPLOYMENT_NAME, client, MAX_TOKENS, TEMPERATURE, TOP_P,
                                              FREQUENCY_PENALTY, PRESENCE_PENALTY, MAX_PDFS_PER_FILE)

    print("\nAggregating summaries into a final document...")

    # Generate a comprehensive summary from the individual summaries
    agentic_aggregation.summarize_summaries()
    print("\nSummary aggregation completed.")


if __name__ == "__main__":
    main()
