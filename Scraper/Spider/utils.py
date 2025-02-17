import os
import re
import shutil
import requests
import time
import json


def keyword_match(title, keywords, min_groups=2):
    """
    Check if the title matches at least `min_groups` groups of keywords.
    Each group in `keywords` is a list of possible keyword matches.
    If at least one keyword in a group is found in the title, that group is considered matched.
    This function returns True if at least `min_groups` groups are matched.
    """
    title_lower = title.lower()
    match_count = 0

    for group in keywords:
        # If at least one keyword in this group is found in the title
        if any(option.lower() in title_lower for option in group):
            match_count += 1

    return match_count >= min_groups


def download_paper(pdf_url, pdf_title, save_dir, driver, keywords, max_retries=3, retry_delay=30):
    """
    Download a PDF with retry logic and keyword checks.
    """
    for attempt in range(1, max_retries + 1):
        try:
            os.makedirs(save_dir, exist_ok=True)
            # Clean title
            title = re.sub(r'[^a-zA-Z0-9\s\-_.,]', '', pdf_title.strip())
            title = ' '.join(title.split())

            # Check keywords
            if keywords is not None and not keyword_match(title, keywords):
                print(f"Skipping PDF '{title}': does not match keywords.")
                return False

            file_path = os.path.join(save_dir, f"{title}.pdf")
            if os.path.exists(file_path):
                print(f"PDF '{title}' already downloaded.")
                return True

            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            if not pdf_url.endswith('.pdf'):
                # Download through browser
                temp_dir = os.path.join(save_dir, "temp_download")
                os.makedirs(temp_dir, exist_ok=True)
                driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": temp_dir})
                driver.get(pdf_url)
                time.sleep(10)

                downloaded_file = next((f for f in os.listdir(temp_dir) if f.endswith('.pdf')), None)
                if downloaded_file:
                    shutil.move(os.path.join(temp_dir, downloaded_file), file_path)
                shutil.rmtree(temp_dir)
            else:
                # Direct PDF URL
                pdf_response = requests.get(pdf_url, cookies=cookies, stream=True)
                pdf_response.raise_for_status()
                with open(file_path, "wb") as file:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        file.write(chunk)

            print(f"PDF '{title}' saved successfully!")
            return True

        except Exception as e:
            print(f"Error downloading PDF (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                print("Max attempts reached. Could not download PDF.")
                return False


def load_credentials(file_path="Spider/credentials.json"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Credentials file '{file_path}' not found.")

    with open(file_path, "r") as f:
        creds = json.load(f)

    # Extract username and password from the JSON
    username = creds.get("ACM_USERNAME", "")
    password = creds.get("ACM_PASSWORD", "")
    institution = creds.get("INSTITUTION", "")
    return username, password, institution
