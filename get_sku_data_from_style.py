import requests
import json
import pandas as pd
from bs4 import BeautifulSoup

def fetch_inventory(style_number: str) -> pd.DataFrame:
    """
    Fetches SKU and inventory data for a given MEC style number.
    Returns a DataFrame with columns: style_number, sku, size, colour, qty_available, price, promoBadge.
    """
    # 1. Build the public product URL
    clean = style_number.replace('-', '')
    url = f"https://www.mec.ca/en/product/{clean[:4]}-{clean[4:]}"
    
    # 2. Download the HTML with a mock header
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    html = resp.text

    # 3. Pull out the __NEXT_DATA__ <script>
    soup = BeautifulSoup(html, "html.parser")
    data_tag = soup.find("script", id="__NEXT_DATA__")
    if data_tag is None:
        raise ValueError("Could not find __NEXT_DATA__ script tag in the page. The page structure may have changed or the product does not exist.")
    data = json.loads(data_tag.string)

    # 4. Walk the JSON tree safely
    try:
        product = data["props"]["pageProps"]["product"]
        variants = product.get("variants", [])
        sizes = {s["id"]: s["name"] for s in product.get("sizes", [])}
        colours = {c["id"]: c["name"] for c in product.get("allColours", [])}
    except (KeyError, TypeError):
        raise ValueError("Could not find expected product structure in JSON.")

    rows = []
    for v in variants:
        sku = v.get("sku")
        size = sizes.get(v.get("sizeId"), "")
        colour = colours.get(v.get("colourId"), "")
        qty = v.get("inventoryAggregated", {}).get("availableToSell", None)
        price = v.get("price", {}).get("price", {}).get("value", None)
        promo = v.get("promoBadge", {}).get("code") if v.get("promoBadge") else None

        rows.append({
            "style_number": style_number,
            "sku": sku,
            "size": size,
            "colour": colour,
            "qty_available": qty,
            "price": price,
            "promoBadge": promo
        })

    return pd.DataFrame(rows)

# ---- example run ----
if __name__ == "__main__":
    style_number = input("Enter MEC style number (e.g. 5060364): ").strip()
    df = fetch_inventory(style_number)
    print(df)
