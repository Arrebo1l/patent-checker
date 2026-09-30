# Patent Infringement Check App

Enter a patent number and a company name, and the app flags the two products from that company most likely to infringe — with a risk level, the matched technical features, and the reasoning behind each verdict.

Built for **preliminary screening**: it narrows dozens of products down to the few worth a closer human look. It is not a substitute for legal judgment.

## Architecture

```
React (Vite)  →  FastAPI  →  LangChain (Gemini)  →  Local JSON data
```

| Layer | Responsibility |
|---|---|
| Frontend | Input form, result cards, report saving and export |
| Backend | REST API, input validation, result caching, unified error handling |
| LLM | Claim feature extraction, per-product scoring, overall risk summary |
| Data | Patent corpus, company product catalog, saved reports (local JSON) |

How a single analysis runs:

1. Look up the patent and the company (company names support Chinese aliases and case-insensitive partial matching)
2. Parse the patent's claims and locate the first independent claim
3. Use the LLM to extract 3–6 key technical features from that claim
4. Score every product of the company against those features — the LLM returns a 0–100 score with a rationale
5. Sort by score, keep the top 2, and map each score to a High / Moderate / Low risk level
6. Make one more LLM call to write a three-sentence overall risk assessment from the top 2 results

## Requirements

- Python 3.11+
- Node.js 18+
- A Google Gemini API key

## Data Setup

`data/company_product_data.json` is included in the repository.

`data/patents.json` (~17 MB) is excluded from version control because of its size. Place it in the `data/` directory before starting the backend — otherwise `data_loader.py` will fail on startup.

## Running the Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` with your API key:

```
GOOGLE_API_KEY=your_api_key_here
```

Start the server:

```bash
uvicorn main:app --reload
```

- API server: `http://127.0.0.1:8000`
- Interactive API docs: `http://127.0.0.1:8000/docs`

## Running the Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

App URL: `http://localhost:5173`

The frontend calls `http://127.0.0.1:8000` by default, and the backend allows CORS from `http://localhost:5173`, so the two connect out of the box on their default ports.

## API Reference

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/check` | Core endpoint. Takes `patent_id` and `company_name`, returns the full risk analysis |
| POST | `/api/reports` | Saves an analysis result to `data/reports.json` |
| GET | `/api/reports` | Lists saved reports (summary fields only) |
| GET | `/health` | Health check |
| GET | `/patents/{publication_number}` | Returns basic info for one patent |
| GET | `/companies/{company_name}/products` | Returns a company's product list |

### Example Request

```bash
curl -X POST 'http://127.0.0.1:8000/api/check' \
  -H 'Content-Type: application/json' \
  -d '{"patent_id": "US-RE49889-E1", "company_name": "Walmart"}'
```

### Response Shape

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
      "matched_features": ["Displays an electronic product advertisement", "Adds the product identifier to an online shopping list"],
      "explanation": "..."
    }
  ],
  "overall_risk_assessment": "..."
}
```

When a result is served from cache, the response includes an extra `"cached": true` field.

> Note: the LLM prompts are written in Chinese, so feature lists and explanations in real responses are returned in Chinese. The example above is translated for readability.

### Error Responses

Every error uses the same shape:

```json
{"error": {"code": "PATENT_NOT_FOUND", "message": "Patent not found"}}
```

| Code | Status | Meaning |
|---|---|---|
| `PATENT_NOT_FOUND` | 404 | The patent number does not exist |
| `COMPANY_NOT_FOUND` | 404 | The company name could not be matched |
| `INVALID_INPUT` | 422 | Input is empty or longer than 100 characters |
| `LLM_ERROR` | 503 | All LLM calls failed — retry later |

## Performance

A full analysis makes 11 LLM calls internally (10 product scores + 1 summary), so a cold request takes about 60 seconds. Repeat queries are served from an in-memory cache — measured at 0.021 seconds on the second request. Cache keys are case-normalized, so `Walmart` and `walmart` share one entry. The cache is cleared when the server restarts.

## Known Limitations

1. **Preliminary screening only, not legal advice.** Output is meant to narrow the scope of human review; an actual infringement determination requires the full claim set and professional legal analysis.
2. **LLM-dependent, so results vary.** Even at temperature 0, the granularity of extracted claim features can shift between runs, which in turn affects scores and risk levels.
3. **Fixed sample dataset.** Patent and product data come from local JSON files rather than live sources, so coverage is limited. The Chinese company alias table is maintained by hand.
4. **Only the first independent claim is analyzed.** The app does not cover all claims or compare dependent claims one by one.

## Project Structure

```
patent-checker/
├── backend/
│   ├── main.py              # FastAPI app, routes, input validation, caching
│   ├── pipeline.py          # Analysis pipeline orchestration
│   ├── matcher.py           # Product scoring and ranking
│   ├── claims_analyzer.py   # Claim parsing and feature extraction
│   ├── data_loader.py       # Data loading, company name normalization
│   ├── agent.py             # Command-line AI agent (LLM routing)
│   ├── errors.py            # Unified error type and exception handler
│   ├── requirements.txt
│   └── .env                 # Not committed
├── frontend/                # React app
├── data/                    # patents.json / company_product_data.json / reports.json
├── docs/                    # Weekly notes, test records, final report (in Chinese)
└── README.md
```