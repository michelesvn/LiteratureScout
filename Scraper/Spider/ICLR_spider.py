import os
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .base_spider import BaseSpider
from .utils import download_paper


class ICLR_spider(BaseSpider):
    def scrape_papers(self, link, selected_years, keywords):
        max_retries = 5
        retry_delay = 30

        try:
            self.driver.get(link)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//a[contains(@class, 'toc-link') and contains(@href, 'dblp.org')]"))
            )

            links = self.driver.find_elements(By.XPATH,
                                              "//a[contains(@class, 'toc-link') and contains(@href, 'dblp.org')]")
            year_url_mapping = {}
            for l in links:
                url = l.get_attribute("href")
                year_match = re.search(r'(\d{4})', url)
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
                                (By.XPATH, "//div[@class='head']/a[contains(@href, 'openreview.net/forum') or contains(@href, 'arxiv.org/abs')]")
                            )
                        )

                        pdf_pages = self.driver.find_elements(By.XPATH, "//div[@class='head']/a[contains(@href, 'openreview.net/forum') or contains(@href, 'arxiv.org/abs')]")
                        pdf_pages_links = [pdf_page.get_attribute("href") for pdf_page in pdf_pages]
                        print(f"Found {len(pdf_pages_links)} PDFs for year {yr}.")

                        for pdf_page_link in pdf_pages_links:
                            for attempt_pdf in range(1, max_retries + 1):
                                try:
                                    self.driver.get(pdf_page_link)

                                    if yr > 2016:
                                        WebDriverWait(self.driver, 20).until(
                                            EC.presence_of_all_elements_located(
                                                (By.XPATH, "//h2[@class='note_content_title']/span | //h2[@class='citation_title']")
                                            )
                                        )

                                        title_element = self.driver.find_element(By.XPATH, "//h2[@class='note_content_title']/span | //h2[@class='citation_title']")
                                        pdf_title = title_element.text.strip()
                                        pdf_element = self.driver.find_element(By.XPATH, "//a[@class='note_content_pdf'] | //a[@class='citation_pdf_url']")
                                        pdf_url = pdf_element.get_attribute("href")

                                        print(f"Processing PDF: {pdf_title} (Year: {yr})")
                                        download_paper(pdf_url, pdf_title,
                                                       os.path.join(self.output_path, str(yr)),
                                                       self.driver, keywords)
                                    else:
                                        WebDriverWait(self.driver, 20).until(
                                            EC.presence_of_all_elements_located(
                                                (By.XPATH, "//h1[@class='title mathjax']")
                                            )
                                        )

                                        title_element = self.driver.find_element(By.XPATH,
                                                                                 "//h1[@class='title mathjax']")
                                        pdf_title = title_element.text.replace("Title:", "").strip()
                                        pdf_element = self.driver.find_element(By.XPATH,
                                                                               "//a[@class='abs-button download-pdf']")
                                        pdf_url = pdf_element.get_attribute("href")

                                        print(f"Processing PDF: {pdf_title} (Year: {yr})")
                                        download_paper(pdf_url, pdf_title,
                                                       os.path.join(self.output_path, str(yr)),
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
            print(f"Error scraping ICLR: {e}")
