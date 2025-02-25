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


class ACM_spider(BaseSpider):
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
                print(f"Stale element on safe_click attempt {attempt+1}, retrying...")
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
                print(f"Stale element on safe_find attempt {attempt+1}, retrying...")
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
        self.login(link)

        try:
            time.sleep(8)
            if not self.safe_click(By.XPATH, "//span[@class='btn' and text()='View All Proceedings']", timeout=15):
                print("Could not click 'View All Proceedings' button.")
                return

            time.sleep(8)
            # Wait for proceedings links
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/doi/proceedings/']"))
            )

            all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/doi/proceedings/']")
            main_keywords = ["WSDM", "WWW", "UMAP", "SIGIR", "CIKM", "KDD", "RecSys"]

            filtered_links = [
                l for l in all_links
                if not l.get_attribute("data-code") and not l.get_attribute("class") and
                   any(keyword in l.text for keyword in main_keywords)
            ]

            year_url_mapping = {}
            for l in filtered_links:
                url = l.get_attribute("href")
                text = l.text
                year_match = re.search(r"'(\d{2})", text)
                if year_match:
                    y = int(year_match.group(1))
                    year = 2000 + y if y < 50 else 1900 + y
                    year_url_mapping[url] = str(year)

            print("\nYear --> URL mapping:")
            for url, year in year_url_mapping.items():
                print(f"{year} -> {url}")

            for year_url, year in year_url_mapping.items():
                yr = int(year)
                if yr not in selected_years:
                    print(f"Year {year} not selected. Skipping.")
                    continue

                print(f"\nYear {year} selected!")
                for attempt_year in range(1, max_retries + 1):
                    try:
                        self.driver.get(year_url)

                        # Expand collapses
                        time.sleep(8)
                        # Repeatedly find elements and click them to reduce staleness
                        paper_collapses = WebDriverWait(self.driver, 30).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "accordion-tabbed__control"))
                        )

                        time.sleep(8)
                        for pc in paper_collapses:
                            try:
                                if pc.get_attribute("aria-expanded") != "true":
                                    self.click_element(pc)
                                    time.sleep(1)
                            except StaleElementReferenceException:
                                # Re-locate and retry if stale
                                paper_collapses = self.driver.find_elements(By.CLASS_NAME, "accordion-tabbed__control")
                                for pc_retry in paper_collapses:
                                    if pc_retry.get_attribute("aria-expanded") != "true":
                                        self.click_element(pc_retry)
                                        time.sleep(1)

                        # Wait for PDF links
                        time.sleep(8)
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/doi/pdf/')]"))
                        )

                        pdf_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/doi/pdf/')]")
                        print(f"Found {len(pdf_links)} PDFs for year {year}.")

                        for pdf_link in pdf_links:
                            for attempt_pdf in range(1, max_retries + 1):
                                try:
                                    pdf_url = pdf_link.get_attribute("href")
                                    doi_url = pdf_url.replace('/pdf', '')
                                    relative_doi_url = "/doi" + doi_url.split("/doi")[-1]

                                    # Re-locate the title element each time
                                    title_element = WebDriverWait(self.driver, 10).until(
                                        EC.presence_of_element_located((By.XPATH, f"//a[contains(@href, '{relative_doi_url}')]"))
                                    )
                                    pdf_title = title_element.text.strip()

                                    print(f"Processing PDF: {pdf_title} (Year: {year})")
                                    download_paper(pdf_url, pdf_title, os.path.join(self.output_path, year),
                                                   self.driver, keywords)
                                    break
                                except (StaleElementReferenceException, TimeoutException) as e:
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
            print(f"Error scraping ACM: {e}")