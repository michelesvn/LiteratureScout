import os
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BaseSpider:
    """
    Base class for all spiders, providing common Selenium setup, teardown,
    and utility methods for waiting, clicking, and extracting elements.
    """

    def __init__(self, output_path="Output", headless=True):
        self.output_path = output_path
        #self.driver_path = chromedriver_autoinstaller.chromedriver_filename
        #self.service = Service(self.driver_path)
        self.driver = self._init_driver(headless=headless)

    def _init_driver(self, headless=True):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
            # Set a larger window size to ensure elements are visible
            options.add_argument("--window-size=1920,1080")
            # Recommended arguments to avoid detection and improve stability
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            # Add a common desktop user agent to avoid headless detection
            options.add_argument(
                "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"
            )

        # Configure download preferences
        options.add_experimental_option("prefs", {
            "download.default_directory": os.path.abspath(self.output_path),
            "plugins.always_open_pdf_externally": True
        })

        #return webdriver.Chrome(service=self.service, options=options)
        return webdriver.Chrome(options=options)

    def wait_for_presence(self, by, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, locator)))

    def wait_for_all_presence(self, by, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_all_elements_located((by, locator)))

    def click_element(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        self.driver.execute_script("arguments[0].click();", element)

    def get_cookies_dict(self):
        return {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

    def cleanup(self):
        self.driver.quit()

    def scrape_papers(self, link, selected_years, keywords):
        """
        Abstract method to be implemented by subclasses.
        This method should navigate to the given link, find years and PDFs, and download those matching keywords.
        """
        raise NotImplementedError("Subclasses must implement this method")
