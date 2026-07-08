from pathlib import Path
import json

# find data path
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Load both datasets once
with open(DATA_DIR / "patents.json", encoding="utf-8") as f:
    PATENTS = json.load(f)

with open(DATA_DIR / "company_product_data.json", encoding="utf-8") as f:
    COMPANIES = json.load(f)["companies"]

# Find a patent by its publication number
def get_patent(pub_number: str):
    key = pub_number.strip().lower()
    for p in PATENTS:
        if p["publication_number"].lower() == key:
            return p
    return None

# Find a company by name using partial match
def get_company(name: str):
    key = name.strip().lower()
    for c in COMPANIES:
        if key in c["name"].lower():
            return c
    return None

