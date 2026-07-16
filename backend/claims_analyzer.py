import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from data_loader import get_patent

load_dotenv()  # Load GOOGLE_API_KEY from .env

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

def parse_claims(patent):
    """Parse the claims field into a clean list of {num, text}."""
    raw_claims = json.loads(patent["claims"])
    result = []
    for claim in raw_claims:
        result.append({
            "num": int(claim["num"]), 
            "text": claim["text"],
        })
    return result

def is_independent(claim_text):
    """An independent claim does not reference another claim."""
    lowered = claim_text.lower()
    if "of claim" in lowered:
        return False
    if "according to claim" in lowered:
        return False
    return True


def _to_list(raw):
    """Clean the model output and parse it into a Python list."""
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


def extract_features(claim_text):
    """Use the LLM to extract 3-6 key technical features as a list."""
    prompt = ChatPromptTemplate.from_template(
        "你是专利分析助手。阅读下面的权利要求,提取 3~6 条关键技术特征,每条不超过 20 个词。\n"
        "只输出 JSON 数组,例如 [\"feature 1\", \"feature 2\"],不要输出任何其他文字。\n"
        "权利要求:{claim}"
    )
    chain = prompt | llm

    for attempt in range(2):
        raw = chain.invoke({"claim": claim_text}).text
        try:
            return _to_list(raw)
        except json.JSONDecodeError:
            print(f"第 {attempt + 1} 次解析失败,重试…")

    print("警告: 特征提取失败,返回空列表")
    return []

# Run on two patents and save the results in a sample JSON file
if __name__ == "__main__":
    patent_ids = ["US-RE49889-E1", "US-11950524-B2"]
    output = []

    for pid in patent_ids:
        patent = get_patent(pid)
        claims = parse_claims(patent)

        # Find the first independent claim
        first_independent = None
        for claim in claims:
            if is_independent(claim["text"]):
                first_independent = claim
                break

        # Skip this patent if no independent claim was found
        if first_independent is None:
            print(f"{pid} 没有找到独立 claim,跳过")
            continue

        print(f"正在处理 {pid} 的 claim {first_independent['num']} …")
        features = extract_features(first_independent["text"])

        output.append({
            "publication_number": pid,
            "claim_num": first_independent["num"],
            "features": features,
        })

    # Save to docs/claims_features_示例.json
    with open("../docs/claims_features_示例.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("完成!已保存到 docs/claims_features_示例.json")