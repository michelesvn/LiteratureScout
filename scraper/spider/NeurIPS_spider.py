import os
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .base_spider import BaseSpider
from .utils import download_paper


class NeurIPS_spider(BaseSpider):
    def scrape_papers(self, link, selected_years, keywords):
        max_retries = 5
        retry_delay = 30

        try:
            self.driver.get(link)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/paper_files/paper/')]"))
            )

            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/paper_files/paper/')]")
            year_url_mapping = {}
            for l in links:
                url = l.get_attribute("href")
                year_match = re.search(r'/paper/(\d{4})', url)
                if year_match:
                    year = int(year_match.group(1))
                    year_url_mapping[url] = year

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
                        WebDriverWait(self.driver, 20).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, "//a[contains(@href, '/paper_files/paper/') and (contains(@href, '-Abstract-Conference.html') or contains(@href, '-Abstract.html'))]")
                            )
                        )

                        detail_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/paper_files/paper/') and (contains(@href, '-Abstract-Conference.html') or contains(@href, '-Abstract.html'))]")
                        print(f"Found {len(detail_links)} PDFs for year {yr}.")

                        pdf_url_title_mapping = {}
                        for dl in detail_links:
                            pdf_url = dl.get_attribute("href")
                            pdf_title = dl.text.strip()
                            pdf_url_title_mapping[pdf_url] = pdf_title

                        for pdf_page_url, pdf_title in pdf_url_title_mapping.items():
                            for attempt_pdf in range(1, max_retries + 1):
                                try:
                                    self.driver.get(pdf_page_url)
                                    pdf_link_element = WebDriverWait(self.driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.XPATH, "//a[(contains(@class, 'btn btn-primary btn-spacer') or contains(@class, 'btn btn-light btn-spacer'))"
                                                       " and (contains(@href, '-Paper-Conference.pdf') or contains(@href, '-Paper.pdf'))]")
                                        )
                                    )

                                    final_pdf_url = pdf_link_element.get_attribute("href")
                                    print(f"Processing PDF: {pdf_title} (Year: {yr})")
                                    download_paper(final_pdf_url, pdf_title, os.path.join(self.output_path, str(yr)),
                                                   self.driver, keywords)
                                    break
                                except Exception as e:
                                    print(f"Error scraping PDF {pdf_title}, attempt {attempt_pdf}: {e}")
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
            print(f"Error scraping NeurIPS: {e}")
