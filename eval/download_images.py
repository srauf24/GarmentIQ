"""Download test images from Pexels for evaluation.

Pexels images are free to use (Pexels license, no attribution required).
IDs sourced from Pexels search results for each garment type.
"""

import csv
import sys
import time
import urllib.request
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
IMAGE_DIR = EVAL_DIR / "test_images"
GROUND_TRUTH_PATH = EVAL_DIR / "ground_truth.csv"

# (pexels_id, filename, garment_type, style, material, occasion, location_country)
# Ground truth labels will be refined after visual inspection.
IMAGES = [
    # --- Dresses (6) ---
    (5254750, "dress_silk_01.jpeg", "Dress", "Formal", "Silk", "Evening/Formal", ""),
    (12588048, "dress_red_01.jpeg", "Dress", "Formal", "Synthetic", "Evening/Formal", ""),
    (30736113, "dress_white_01.jpeg", "Dress", "Minimalist", "Cotton", "Casual Daily", ""),
    (7166022, "dress_beige_01.jpeg", "Dress", "Casual", "Silk", "Casual Daily", ""),
    (9512043, "dress_floral_01.jpeg", "Dress", "Bohemian", "Synthetic", "Evening/Formal", ""),
    (1391499, "dress_white_02.jpeg", "Dress", "Minimalist", "Cotton", "Casual Daily", ""),

    # --- Jackets (6) ---
    (1824561, "jacket_leather_01.jpeg", "Jacket", "Streetwear", "Leather", "Casual Daily", ""),
    (2747600, "jacket_leather_02.jpeg", "Jacket", "Streetwear", "Leather", "Casual Daily", ""),
    (11555859, "jacket_leather_03.jpeg", "Jacket", "Streetwear", "Leather", "Casual Daily", ""),
    (10274665, "jacket_brown_01.jpeg", "Jacket", "Casual", "Leather", "Casual Daily", ""),
    (1687116, "jacket_leather_04.jpeg", "Jacket", "Casual", "Leather", "Casual Daily", ""),
    (977796, "jacket_leather_05.jpeg", "Jacket", "Streetwear", "Leather", "Casual Daily", ""),

    # --- Suits (6) ---
    (1093926, "suit_blue_01.jpeg", "Suit", "Formal", "Wool", "Business", ""),
    (31972610, "suit_formal_01.jpeg", "Suit", "Formal", "Wool", "Business", ""),
    (4173354, "suit_business_01.jpeg", "Suit", "Formal", "Wool", "Business", ""),
    (653429, "suit_black_01.jpeg", "Suit", "Formal", "Wool", "Evening/Formal", ""),
    (6918507, "suit_meeting_01.jpeg", "Suit", "Formal", "Wool", "Business", ""),
    (3823494, "suit_senior_01.jpeg", "Suit", "Formal", "Wool", "Business", ""),

    # --- Tops (6) ---
    (19317154, "top_blouse_01.jpeg", "Top", "Casual", "Synthetic", "Casual Daily", ""),
    (19191808, "top_blouse_02.jpeg", "Top", "Formal", "Silk", "Business", ""),
    (1980103, "top_floral_01.jpeg", "Top", "Bohemian", "Cotton", "Casual Daily", ""),
    (17360584, "top_casual_01.jpeg", "Top", "Casual", "Cotton", "Casual Daily", ""),
    (9594676, "top_rack_01.jpeg", "Top", "Casual", "Cotton", "Casual Daily", ""),
    (8387830, "top_store_01.jpeg", "Top", "Casual", "Cotton", "Casual Daily", ""),

    # --- Skirts (5) ---
    (16745832, "skirt_mini_01.jpeg", "Skirt", "Casual", "Cotton", "Casual Daily", ""),
    (22601751, "skirt_black_01.jpeg", "Skirt", "Formal", "Synthetic", "Business", ""),
    (15647611, "skirt_green_01.jpeg", "Skirt", "Casual", "Cotton", "Casual Daily", ""),
    (20356179, "skirt_white_01.jpeg", "Skirt", "Minimalist", "Cotton", "Casual Daily", ""),
    (1007018, "skirt_blue_01.jpeg", "Skirt", "Casual", "Cotton", "Casual Daily", ""),

    # --- Coats (5) ---
    (14495270, "coat_portrait_01.jpeg", "Coat", "Classic", "Wool", "Casual Daily", ""),
    (30773116, "coat_winter_01.jpeg", "Coat", "Classic", "Wool", "Casual Daily", ""),
    (10955935, "coat_winter_02.jpeg", "Coat", "Casual", "Synthetic", "Casual Daily", ""),
    (3398192, "coat_black_01.jpeg", "Coat", "Formal", "Wool", "Business", ""),
    (6712145, "coat_white_01.jpeg", "Coat", "Casual", "Synthetic", "Casual Daily", ""),

    # --- Knitwear (5) ---
    (5475173, "knitwear_sweaters_01.jpeg", "Knitwear", "Casual", "Knit", "Casual Daily", ""),
    (3262937, "knitwear_closeup_01.jpeg", "Knitwear", "Casual", "Knit", "Casual Daily", ""),
    (4324402, "knitwear_woman_01.jpeg", "Knitwear", "Casual", "Knit", "Casual Daily", ""),
    (5493784, "knitwear_women_01.jpeg", "Knitwear", "Casual", "Knit", "Casual Daily", ""),
    (7237040, "knitwear_man_01.jpeg", "Knitwear", "Casual", "Knit", "Casual Daily", ""),

    # --- Trousers (6) ---
    (885580, "trousers_casual_01.jpeg", "Trousers", "Casual", "Cotton", "Casual Daily", ""),
    (14408067, "trousers_wide_01.jpeg", "Trousers", "Bohemian", "Cotton", "Casual Daily", ""),
    (17350031, "trousers_patterned_01.jpeg", "Trousers", "Streetwear", "Synthetic", "Casual Daily", ""),
    (18359102, "trousers_white_01.jpeg", "Trousers", "Casual", "Cotton", "Casual Daily", ""),
    (16751012, "trousers_cargo_01.jpeg", "Trousers", "Streetwear", "Cotton", "Casual Daily", ""),
    (18866333, "trousers_leather_01.jpeg", "Trousers", "Streetwear", "Leather", "Casual Daily", ""),

    # --- Accessories (5) ---
    (1152077, "accessories_bag_01.jpeg", "Accessories", "Classic", "Leather", "Casual Daily", ""),
    (167703, "accessories_bag_02.jpeg", "Accessories", "Classic", "Leather", "Casual Daily", ""),
    (2986445, "accessories_various_01.jpeg", "Accessories", "Classic", "Leather", "Casual Daily", ""),
    (1936848, "accessories_tote_01.jpeg", "Accessories", "Casual", "Leather", "Casual Daily", ""),
    (1204464, "accessories_bag_03.jpeg", "Accessories", "Formal", "Leather", "Business", ""),
]


