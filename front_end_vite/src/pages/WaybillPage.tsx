import { useState } from "react";
import SpotlightCard from "../components/SpotlightCard";
import Topbar from "../components/Topbar";

function WaybillPage() {
  const [queryNo, setQueryNo] = useState("");
  const [queryResult, setQueryResult] = useState("等待中...");
  const [saveResult, setSaveResult] = useState("等待中...");
  const [busy, setBusy] = useState(false);
  const [excelFile, setExcelFile] = useState<File | null>(null);

  const [form, setForm] = useState({
    waybill_no: "",
    company: "",
    insured: "",
    full_insured: "",
    weight: "",
    signed: "",
    signed_at: "",
    status: "",
    cost: "",
    price: "",
    route: "",
  });

  const updateField = (key: string, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const parseOptionalBool = (value: string) => {
    if (value === "true") return true;
    if (value === "false") return false;
    return null;
  };

  const handleQuery = async () => {
    if (!queryNo.trim()) {
      setQueryResult("请输入运单号。");
      return;
    }
    setBusy(true);
    setQueryResult("查询中...");
    try {
      const res = await fetch(`/waybills/${encodeURIComponent(queryNo.trim())}`);
      const data = await res.json();
      setQueryResult(res.ok ? JSON.stringify(data, null, 2) : data.detail || "查询失败");
    } catch (err: any) {
      setQueryResult(err?.message || String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleSave = async () => {
    if (!form.waybill_no.trim()) {
      setSaveResult("运单号必填。");
      return;
    }
    setBusy(true);
    setSaveResult("保存中...");
    try {
      const payload: any = {
        waybill_no: form.waybill_no.trim(),
        company: form.company.trim() || null,
        insured: parseOptionalBool(form.insured),
        full_insured: parseOptionalBool(form.full_insured),
        weight: form.weight ? Number(form.weight) : null,
        signed: parseOptionalBool(form.signed),
        signed_at: form.signed_at || null,
        status: form.status.trim() || null,
        cost: form.cost ? Number(form.cost) : null,
        price: form.price ? Number(form.price) : null,
        route: form.route ? form.route.split(",").map((v) => v.trim()).filter(Boolean) : null,
      };
      const res = await fetch("/waybills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setSaveResult(res.ok ? JSON.stringify(data, null, 2) : data.detail || "保存失败");
    } catch (err: any) {
      setSaveResult(err?.message || String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleImportExcel = async () => {
    if (!excelFile) {
      setSaveResult("请选择 Excel 文件。");
      return;
    }
    setBusy(true);
    setSaveResult("导入中...");
    try {
      const formData = new FormData();
      formData.append("file", excelFile);
      const res = await fetch("/waybills/import-excel", { method: "POST", body: formData });
      const data = await res.json();
      setSaveResult(res.ok ? JSON.stringify(data, null, 2) : data.detail || "导入失败");
    } catch (err: any) {
      setSaveResult(err?.message || String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="shell">
      <Topbar />
      <header className="header-stack">
        <div>
          <h1>面单维护</h1>
          <div className="hint">新增、查询或导入快递面单数据。</div>
        </div>
      </header>

      <div className="grid">
        <SpotlightCard className="card">
          <div className="row">
            <h3>查询面单</h3>
            <span className="tag">/waybills/{`{waybill_no}`}</span>
          </div>
          <label htmlFor="query-no">运单号</label>
          <input
            type="text"
            id="query-no"
            value={queryNo}
            onChange={(e) => setQueryNo(e.target.value)}
            placeholder="WB1001"
          />
          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
            <button type="button" onClick={handleQuery} disabled={busy}>
              查询
            </button>
          </div>
          <div style={{ marginTop: 12 }}>
            <label>查询结果</label>
            <pre>{queryResult}</pre>
          </div>
        </SpotlightCard>

        <SpotlightCard className="card">
          <div className="row">
            <h3>新增 / 更新</h3>
            <span className="tag">/waybills</span>
          </div>
          <div className="stack">
            <div>
              <label>运单号</label>
              <input
                type="text"
                value={form.waybill_no}
                onChange={(e) => updateField("waybill_no", e.target.value)}
                placeholder="WB1001"
              />
            </div>
            <div>
              <label>物流公司</label>
              <input
                type="text"
                value={form.company}
                onChange={(e) => updateField("company", e.target.value)}
                placeholder="SF"
              />
            </div>
            <div>
              <label>是否保价</label>
              <select value={form.insured} onChange={(e) => updateField("insured", e.target.value)}>
                <option value="">未提供</option>
                <option value="true">是</option>
                <option value="false">否</option>
              </select>
            </div>
            <div>
              <label>是否足额保价</label>
              <select value={form.full_insured} onChange={(e) => updateField("full_insured", e.target.value)}>
                <option value="">未提供</option>
                <option value="true">是</option>
                <option value="false">否</option>
              </select>
            </div>
            <div>
              <label>重量</label>
              <input
                type="text"
                value={form.weight}
                onChange={(e) => updateField("weight", e.target.value)}
                placeholder="2.3"
              />
            </div>
            <div>
              <label>是否签收</label>
              <select value={form.signed} onChange={(e) => updateField("signed", e.target.value)}>
                <option value="">未提供</option>
                <option value="true">是</option>
                <option value="false">否</option>
              </select>
            </div>
            <div>
              <label>签收日期</label>
              <input
                type="date"
                value={form.signed_at}
                onChange={(e) => updateField("signed_at", e.target.value)}
              />
            </div>
            <div>
              <label>状态</label>
              <input
                type="text"
                value={form.status}
                onChange={(e) => updateField("status", e.target.value)}
                placeholder="delivered"
              />
            </div>
            <div>
              <label>运费</label>
              <input
                type="text"
                value={form.cost}
                onChange={(e) => updateField("cost", e.target.value)}
                placeholder="30"
              />
            </div>
            <div>
              <label>货值</label>
              <input
                type="text"
                value={form.price}
                onChange={(e) => updateField("price", e.target.value)}
                placeholder="100"
              />
            </div>
            <div>
              <label>路由 (逗号分隔)</label>
              <input
                type="text"
                value={form.route}
                onChange={(e) => updateField("route", e.target.value)}
                placeholder="SZ,GZ,SH"
              />
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button type="button" onClick={handleSave} disabled={busy}>
                保存
              </button>
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <label>保存结果</label>
            <pre>{saveResult}</pre>
          </div>
          <div style={{ marginTop: 12 }}>
            <label>Excel 导入</label>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => setExcelFile(e.target.files?.[0] || null)}
            />
            <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
              <button type="button" onClick={handleImportExcel} disabled={busy}>
                确认导入
              </button>
            </div>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}

export default WaybillPage;
