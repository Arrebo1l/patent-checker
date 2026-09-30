# Patent Infringement Check App

输入一个专利号和一家公司名,自动筛出该公司最可能侵权的 2 个产品,给出风险等级、命中的技术特征和判定理由。

面向专利风险的**初步筛查**场景:把一家公司几十个产品缩小到最值得人工细看的几个,而不是替代法律判断。

## 架构

```
React (Vite)  →  FastAPI  →  LangChain (Gemini)  →  本地 JSON 数据
```

| 层 | 职责 |
|---|---|
| 前端 | 表单输入、结果卡片展示、报告保存与导出 |
| 后端 | REST 接口、输入校验、结果缓存、统一错误处理 |
| LLM | claim 特征提取、产品逐个打分、整体风险总结 |
| 数据 | 专利库、公司产品库、历史报告(本地 JSON) |

一次分析的内部流程:

1. 按专利号和公司名查出记录(公司名支持中文别名和大小写模糊匹配)
2. 解析专利 claims,找出第一条独立权利要求
3. 用 LLM 从该 claim 中提取 3~6 条关键技术特征
4. 拿这组特征逐个比对公司的每个产品,LLM 给出 0~100 分及理由
5. 按分数排序取 Top 2,映射为 High / Moderate / Low 风险等级
6. 再调一次 LLM,基于 Top 2 生成三句话的整体风险评估

## 环境要求

- Python 3.11+
- Node.js 18+
- Google Gemini API key

## 数据准备

`data/company_product_data.json` 已包含在仓库中。

`data/patents.json`(约 17 MB)因体积未纳入版本控制,需自行放入 `data/` 目录后再启动后端,否则 `data_loader.py` 在加载时会直接报错。

## 后端启动

```bash
cd backend
pip install -r requirements.txt
```

在 `backend/` 目录下创建 `.env` 文件,填入 API key:

```
GOOGLE_API_KEY=your_api_key_here
```

启动服务:

```bash
uvicorn main:app --reload
```

- 服务地址:`http://127.0.0.1:8000`
- 交互式 API 文档:`http://127.0.0.1:8000/docs`

## 前端启动

另开一个终端:

```bash
cd frontend
npm install
npm run dev
```

页面地址:`http://localhost:5173`

前端默认请求 `http://127.0.0.1:8000`,后端已对 `http://localhost:5173` 开放 CORS,两端都用默认端口即可直接联通。

## API 一览

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/check` | 核心接口。传入 `patent_id` 和 `company_name`,返回完整风险分析 |
| POST | `/api/reports` | 保存一次分析结果到 `data/reports.json` |
| GET | `/api/reports` | 返回历史报告列表(仅摘要字段) |
| GET | `/health` | 健康检查 |
| GET | `/patents/{publication_number}` | 查询单个专利的基本信息 |
| GET | `/companies/{company_name}/products` | 查询某公司的产品列表 |

### 请求示例

```bash
curl -X POST 'http://127.0.0.1:8000/api/check' \
  -H 'Content-Type: application/json' \
  -d '{"patent_id": "US-RE49889-E1", "company_name": "Walmart"}'
```

### 响应结构

```json
{
  "analysis_id": "c5598a5f",
  "analysis_date": "2026-09-01",
  "patent_id": "US-RE49889-E1",
  "company_name": "Walmart Inc.",
  "analyzed_products_count": 10,
  "top_infringing_products": [
    {
      "product_name": "Walmart Shopping App",
      "infringement_likelihood": "Moderate",
      "relevant_claims": ["1"],
      "matched_features": ["展示产品电子广告", "将产品标识添加至在线购物清单"],
      "explanation": "……"
    }
  ],
  "overall_risk_assessment": "……"
}
```

命中缓存时响应会额外带上 `"cached": true`。

### 错误响应

所有错误统一为同一结构:

```json
{"error": {"code": "PATENT_NOT_FOUND", "message": "Patent not found"}}
```

| 代码 | 状态码 | 含义 |
|---|---|---|
| `PATENT_NOT_FOUND` | 404 | 专利号不存在 |
| `COMPANY_NOT_FOUND` | 404 | 公司名查不到 |
| `INVALID_INPUT` | 422 | 输入为空或超过 100 字符 |
| `LLM_ERROR` | 503 | LLM 调用全部失败,稍后重试 |

## 性能说明

一次完整分析内部要调用 11 次 LLM(10 个产品打分 + 1 次总结),首次请求约 60 秒。相同查询会命中内存缓存,实测第二次为 0.021 秒。缓存 key 经过大小写归一化,`Walmart` 与 `walmart` 共用一份;服务重启后缓存清空。

## 已知限制

1. **仅为初步筛查,不构成法律意见。** 输出用于缩小人工审查范围,真实侵权判定需结合完整权利要求和专业法律分析。
2. **依赖 LLM,结果存在波动。** 即使温度设为 0,claim 特征提取的粒度仍可能在不同次运行间变化,进而影响评分和风险等级。
3. **数据为固定样本库。** 专利与公司产品数据来自本地 JSON 文件,非实时抓取,覆盖范围有限;公司中文别名表为手工维护。
4. **每个专利只分析第一条独立权利要求**,不覆盖全部 claims,也不做从属权利要求的逐条比对。

## 目录结构

```
patent-checker/
├── backend/
│   ├── main.py              # FastAPI 应用、路由、输入校验、缓存
│   ├── pipeline.py          # 分析流水线编排
│   ├── matcher.py           # 产品打分与排序
│   ├── claims_analyzer.py   # claim 解析与特征提取
│   ├── data_loader.py       # 数据加载、公司名归一化
│   ├── agent.py             # 命令行 AI agent(LLM 路由)
│   ├── errors.py            # 统一错误类型与异常处理器
│   ├── requirements.txt
│   └── .env                 # 不提交
├── frontend/                # React 应用
├── data/                    # patents.json / company_product_data.json / reports.json
├── docs/                    # 每周文档、测试记录、结题报告
└── README.md
```