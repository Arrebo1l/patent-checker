import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from data_loader import get_patent

load_dotenv()  # Load GOOGLE_API_KEY from .env

# Create the LLM
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

# Take claim 1 of the test patent
patent = get_patent("US-RE49889-E1")
claim1 = json.loads(patent["claims"])[0]["text"]

# Three different prompts to compare
prompts = {
    "直白翻译": "把这条专利权利要求直接翻译成通俗的中文：\n{claim}",
    "面向产品经理": "假设你在向一位产品经理解释，用通俗的语言说明这条专利权利要求保护的是什么功能：\n{claim}",
    "提炼重点": "把这条专利权利要求拆解成 3-5 条重点，用列表形式呈现：\n{claim}",
}

# Run each prompt and print the result
for name, template in prompts.items():
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    result = chain.invoke({"claim": claim1})
    print("=" * 40)
    print(f"【{name}】")
    content = result.content
    if isinstance(content, list):
        content = "".join(block.get("text", "") for block in content if isinstance(block, dict))
    print(content)
    print()