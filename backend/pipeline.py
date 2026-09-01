import uuid
import json
from datetime import date
from errors import AppError
from data_loader import get_patent, get_company
from matcher import rank_products, get_first_independent_claim_features
from claims_analyzer import parse_claims, is_independent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

# risk level
def score_to_level(score):
    if score >= 70:
        return "High"
    if score >= 40:
        return "Moderate"
    return "Low"

# Quick check
assert score_to_level(85) == "High"
assert score_to_level(50) == "Moderate"
assert score_to_level(10) == "Low"

# Run the analysis pipeline
def analyze(patent_id, company_name):
    # 404 if is missing
    patent = get_patent(patent_id)
    if patent is None:
        raise AppError(404, "PATENT_NOT_FOUND", "Patent not found")

    company = get_company(company_name)
    if company is None:
        raise AppError(404, "COMPANY_NOT_FOUND", "Company not found")

    # Find the claim number we are analyzing
    claims = parse_claims(patent)
    claim_num = None
    for claim in claims:
        if is_independent(claim["text"]):
            claim_num = claim["num"]
            break

    # 503 cases
    top2 = rank_products(patent, company)
    if not top2:
        raise AppError(503, "LLM_ERROR", "Analysis failed, please try again later")

    # Required output structure
    top_products = []
    for r in top2:
        top_products.append({
            "product_name": r["product_name"],
            "infringement_likelihood": score_to_level(r["score"]),
            "relevant_claims": [str(claim_num)],
            "matched_features": r["matched_features"],
            "explanation": r["reason"],
        })

    # Overall risk summary
    summary_prompt = ChatPromptTemplate.from_template(
        "你是专利侵权筛选助手。以下是某公司最可能侵权的产品分析结果。\n"
        "请用3句话,给出整体侵权风险的总结。\n"
        "分析结果: {results}"
    )
    summary_chain = summary_prompt | llm
    overall = summary_chain.invoke({"results": json.dumps(top_products, ensure_ascii=False)}).text

    return {
        "analysis_id": uuid.uuid4().hex[:8],
        "analysis_date": date.today().isoformat(),
        "patent_id": patent_id,
        "company_name": company["name"],
        "analyzed_products_count": len(company["products"]),
        "top_infringing_products": top_products,
        "overall_risk_assessment": overall.strip(),
    }