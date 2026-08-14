import json
from fastapi import FastAPI, HTTPException
from data_loader import get_patent
from data_loader import get_company
from pydantic import BaseModel
from pipeline import analyze
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI application
app = FastAPI(title="Patent Infringement Check API")

# Allow requests from the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CheckRequest(BaseModel):
    patent_id: str
    company_name: str

# Infringement analysis
@app.post("/api/check")
def check(req: CheckRequest):
    return analyze(req.patent_id, req.company_name)

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