import time
import re
import os
from fuzzywuzzy import fuzz
from .base_spider import BaseSpider
from .utils import download_paper, load_credentials
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException


class ICML_spider(BaseSpider):
    def safe_click(self, by, locator, timeout=10, retries=10):
        """
        Safely click an element identified by (by, locator).
        Retries if a stale element error occurs.
        """
        for attempt in range(retries):
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, locator))
                )
                self.click_element(element)
                return True
            except StaleElementReferenceException:
                print(f"Stale element on safe_click attempt {attempt + 1}, retrying...")
                time.sleep(1)
        return False

    def safe_find(self, by, locator, timeout=10, retries=3):
        """
        Safely find an element identified by (by, locator).
        Retries on stale element reference.
        """
        for attempt in range(retries):
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, locator))
                )
                return element
            except StaleElementReferenceException:
                print(f"Stale element on safe_find attempt {attempt + 1}, retrying...")
                time.sleep(1)
        return None

    def login(self, link):
        max_retries = 5
        retry_delay = 30
        username, password, institution = load_credentials()

        if not username or not password:
            print("No ACM credentials provided. Proceeding without login.")
            self.driver.get(link)
            return

        for attempt_login in range(1, max_retries + 1):
            try:
                self.driver.get("https://dl.acm.org/action/showLogin")
                # Let the page load
                time.sleep(3)

                if not self.safe_click(By.XPATH, "//a[@data-simple-tab-id='institutional-login']", timeout=10):
                    raise TimeoutException("Institutional login button not clickable.")

                time.sleep(2)
                if not self.safe_click(By.XPATH, "//i[@class='icon-arrow_d_n']", timeout=10):
                    raise TimeoutException("Dropdown arrow not clickable.")

                time.sleep(2)
                search_input = self.safe_find(By.XPATH, "//input[@placeholder='Search Institution name']", timeout=10)
                if not search_input:
                    raise TimeoutException("Search input not found.")
                search_input.clear()
                search_input.send_keys(institution)

                institution_option = self.safe_find(By.XPATH, f"//span[text()='{institution}']", timeout=10)
                if not institution_option:
                    raise TimeoutException("Institution option not found.")
                self.click_element(institution_option)

                time.sleep(2)
                username_field = self.safe_find(By.ID, "username", timeout=10)
                password_field = self.safe_find(By.ID, "password", timeout=10)
                if not username_field or not password_field:
                    raise TimeoutException("Username or password field not found.")

                username_field.send_keys(username)
                password_field.send_keys(password)
                password_field.send_keys(Keys.RETURN)

                # Wait for institution name
                institution_elem = self.safe_find(By.CLASS_NAME, "institution__name", timeout=15)
                if not institution_elem:
                    raise TimeoutException("Institution name element not found after login.")

                time.sleep(5)
                institution_name = institution_elem.text
                similarity = fuzz.ratio(institution.lower(), institution_name.lower())
                if similarity >= 70:
                    self.driver.get(link)
                    print("Login successful!")
                    break

            except Exception as e:
                print(f"Login attempt {attempt_login} failed: {e}")
                if attempt_login < max_retries:
                    time.sleep(retry_delay)
                else:
                    print("Unable to login after all attempts.")
                    self.driver.get(link)
                    break

    def scrape_papers(self, link, selected_years, keywords):
        max_retries = 5
        retry_delay = 30

        try:
            self.login(link)
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
                    if yr <= 2002:
                        print(f"Year {yr} has no PDFs. Skipping.")
                        break
                    try:
                        self.driver.get(year_url)
                        WebDriverWait(self.driver, 20).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH,
                                 "//div[@class='head']/a["
                                 "contains(@href, 'openreview.net/forum') or "
                                 "((starts-with(@href, 'http://proceedings.mlr.press/') or starts-with(@href, 'https://proceedings.mlr.press/')) and "
                                 "contains(@href, '.html') and not(contains(@href, 'twitter.com'))) or "
                                 "(starts-with(@href, 'https://ceur-ws.org/') and not(contains(@href, 'twitter.com'))) or "
                                 "(starts-with(@href, 'https://doi.org/') and not(contains(@href, 'twitter.com'))) or "
                                 "((starts-with(@href, 'http://www.aaai.org/') or starts-with(@href, 'https://www.aaai.org/')) and not(contains(@href, 'twitter.com'))) or "
                                 "((starts-with(@href, 'http://icml.cc/') or starts-with(@href, 'https://icml.cc/')) and "
                                 "contains(@href, '.pdf') and not(contains(@href, 'twitter.com')))"
                                 "]"
                                 )
                            )
                        )

                        pdf_pages = self.driver.find_elements(By.XPATH,
                                                              "//div[@class='head']/a["
                                                              "contains(@href, 'openreview.net/forum') or "
                                                              "((starts-with(@href, 'http://proceedings.mlr.press/') or starts-with(@href, 'https://proceedings.mlr.press/')) and "
                                                              "contains(@href, '.html') and not(contains(@href, 'twitter.com'))) or "
                                                              "(starts-with(@href, 'https://ceur-ws.org/') and not(contains(@href, 'twitter.com'))) or "
                                                              "(starts-with(@href, 'https://doi.org/') and not(contains(@href, 'twitter.com'))) or "
                                                              "((starts-with(@href, 'http://www.aaai.org/') or starts-with(@href, 'https://www.aaai.org/')) and not(contains(@href, 'twitter.com'))) or "
                                                              "((starts-with(@href, 'http://icml.cc/') or starts-with(@href, 'https://icml.cc/')) and "
                                                              "contains(@href, '.pdf') and not(contains(@href, 'twitter.com')))"
                                                              "]"
                                                              )
                        pdf_pages_links = [pdf_page.get_attribute("href") for pdf_page in pdf_pages]
                        print(f"Found {len(pdf_pages_links)} PDFs for year {yr}.")

                        counter = 0
                        for pdf_page_link in pdf_pages_links:
                            counter += 1
                            for attempt_pdf in range(1, max_retries + 1):
                                try:
                                    if 'openreview.net/forum' in pdf_page_link:
                                        self.driver.get(pdf_page_link)
                                        WebDriverWait(self.driver, 20).until(
                                            EC.presence_of_all_elements_located(
                                                (By.XPATH,
                                                 "//h2[@class='note_content_title']/span | //h2[@class='citation_title']")
                                            )
                                        )

                                        title_element = self.driver.find_element(By.XPATH,
                                                                                 "//h2[@class='note_content_title']/span | //h2[@class='citation_title']")
                                        pdf_title = title_element.text.strip()
                                        pdf_element = self.driver.find_element(By.XPATH,
                                                                               "//a[@class='note_content_pdf'] | //a[@class='citation_pdf_url']")
                                        pdf_url = pdf_element.get_attribute("href")
                                    elif 'proceedings.mlr.press' in pdf_page_link:
                                        self.driver.get(pdf_page_link)
                                        WebDriverWait(self.driver, 20).until(
                                            EC.presence_of_all_elements_located(
                                                (By.XPATH, "//h1")
                                            )
                                        )

                                        title_element = self.driver.find_element(By.XPATH, "//h1")
                                        pdf_title = title_element.text.strip()
                                        pdf_element = self.driver.find_element(By.XPATH, "//a[contains(@href, '.pdf')]")
                                        pdf_url = pdf_element.get_attribute("href")
                                    elif 'doi.org' in pdf_page_link:
                                        if counter == 1:
                                            continue
                                        self.driver.get(pdf_page_link)
                                        current_url = self.driver.current_url
                                        if 'book' in current_url:
                                            break
                                        try:
                                            login_text_element = WebDriverWait(self.driver, 5).until(
                                                EC.presence_of_element_located(
                                                    (By.XPATH, "//*[contains(text(), 'Log in via an institution')]"))
                                            )
                                            if login_text_element:
                                                continue
                                        except TimeoutException:
                                            pass

                                        pdf_element = WebDriverWait(self.driver, 20).until(
                                            EC.presence_of_element_located((By.XPATH,
                                                                            "//a[contains(@href, '/doi/pdf/') or contains(@href, '.pdf')]"))
                                        )
                                        pdf_url = pdf_element.get_attribute("href")
                                        title_element = WebDriverWait(self.driver, 20).until(
                                            EC.presence_of_element_located((By.XPATH,
                                                                            "//h1[@property='name' or (@class='c-article-title' and @data-test='chapter-title')]"))
                                        )
                                        pdf_title = title_element.text.strip()
                                    elif 'aaai.org' in pdf_page_link:
                                        self.driver.get(pdf_page_link)
                                        WebDriverWait(self.driver, 20).until(
                                            EC.presence_of_all_elements_located(
                                                (By.XPATH, "//h1")
                                            )
                                        )

                                        title_element = self.driver.find_element(By.XPATH, "//h1")
                                        pdf_title = title_element.text.strip()
                                        pdf_element = self.driver.find_element(By.XPATH, "//a[contains(@href, '.pdf')]")
                                        pdf_url = pdf_element.get_attribute("href")
                                    elif 'icml.cc' in pdf_page_link:
                                        entries = self.driver.find_elements(By.XPATH,
                                                                            "//li[@class='entry inproceedings']")
                                        pdf_title = None
                                        for entry in entries:
                                            try:
                                                pdf_element = entry.find_element(By.XPATH, ".//a[@itemprop='url']")
                                                if pdf_element.get_attribute("href") == pdf_page_link:
                                                    title_element = entry.find_element(By.XPATH,
                                                                                       ".//span[@class='title']")
                                                    pdf_title = title_element.text.strip()
                                                    break
                                            except Exception as e:
                                                print(f"Error processing entry: {e}")

                                        if pdf_title:
                                            pdf_url = pdf_page_link
                                        else:
                                            print(f"Title not found for PDF link: {pdf_page_link}")
                                    elif 'ceur-ws' in pdf_page_link:
                                        if counter == 1:
                                            continue
                                        entries = self.driver.find_elements(By.XPATH,
                                                                            "//li[@class='entry inproceedings']")
                                        pdf_title = None
                                        for entry in entries:
                                            try:
                                                pdf_element = entry.find_element(By.XPATH, ".//a[@itemprop='url']")
                                                if pdf_element.get_attribute("href") == pdf_page_link:
                                                    title_element = entry.find_element(By.XPATH,
                                                                                       ".//span[@class='title']")
                                                    pdf_title = title_element.text.strip()
                                                    break
                                            except Exception as e:
                                                print(f"Error processing entry: {e}")

                                        if pdf_title:
                                            pdf_url = pdf_page_link
                                        else:
                                            print(f"Title not found for PDF link: {pdf_page_link}")
                                    else:
                                        continue
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
            print(f"Error scraping ICML: {e}")
