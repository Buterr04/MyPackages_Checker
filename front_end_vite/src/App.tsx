import { useMemo, useState, type FormEvent } from "react";
import "./App.css";
import Aurora from "./components/Aurora";
import SplashCursor from "./components/SplashCursor";
import SpotlightCard from "./components/SpotlightCard";
import GlassSurface from "./components/GlassSurface";

type VisionResponse = {
  analysis?: unknown;
  result?: string;
  reasons?: string[] | null;
  rag?: string | null;
};

function usePage() {
  return useMemo(() => {
    const path = window.location.pathname.toLowerCase();
    if (path === "/info" || path === "/info.html") return "info";
    if (path === "/waybills" || path === "/waybills.html") return "waybills";
    return "home";
  }, []);
}

function HomePage() {
  const [visionResult, setVisionResult] = useState("等待中...");
  const [visionAnalysis, setVisionAnalysis] = useState("等待中...");
  const [visionReasons, setVisionReasons] = useState("等待中...");
  const [visionBusy, setVisionBusy] = useState(false);

  const [docResult, setDocResult] = useState("等待中...");
  const [docBusy, setDocBusy] = useState(false);
  const [ingestBusy, setIngestBusy] = useState(false);

  const parseOptionalBool = (value: string) => {
    if (value === "true") return true;
    if (value === "false") return false;
    return null;
  };

  const handleVisionSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fileInput = form.querySelector<HTMLInputElement>("#image");
    const providerSelect = form.querySelector<HTMLSelectElement>("#vision-provider");
    const waybillInput = form.querySelector<HTMLInputElement>("#vision-waybill");
    const insuredSelect = form.querySelector<HTMLSelectElement>("#vision-insured");
    const fullInsuredSelect = form.querySelector<HTMLSelectElement>("#vision-full-insured");
    const file = fileInput?.files?.[0];

    if (!file) {
      setVisionAnalysis("请选择一张图像。");
      return;
    }

    const provider = providerSelect?.value.trim() ?? "";
    const waybillNo = waybillInput?.value.trim() ?? "";
    const insured = parseOptionalBool(insuredSelect?.value ?? "");
    const fullInsured = parseOptionalBool(fullInsuredSelect?.value ?? "");

    setVisionBusy(true);
    setVisionAnalysis("正在分析图像...");
    setVisionResult("正在评估...");
    setVisionReasons("正在生成依据...");

    const formData = new FormData();
    formData.append("file", file);
    if (insured !== null) formData.append("insured", String(insured));
    if (fullInsured !== null) formData.append("full_insured", String(fullInsured));
    if (waybillNo) formData.append("waybill_no", waybillNo);
    if (provider) formData.append("provider", provider);

    try {
      const res = await fetch("/vision-assess", { method: "POST", body: formData });
      const data = (await res.json()) as VisionResponse & { detail?: string };
      if (res.ok) {
        const analysis = data.analysis ?? {};
        const raw = (analysis as any).raw ?? analysis;
        setVisionAnalysis(raw ? JSON.stringify(raw, null, 2) : JSON.stringify(analysis, null, 2));
        setVisionResult(data.result ?? JSON.stringify(data, null, 2));
        if (Array.isArray(data.reasons) && data.reasons.length) {
          setVisionReasons(data.reasons.join("; "));
        } else if (data.rag) {
          setVisionReasons(data.rag);
        } else {
          setVisionReasons("未提供依据");
        }
      } else {
        const msg = data.detail || "Error";
        setVisionAnalysis(msg);
        setVisionResult(msg);
        setVisionReasons(msg);
      }
    } catch (err: any) {
      const msg = err?.message || String(err);
      setVisionAnalysis(msg);
      setVisionResult(msg);
      setVisionReasons(msg);
    } finally {
      setVisionBusy(false);
    }
  };

  const handleDocSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const id = form.querySelector<HTMLInputElement>("#doc-id")?.value.trim() ?? "";
    const content = form.querySelector<HTMLTextAreaElement>("#doc-content")?.value.trim() ?? "";
    const metaRaw = form.querySelector<HTMLTextAreaElement>("#doc-meta")?.value.trim() ?? "";
    if (!id || !content) {
      setDocResult("请提供文档ID和内容。");
      return;
    }
    let metadata: any = undefined;
    if (metaRaw) {
      try {
        metadata = JSON.parse(metaRaw);
      } catch {
        setDocResult("元数据JSON无效");
        return;
      }
    }
    setDocBusy(true);
    setDocResult("正在提交...");
    try {
      const res = await fetch("/docs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, content, metadata }),
      });
      const data = await res.json();
      setDocResult(res.ok ? JSON.stringify(data, null, 2) : data.detail || "错误");
    } catch (err: any) {
      setDocResult(err?.message || String(err));
    } finally {
      setDocBusy(false);
    }
  };

  const handleDocIngest = async () => {
    setIngestBusy(true);
    setDocResult("正在刷新向量库...");
    try {
      const res = await fetch("/docs/ingest", { method: "POST" });
      const data = await res.json();
      setDocResult(res.ok ? JSON.stringify(data, null, 2) : data.detail || "错误");
    } catch (err: any) {
      setDocResult(err?.message || String(err));
    } finally {
      setIngestBusy(false);
    }
  };

  return (
    <div className="shell">
      <div className="topbar-sticky">
        <GlassSurface className="topbar-glass" width="90%" height="50px" backgroundOpacity={0.1} borderRadius={999}>
          <div className="topbar-inner">
            <div className="topbar-logo" aria-hidden="true">
              RB
            </div>
            <div className="topbar-actions">
              <nav className="topbar-links">
                <a href="/">Home</a>
                <a href="/info">Docs</a>
                <a href="/waybills">Waybills</a>
              </nav>
              <div className="topbar-menu">☰</div>
            </div>
          </div>
        </GlassSurface>
      </div>
      <header className="header-stack">
        <div>
          <h1>包裹识别智能赔付系统</h1>
          <div className="hint">上传图像进行识别和赔付评估</div>
        </div>
      </header>

      <div className="grid">
        <SpotlightCard className="card">
          <div className="row">
            <h3>图像评估</h3>
            <span className="tag">/vision-assess</span>
          </div>
          <form id="vision-form" onSubmit={handleVisionSubmit}>
            <label htmlFor="image">上传图像 (jpg/png/webp)</label>
            <input type="file" id="image" name="image" accept="image/*" />
            <label htmlFor="vision-provider" style={{ marginTop: 8 }}>
              模型提供商
            </label>
            <select id="vision-provider" name="vision-provider">
              <option value="">默认（环境变量）</option>
              <option value="gemini">Gemini</option>
              <option value="openai">OpenAI</option>
              <option value="openai_compat">OpenAI Compatible</option>
            </select>
            <label htmlFor="vision-waybill" style={{ marginTop: 8 }}>
              运单号（可选）
            </label>
            <input type="text" id="vision-waybill" name="vision-waybill" placeholder="例如：WB1001" />
            <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
              <button type="submit" id="vision-submit" disabled={visionBusy}>
                分析与评估
              </button>
            </div>
          </form>
          <div style={{ marginTop: 12 }} className="stack">
            <div>
              <label>评估结果</label>
              <pre id="vision-result">{visionResult}</pre>
            </div>
            <div>
              <label>图像分析（JSON）</label>
              <pre id="vision-analysis">{visionAnalysis}</pre>
            </div>
            <div>
              <label>赔付依据</label>
              <pre id="vision-reasons">{visionReasons}</pre>
            </div>
          </div>
        </SpotlightCard>

        <SpotlightCard className="card">
          <div className="row">
            <h3>上传文档</h3>
            <span className="tag">/docs</span>
          </div>
          <form id="doc-form" onSubmit={handleDocSubmit}>
            <label htmlFor="doc-id">文档ID</label>
            <input type="text" id="doc-id" name="doc-id" placeholder="policy-001" />
            <label htmlFor="doc-content" style={{ marginTop: 8 }}>
              内容
            </label>
            <textarea id="doc-content" name="doc-content" placeholder="赔付规则或说明文本" />
            <label htmlFor="doc-meta" style={{ marginTop: 8 }}>
              元数据 (JSON，可选)
            </label>
            <textarea id="doc-meta" name="doc-meta" placeholder='{"source":"manual"}' />
            <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
              <button type="submit" id="doc-submit" disabled={docBusy}>
                添加 / 更新
              </button>
              <button type="button" id="doc-ingest" onClick={handleDocIngest} disabled={ingestBusy}>
                刷新向量库
              </button>
            </div>
          </form>
          <div style={{ marginTop: 12 }}>
            <label>结果</label>
            <pre id="doc-result">{docResult}</pre>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}

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
      <div className="topbar-sticky">
        <GlassSurface className="topbar-glass" width="90%" height="60px" backgroundOpacity={0.1} borderRadius={999}>
          <div className="topbar-inner">
            <div className="topbar-logo" aria-hidden="true">
              RB
            </div>
            <div className="topbar-actions">
              <nav className="topbar-links">
                <a href="/">Home</a>
                <a href="/info">Docs</a>
                <a href="/waybills">Waybills</a>
              </nav>
              <div className="topbar-menu">☰</div>
            </div>
          </div>
        </GlassSurface>
      </div>
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

