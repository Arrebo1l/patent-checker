import { useState } from "react";

export default function App() {
  const [patentId, setPatentId] = useState("");
  const [company, setCompany] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleAnalyze() {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patent_id: patentId, company_name: company }),
      });
      setResult(await res.json());
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: "40px auto" }}>
      <h1>Patent Infringement Check</h1>
      <input value={patentId} onChange={e => setPatentId(e.target.value)} placeholder="Patent ID" />
      <input value={company} onChange={e => setCompany(e.target.value)} placeholder="Company Name" />
      <button onClick={handleAnalyze} disabled={loading}>
        {loading ? "分析中…" : "Analyze"}
      </button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}