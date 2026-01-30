import { useMemo, useState, type FormEvent } from "react";
import "./App.css";

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
      <header>
        <div>
          <h1>Packages Checker包裹检测器</h1>
          <div className="hint">上传图像进行检测，或维护/扩展规则文档。</div>
        </div>
        <div className="nav-group">
          <a className="tag" href="/info">使用说明</a>
          <span className="tag">FastAPI</span>
        </div>
      </header>

      <div className="grid">
        <div className="card">
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
            <label htmlFor="vision-insured" style={{ marginTop: 8 }}>
              是否保价
            </label>
            <select id="vision-insured" name="vision-insured">
              <option value="">未提供</option>
              <option value="true">是</option>
              <option value="false">否</option>
            </select>
            <label htmlFor="vision-full-insured" style={{ marginTop: 8 }}>
              是否足额保价
            </label>
            <select id="vision-full-insured" name="vision-full-insured">
              <option value="">未提供</option>
              <option value="true">是</option>
              <option value="false">否</option>
            </select>
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
        </div>

        <div className="card">
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
        </div>
      </div>
    </div>
  );
}

function InfoPage() {
  return (
    <div className="shell">
      <header>
        <div>
          <h1>使用说明</h1>
          <div className="hint">快速了解如何使用包裹检测与赔付评估系统。</div>
        </div>
        <div className="nav-group">
          <a className="tag" href="/">
            返回主页
          </a>
          <span className="tag">指南</span>
        </div>
      </header>

      <div className="grid">
        <div className="card">
          <div className="row">
            <h3>图像评估</h3>
            <span className="tag">/vision-assess</span>
          </div>
          <p>上传包裹图片，系统会自动识别破损并给出赔付结论。</p>
          <ul>
            <li>可选填写运单号（如：WB1001），用于获取运单信息。</li>
            <li>可选选择模型提供商（Gemini / OpenAI / OpenAI Compatible）。</li>
            <li>可选填写保价与足额保价信息。</li>
          </ul>
        </div>

        <div className="card">
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
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="row">
          <h3>接口与调试</h3>
          <span className="tag">/docs/list</span>
        </div>
        <p>可通过接口查看向量库中文档列表：</p>
        <pre>GET /docs/list</pre>
        <p>如需手动触发文档入库：</p>
        <pre>POST /docs/ingest</pre>
      </div>
    </div>
  );
}

function App() {
  const page = usePage();
  return page === "info" ? <InfoPage /> : <HomePage />;
}

export default App;