function InfoPage() {
  return (
    <div className="shell">
      <div className="topbar-sticky">
        <GlassSurface className="topbar-glass" width="90%" height="60px" backgroundOpacity={0.1} borderRadius={999}>
          <div className="topbar-inner">
            <div className="topbar-logo" aria-hidden="true">
              RB
            </div>
            <div className="topbar-actions">
              <nav className="topbar-links">
                <a href="/">Home</a>
                <a href="/info">Docs</a>
                <a href="/waybills">Waybills</a>
              </nav>
              <div className="topbar-menu">☰</div>
            </div>
          </div>
        </GlassSurface>
      </div>
      <header className="header-stack">
        <div>
          <h1>使用说明</h1>
          <div className="hint">快速了解如何使用包裹检测与赔付评估系统。</div>
        </div>
      </header>

      <div className="grid">
        <SpotlightCard className="card">
          <div className="row">
            <h3>图像评估决策</h3>
            <span className="tag">/vision-assess</span>
          </div>
          <p>上传包裹图片，系统会自动识别破损并给出赔付结论。</p>
          <ul>
            <li>可选填写运单号（如：WB1001），用于获取运单信息。</li>
            <li>选择模型提供商（Gemini / OpenAI / OpenAI Compatible）。</li>
            <li>可选填写保价与足额保价信息。</li>
          </ul>
        </SpotlightCard>

        <SpotlightCard className="card">
          <div className="row">
            <h3>规则文档</h3>
            <span className="tag">/docs</span>
          </div>
          <p>上传或更新赔付条款文档，系统会用于后续 RAG 检索。</p>
          <ul>
            <li>文档 ID 用于唯一标识文档。</li>
            <li>元数据 JSON 可选（例如来源、公司等）。</li>
            <li>如需批量更新，点击“刷新向量库”按钮。</li>
          </ul>
        </SpotlightCard>
      </div>
    </div>
  );
}

function App() {
  const page = usePage();
  return (
    <div className="app-root">
      <div className="aurora-layer">
        <Aurora colorStops={["#0a1a2f", "#5ce1e6", "#7cf1c4"]} amplitude={1.2} blend={0.45} />
      </div>
      <div className="splash-layer">
        <SplashCursor
          BACK_COLOR={{ r: 0.02, g: 0.05, b: 0.08 }}
          SHADING={true}
          SPLAT_FORCE={500}
          DENSITY_DISSIPATION={4.5}
          VELOCITY_DISSIPATION={3.2}
        />
      </div>
      <div className="content-layer">
        {page === "info" ? <InfoPage /> : page === "waybills" ? <WaybillPage /> : <HomePage />}
      </div>
    </div>
  );
}

export default App;
