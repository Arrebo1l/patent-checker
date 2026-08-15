import json
from fastapi import FastAPI, HTTPException
from data_loader import get_patent
from data_loader import get_company
from pydantic import BaseModel
from pipeline import analyze
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# Create the FastAPI application
app = FastAPI(title="Patent Infringement Check API")

# Allow requests from the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Where saved reports are stored
REPORTS = Path(__file__).resolve().parent.parent / "data" / "reports.json"

# Append one analysis result to reports.json
def save_report(report: dict):
    reports = json.loads(REPORTS.read_text(encoding="utf-8")) if REPORTS.exists() else []
    reports.append(report)
    REPORTS.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")

class CheckRequest(BaseModel):
    patent_id: str
    company_name: str

# Infringement analysis
@app.post("/api/check")
def check(req: CheckRequest):
    return analyze(req.patent_id, req.company_name)

# Save one analysis result
@app.post("/api/reports")
def create_report(report: dict):
    save_report(report)
    return {"status": "saved"}


# List saved reports (summary fields only)
@app.get("/api/reports")
def list_reports():
    if not REPORTS.exists():
        return []
    reports = json.loads(REPORTS.read_text(encoding="utf-8"))
    return [
        {
            "analysis_id": r["analysis_id"],
            "analysis_date": r["analysis_date"],
            "patent_id": r["patent_id"],
            "company_name": r["company_name"],
        }
        for r in reports
    ]

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}

# Get patent by publication number
@app.get("/patents/{publication_number}")
def read_patent(publication_number: str):
    p = get_patent(publication_number)
    if p is None:
        raise HTTPException(status_code=404, detail="Patent not found")
    return {
        "publication_number": p["publication_number"],
        "title": p["title"],
        "assignee": p["assignee"],
        "grant_date": p["grant_date"],
        "claim_count": len(json.loads(p["claims"])),
    }

# Get product by company name
@app.get("/companies/{company_name}/products")
def read_company(company_name):
    c = get_company(company_name)
    if c is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return {
        "company_name": c["name"],
        "products": c["products"]
    }