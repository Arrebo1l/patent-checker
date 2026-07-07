import json

# read patent data
with open("data/patents.json", encoding="utf-8") as f:
    patents = json.load(f)

# read company product data
with open("data/company_product_data.json", encoding="utf-8") as f:
    companies = json.load(f)["companies"]

print("专利数:", len(patents))
print("公司数:", len(companies))

print("\n各公司产品数量:")
for c in companies:
    print(c["name"], "→", len(c["products"]), "个产品")

p = patents[0]
print("\n第一条专利:")
print("publication_number:", p["publication_number"])
print("title:", p["title"])
print("assignee:", p["assignee"])

claims = json.loads(p["claims"])
print("\nclaim 条数:", len(claims))
print("第一条 claim 前200字:")
print(claims[0]["text"][:200])
