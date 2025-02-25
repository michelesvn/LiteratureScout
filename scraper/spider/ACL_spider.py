import os
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .base_spider import BaseSpider
from .utils import download_paper


class ACL_spider(BaseSpider):
    def scrape_papers(self, link, selected_years, keywords):
        max_retries = 3
        retry_delay = 30

        try:
            self.driver.get(link)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='events/']"))
            )

            # Get year links
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='events/']")
            year_url_mapping = {}
            for l in links:
                year_url = l.get_attribute("href")
                year_match = re.search(r"\b\d{4}\b", year_url)
                if year_match:
                    year = year_match.group()
                    year_url_mapping[year_url] = year

            print("\nYear --> URL mapping:")
            for year_url, year in year_url_mapping.items():
                print(f"{year} -> {year_url}")

            for year_url, year in year_url_mapping.items():
                yr = int(year)
                if yr not in selected_years:
                    print(f"Year {year} not selected. Skipping.")
                    continue

                print(f"\nYear {year} selected!")
                for attempt_year in range(1, max_retries + 1):
                    try:
                        self.driver.get(year_url)
                        WebDriverWait(self.driver, 15).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '.pdf') and @data-original-title='Open PDF']"))
                        )

                        pdf_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf') and @data-original-title='Open PDF']")
                        print(f"Found {len(pdf_links)} PDFs for year {year}.")

                        for pdf_link in pdf_links:
                            for attempt_pdf in range(1, max_retries + 1):
                                try:
                                    pdf_url = pdf_link.get_attribute("href")
                                    # Derive title link
                                    new_url = pdf_url.replace('.pdf', '')
                                    relative_new_url = "/" + new_url.split("/")[-1] + "/"
                                    title_element = WebDriverWait(self.driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.XPATH, f"//a[contains(@href, '{relative_new_url}')]")
                                        )
                                    )
                                    pdf_title = title_element.text.strip()

                                    print(f"Processing PDF: {pdf_title} (Year: {year})")
                                    download_paper(pdf_url, pdf_title, os.path.join(self.output_path, year),
                                                   self.driver, keywords)
                                    break
                                except Exception as e:
                                    print(f"Error scraping PDF attempt {attempt_pdf}: {e}")
                                    if attempt_pdf < max_retries:
                                        time.sleep(retry_delay)
                                    else:
                                        print("PDF scraping failed after all attempts.")
                        break

                    except Exception as e:
                        print(f"Error scraping year {year}, attempt {attempt_year}: {e}")
                        if attempt_year < max_retries:
                            time.sleep(retry_delay)
                        else:
                            print(f"Year {year} scraping failed after all attempts.")

        except Exception as e:
            print(f"Error scraping ACL: {e}")