def download_image(pexels_id: int, filename: str) -> bool:
    """Download a single image from Pexels. Returns True on success."""
    url = f"https://images.pexels.com/photos/{pexels_id}/pexels-photo-{pexels_id}.jpeg?auto=compress&cs=tinysrgb&w=800"
    dest = IMAGE_DIR / filename
    if dest.exists():
        return True

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if len(data) < 1000:  # Too small, likely an error page
                print(f"    FAILED: response too small ({len(data)} bytes)")
                return False
            dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"    FAILED: {e}")
        return False


def write_ground_truth(entries: list[tuple]) -> None:
    """Write ground_truth.csv from the successful downloads."""
    with open(GROUND_TRUTH_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "garment_type", "style", "material", "occasion", "location_country"])
        for entry in entries:
            writer.writerow(entry[1:])


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {len(IMAGES)} images to {IMAGE_DIR}...")
    successful = []
    failed = []

    for i, entry in enumerate(IMAGES, 1):
        pexels_id, filename = entry[0], entry[1]
        print(f"  [{i}/{len(IMAGES)}] {filename}...", end=" ", flush=True)

        if download_image(pexels_id, filename):
            print("OK")
            successful.append(entry)
        else:
            failed.append(entry)

        time.sleep(0.3)

    print(f"\nDownloaded: {len(successful)}/{len(IMAGES)}")

    if failed:
        print(f"Failed ({len(failed)}):")
        for entry in failed:
            print(f"  - {entry[1]} (pexels id: {entry[0]})")

    write_ground_truth(successful)
    print(f"Ground truth written: {GROUND_TRUTH_PATH} ({len(successful)} entries)")


if __name__ == "__main__":
    main()
