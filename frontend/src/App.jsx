import { useState, useEffect } from "react";

// Pick badge color by risk level
function levelColor(level) {
  if (level === "High") return "#c00";
  if (level === "Moderate") return "#e67e22";
  return "#27ae60";
}

export default function App() {
  const [patentId, setPatentId] = useState("");
  const [company, setCompany] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reports, setReports] = useState([]);

  // Load history once when the page opens
  useEffect(() => {
    loadReports();
  }, []);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patent_id: patentId, company_name: company }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error?.message || "分析失败");
        return;
      }
      setResult(data);
    } catch (e) {
      setError("无法连接后端服务");
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(result),
      });
      if (!res.ok) {
        alert("保存失败");
        return;
      }
      await loadReports();
      alert("已保存");
    } catch (e) {
      alert("保存失败:无法连接后端服务");
    }
  }

  async function loadReports() {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/reports");
      if (!res.ok) {
        console.error("加载历史报告失败");
        return;
      }
      setReports(await res.json());
    } catch (e) {
      console.error("加载历史报告失败:无法连接后端服务");
    }
  }

  function downloadJson(data) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `report_${data.patent_id}.json`;
    a.click();
  }

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", textAlign: "left" }}>
      <h1>Patent Infringement Check</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <input value={patentId} onChange={e => setPatentId(e.target.value)} placeholder="Patent ID" />
        <input value={company} onChange={e => setCompany(e.target.value)} placeholder="Company Name" />
        <button onClick={handleAnalyze} disabled={loading}>
          {loading ? "分析中…" : "Analyze"}
        </button>
      </div>

      {loading && <p style={{ color: "#666" }}>分析中,约需 20 秒…</p>}

      {error && (
        <div style={{ background: "#fee", color: "#c00", padding: "12px 16px", borderRadius: 6, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {result && (
        <div>
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            <button onClick={handleSave}>Save Report</button>
            <button onClick={() => downloadJson(result)}>Download JSON</button>
          </div>

          <div style={{ background: "#f5f5f5", padding: 16, borderRadius: 6, marginBottom: 20 }}>
            <h3 style={{ marginTop: 0 }}>整体风险评估</h3>
            <p style={{ margin: 0 }}>{result.overall_risk_assessment}</p>
            <p style={{ margin: "12px 0 0", fontSize: 13, color: "#666" }}>
              {result.patent_id} × {result.company_name} · 共分析 {result.analyzed_products_count} 个产品 · {result.analysis_date}
            </p>
          </div>

          {result.top_infringing_products.map(p => (
            <div key={p.product_name} style={{ border: "1px solid #ddd", borderRadius: 6, padding: 16, marginBottom: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <h3 style={{ margin: 0 }}>{p.product_name}</h3>
                <span style={{
                  background: levelColor(p.infringement_likelihood),
                  color: "#fff",
                  padding: "2px 10px",
                  borderRadius: 12,
                  fontSize: 13,
                }}>
                  {p.infringement_likelihood}
                </span>
              </div>

              <p style={{ fontSize: 13, color: "#666" }}>
                命中权利要求: {p.relevant_claims.join(", ")}
              </p>

              <strong style={{ fontSize: 14 }}>匹配特征</strong>
              <ul style={{ marginTop: 6 }}>
                {p.matched_features.map(f => <li key={f}>{f}</li>)}
              </ul>

              <p style={{ marginBottom: 0 }}>{p.explanation}</p>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 40 }}>
        <h2 style={{ fontSize: 20 }}>历史报告</h2>
        {reports.length === 0 ? (
          <p style={{ color: "#666" }}>暂无保存的报告</p>
        ) : (
          <ul style={{ paddingLeft: 20 }}>
            {reports.map(r => (
              <li key={r.analysis_id} style={{ marginBottom: 6 }}>
                {r.analysis_date} · {r.patent_id} × {r.company_name}
                <span style={{ color: "#999", fontSize: 12 }}> ({r.analysis_id})</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}