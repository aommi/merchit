import pandas as pd
from difflib import SequenceMatcher
from get_sku_data_from_style import fetch_inventory

def closest_color(target, color_list):
    """Find the closest color name from color_list to the target color."""
    def similarity(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return max(color_list, key=lambda c: similarity(target, c))

def find_hero_sku(style_number, hero_color):
    df = fetch_inventory(style_number)
    if df.empty:
        return None

    # Find closest color match
    unique_colors = df['colour'].dropna().unique()
    if not unique_colors.size:
        return None
    best_color = closest_color(hero_color, unique_colors)

    # Filter to rows with the best color
    color_rows = df[df['colour'].str.lower() == best_color.lower()]
    if color_rows.empty:
        return None

    # Find row with highest quantity
    hero_row = color_rows.loc[color_rows['qty_available'].idxmax()]
    return {
        "style_number": hero_row["style_number"],
        "colour": hero_row["colour"],
        "hero_sku": hero_row["sku"],
        "quantity": hero_row["qty_available"]
    }

def main():
    # Toggle: Only print the highest-quantity style if repeated
    deduplicate = False  # Set to False to print all

    # Input: comma-separated style,color pairs
    input_str = input("Enter style,color pairs (e.g. 6017-763,Red; 6027-435,Blue): ").strip()
    pairs = [tuple(map(str.strip, pair.split(','))) for pair in input_str.split(';') if ',' in pair]

    results = []
    for style, color in pairs:
        hero = find_hero_sku(style, color)
        if hero:
            results.append(hero)
        else:
            print(f"No hero SKU found for style {style} and color {color}")

    if deduplicate:
        # Keep only the entry with the highest quantity for each style
        deduped = {}
        for r in results:
            s = r["style_number"]
            if s not in deduped or (r["quantity"] or 0) > (deduped[s]["quantity"] or 0):
                deduped[s] = r
        results = list(deduped.values())

    print("\nStyle\tColor\tHero SKU\tQuantity")
    for r in results:
        print(f"{r['style_number']}\t{r['colour']}\t{r['hero_sku']}\t{r['quantity']}")

if __name__ == "__main__":
    main()