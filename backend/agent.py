import json
from data_loader import get_patent, get_company
from matcher import get_first_independent_claim_features, rank_products
from pipeline import analyze
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)


# Tool 1: explain a patent's core claim feature
def tool_explain_claims(patent_id):
    patent = get_patent(patent_id)
    if patent is None:
        return {"error": f"找不到专利 {patent_id}"}
    features = get_first_independent_claim_features(patent)
    return {"patent_id": patent_id, "features": features}


# Tool 2: find top 2 possibly infringing products 
def tool_match(patent_id, company_name):
    patent = get_patent(patent_id)
    if patent is None:
        return {"error": f"找不到专利 {patent_id}"}
    company = get_company(company_name)
    if company is None:
        return {"error": f"找不到公司 {company_name}"}
    top2 = rank_products(patent, company)
    return {"patent_id": patent_id, "company_name": company["name"], "top_products": top2}


# Tool 3: full overall risk report
def tool_risk(patent_id, company_name):
    return analyze(patent_id, company_name)

# Strip code fences
def _clean_json(raw):
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)

# Router: let the LLM decide which tool to call
def route(question):
    prompt = ChatPromptTemplate.from_template(
        "你是任务路由器。根据用户问题,判断该调用哪个工具,并抽取参数。\n"
        "可选工具: explain(解释专利claims,需要patent_id)、"
        "match(找可能侵权产品,需要 patent_id 和 company_name)、"
        "risk(整体风险评估,需要 patent_id 和 company_name)。\n"
        "只输出 JSON: {{\"tool\": \"...\", \"patent_id\": \"...\", \"company_name\": \"...\", \"missing\": [缺失的参数名]}}\n"
        "用户问题: {question}"
    )
    chain = prompt | llm
    raw = chain.invoke({"question": question}).text
    return _clean_json(raw)

# Call the tool the router picked or ask for missing info
def handle(question):
    r = route(question)

    # Ask the user instead of calling a tool
    if r.get("missing"):
        return f"请补充这些信息: {', '.join(r['missing'])}"

    tool = r.get("tool")
    if tool == "explain":
        return tool_explain_claims(r["patent_id"])
    elif tool == "match":
        return tool_match(r["patent_id"], r["company_name"])
    elif tool == "risk":
        return tool_risk(r["patent_id"], r["company_name"])
    else:
        return f"无法识别的任务: {tool}"


# Command line chat loop; type q to quit
if __name__ == "__main__":
    print("专利侵权初筛助手(输入 q 退出)")
    while True:
        question = input("\n你的问题: ").strip()
        if question == "q":
            print("下次见!")
            break
        if not question:
            continue
        try:
            result = handle(question)
            print(result)
        except Exception as e:
            print("出错了:", e)

