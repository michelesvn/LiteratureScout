import os
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .base_spider import BaseSpider
from .utils import download_paper


class IJCAI_spider(BaseSpider):
    def scrape_papers(self, link, selected_years, keywords):
        max_retries = 5
        retry_delay = 30

        try:
            self.driver.get(link)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/proceedings')]"))
            )

            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/proceedings')]")
            year_url_mapping = {}
            for l in links:
                year_url = l.get_attribute("href")
                year_match = re.search(r"\b\d{4}\b", year_url)
                if year_match:
                    year = int(year_match.group())
                    year_url_mapping[year_url] = year

            print("\nYear --> URL mapping:")
            for y_url, yr in year_url_mapping.items():
                print(f"{yr} -> {y_url}")

            for year_url, yr in year_url_mapping.items():
                if yr not in selected_years:
                    print(f"Year {yr} not selected. Skipping.")
                    continue

                print(f"\nYear {yr} selected!")
                for attempt_year in range(1, max_retries + 1):
                    try:
                        self.driver.get(year_url)

                        # Different logic depending on year
                        if yr >= 2017:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_all_elements_located((By.CLASS_NAME, "paper_wrapper"))
                            )
                            paper_sections = self.driver.find_elements(By.CLASS_NAME, "paper_wrapper")
                        elif 2015 <= yr <= 2016:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//p[contains(., 'PDF')]"))
                            )
                            paper_sections = self.driver.find_elements(By.XPATH, "//p[contains(., 'PDF')]")
                        else:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '.pdf')]"))
                            )
                            paper_sections = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")

                        print(f"Found {len(paper_sections)} PDFs for year {yr}.")

                        for section in paper_sections:
                            for attempt_pdf in range(1, max_retries + 1):
                                try:
                                    if yr > 2016:
                                        title_element = section.find_element(By.CLASS_NAME, "title")
                                        pdf_title = title_element.text.strip()
                                        pdf_link_element = section.find_element(By.XPATH, ".//a[contains(@href, '.pdf')]")
                                        pdf_url = pdf_link_element.get_attribute("href")
                                    elif 2015 <= yr <= 2016:
                                        pdf_title = section.text.split("/")[0].strip()
                                        pdf_link_element = section.find_element(By.XPATH, ".//a[contains(@href, '.pdf')]")
                                        pdf_url = pdf_link_element.get_attribute("href")
                                    else:
                                        pdf_title = section.text.strip()
                                        pdf_url = section.get_attribute("href")

                                    print(f"Processing PDF: {pdf_title} (Year: {yr})")
                                    download_paper(pdf_url, pdf_title, os.path.join(self.output_path, str(yr)),
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
                        print(f"Error scraping year {yr}, attempt {attempt_year}: {e}")
                        if attempt_year < max_retries:
                            time.sleep(retry_delay)
                        else:
                            print(f"Year {yr} scraping failed after all attempts.")

        except Exception as e:
            print(f"Error scraping IJCAI: {e}")
