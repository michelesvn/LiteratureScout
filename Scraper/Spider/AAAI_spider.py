from .base_spider import BaseSpider
from .utils import download_paper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time
import os


class AAAI_spider(BaseSpider):
    def scrape_papers(self, link, selected_years, keywords):
        max_retries = 5
        retry_delay = 30

        try:
            self.driver.get(link)
            # Collect pagination if exists
            page_links = [link]
            # Attempt to find a "Next" button
            try:
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[@class='next']"))
                )
                next_url = next_button.get_attribute("href")
                if next_url:
                    page_links.append(next_url)
            except:
                pass

            year_url_mapping = {}
            for page in page_links:
                self.driver.get(page)
                sections = self.wait_for_all_presence(
                    By.XPATH, "//h2/a[@class='title' and contains(@href, '/view/')]/..", timeout=10
                )

                for section in sections:
                    title_link = section.find_element(By.XPATH, "./a[@class='title']")
                    url = title_link.get_attribute("href")
                    title_text = title_link.text.strip()
                    series_div = section.find_element(By.XPATH, "./div[@class='series']")
                    series_text = series_div.text.strip()

                    # Extract year
                    year = None
                    if "AAAI-" in title_text:
                        year_match = re.search(r"AAAI-(\d{2})", title_text)
                        if year_match:
                            y = int(year_match.group(1))
                            year = 2000 + y if y < 50 else 1900 + y
                    else:
                        year_match = re.search(r"\((\d{4})\)", series_text)
                        if year_match:
                            year = int(year_match.group(1))

                    if year:
                        year_url_mapping[url] = year

            print("\nYear --> URL mapping:")
            for y_url, yr in year_url_mapping.items():
                print(f"{yr} -> {y_url}")
                if yr not in selected_years:
                    print(f"Year {yr} not selected. Skipping.")
                    continue

                for attempt_year in range(1, max_retries + 1):
                    try:
                        self.driver.get(y_url)
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, "//a[contains(@class, 'obj_galley_link') and contains(@class, 'pdf')]")
                            )
                        )
                        pdf_links = self.driver.find_elements(By.XPATH,
                            "//a[contains(@class, 'obj_galley_link') and contains(@class, 'pdf')]")
                        print(f"Found {len(pdf_links)} PDFs for year {yr}.")

                        for pdf_link in pdf_links:
                            for attempt_pdf in range(1, max_retries + 1):
                                try:
                                    pdf_url = pdf_link.get_attribute("href")
                                    article_id = pdf_link.get_attribute("aria-labelledby")
                                    title_element = self.driver.find_element(By.XPATH, f"//a[@id='{article_id}']")
                                    pdf_title = title_element.text.strip()

                                    print(f"Checking PDF: {pdf_title} (Year: {yr})")
                                    download_paper(
                                        pdf_url, pdf_title, os.path.join(self.output_path, str(yr)),
                                        self.driver, keywords
                                    )
                                    break
                                except Exception as e:
                                    print(f"Error scraping PDF attempt {attempt_pdf}: {e}")
                                    if attempt_pdf < max_retries:
                                        time.sleep(retry_delay)
                                    else:
                                        print("PDF scraping failed after all attempts.")
                        break
                    except Exception as e:
                        print(f"Error scraping year {yr}, attempt {attempt_year}: {e}")
                        if attempt_year < max_retries:
                            time.sleep(retry_delay)
                        else:
                            print(f"Year {yr} scraping failed after all attempts.")

        except Exception as e:
            print(f"Error scraping AAAI: {e}")
