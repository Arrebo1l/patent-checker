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

# Map common Chinese names and short forms to the names used in the data
COMPANY_ALIASES = {
    "沃尔玛": "Walmart",
    "约翰迪尔": "John Deere",
    "迪尔": "John Deere",
    "富世华": "Husqvarna",
    "科乐收": "CLAAS",
    "克拉斯": "CLAAS",
    "塔吉特": "Target",
    "克罗格": "Kroger",
    "爱科": "AGCO",
    "凯斯纽荷兰": "CNH",
    "凯斯": "CNH",
}

# Normalize a user-typed company name before looking it up
def normalize_company_name(name: str):
    key = name.strip().lower()
    for alias, standard in COMPANY_ALIASES.items():
        if alias.lower() == key:
            return standard
    return name

# Find a company by name using partial match
def get_company(name: str):
    key = normalize_company_name(name).strip().lower()
    for c in COMPANIES:
        if key in c["name"].lower():
            return c
    return None

