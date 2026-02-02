import { useState, type FormEvent } from "react";
import SpotlightCard from "../components/SpotlightCard";
import Topbar from "../components/Topbar";

type VisionResponse = {
  analysis?: unknown;
  result?: string;
  reasons?: string[] | null;
  rag?: string | null;
};

function DetectPage() {
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
      <Topbar />
      <header className="header-stack">
        <div>
          <h1>包裹识别智能赔付</h1>
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

export default DetectPage;
