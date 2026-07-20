import json
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from claims_analyzer import parse_claims, is_independent, extract_features
from data_loader import get_patent, get_company

load_dotenv()  # read GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

# Get the feature list from a patent's first independent claim 
def get_first_independent_claim_features(patent):
    claims = parse_claims(patent)

    first_independent = None
    for claim in claims:
        if is_independent(claim["text"]):
            first_independent = claim
            break

    if first_independent is None:
        return []

    return extract_features(first_independent["text"])

# Ask the LLM to score how likely one product implements the patent features
def check_product(features, product):
    """让 LLM 评估一个产品实现这些专利特征的可能性,返回打分结果 dict。"""
    prompt = ChatPromptTemplate.from_template(
        "你是专利侵权初筛助手。给定专利的关键技术特征和一个产品的描述,评估该产品实现这些特征的可能性。\n"
        "技术特征: {features}\n"
        "产品名称: {product_name}\n"
        "产品描述: {product_description}\n"
        "评分标准: 80-100 高度吻合(多条特征在描述中有直接对应); 40-79 部分吻合; 0-39 基本无关。\n"
        "只输出 JSON: {{\"score\": 整数, \"matched_features\": [吻合的特征原文], \"reason\": \"不超过80字的理由\"}}"
    )
    chain = prompt | llm

    raw = chain.invoke({
        "features": features,
        "product_name": product["name"],
        "product_description": product["description"],
    }).text

    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)

# Score all products of a company and return the top 2 by score
def rank_products(patent, company):
    """对公司所有产品逐个打分,按分数降序返回 Top 2。"""
    features = get_first_independent_claim_features(patent)

    # skip all LLM calls if no features
    if not features:
        return []

    results = []
    for prod in company["products"]:
        try:
            r = check_product(features, prod)
        except Exception as e:
            print("跳过", prod["name"], e)
            r = {"score": 0, "matched_features": [], "reason": "分析失败"}
        r["product_name"] = prod["name"]
        results.append(r)
        time.sleep(1) 

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:2]

# Run the standard test case: US-RE49889-E1 × Walmart
if __name__ == "__main__":
    patent = get_patent("US-RE49889-E1")
    company = get_company("Walmart")

    top2 = rank_products(patent, company)

    for r in top2:
        print(f"{r['product_name']}: {r['score']} 分 —— {r['reason']}")

    with open("../docs/walmart_匹配结果.json", "w", encoding="utf-8") as f:
        json.dump(top2, f, ensure_ascii=False, indent=2)

    print("完成!已保存到 docs/walmart_匹配结果.json")