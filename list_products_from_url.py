import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from urllib.parse import urlparse, parse_qs, urlencode

def get_product_codes(base_url, extra_params):
    """
    Fetch product codes from paginated URLs.
    Returns a set of raw product codes in their original dashed format (####-###).
    """
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/91.0.4472.124 Safari/537.36')
    }
    
    all_product_codes = set()
    page = 1
    delay = 10  # Initial delay for rate-limiting handling

    while True:
        url = f"{base_url}?page={page}"
        if extra_params:
            url += f"&{extra_params}"

        try:
            response = requests.get(url, headers=headers, timeout=10)
        except requests.RequestException as e:
            print(f"Error during request: {e}")
            break

        if response.status_code == 429:
            print("Too many requests. Waiting longer before retrying...")
            time.sleep(delay)
            delay = min(delay * 2, 300)
            continue

        if response.status_code == 404:
            print(f"No more pages found. Stopping at page {page}.")
            break

        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        product_links = soup.select("[class^='Hit_hitImageLink']")
        
        page_codes_found = False
        for link in product_links:
            href = link.get('href')
            if href:
                match = re.search(r'\b\d{4}-\d{3}\b', href)
                if match:
                    all_product_codes.add(match.group(0))
                    page_codes_found = True

        if not page_codes_found:
            print(f"No product codes found on page {page}. Stopping.")
            break

        page += 1
        delay = 10

    return all_product_codes

def main():
    full_url = input("Enter full URL (including any query parameters): ").strip()
    if not full_url:
        print("Please enter a valid URL.")
        sys.exit(1)

    parsed = urlparse(full_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    # Remove 'page' parameter if present, since pagination is handled in code
    query_dict = parse_qs(parsed.query)
    query_dict.pop('page', None)
    extra_params = urlencode(query_dict, doseq=True)

    preserve_dashes = input("Preserve dashes in codes? (y/n): ").strip().lower() == 'y'
    comma_separated = input("Display as comma separated? (y/n): ").strip().lower() == 'y'

    raw_codes = get_product_codes(base_url, extra_params)
    codes_list = sorted(raw_codes)

    if not preserve_dashes:
        codes_list = [code.replace("-", "") for code in codes_list]

    if comma_separated:
        result_str = ", ".join(codes_list)
    else:
        result_str = "\n".join(codes_list)

    print("\nProduct Codes:\n")
    print(result_str)

    save_csv = input("\nSave results as CSV? (y/n): ").strip().lower() == 'y'
    if save_csv:
        file_path = input("Enter CSV file path (e.g., codes.csv): ").strip()
        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Product Code"])
                for code in codes_list:
                    writer.writerow([code])
            print(f"CSV saved successfully to {file_path}")
        except Exception as e:
            print(f"Error saving CSV: {e}")

if __name__ == "__main__":
    main()