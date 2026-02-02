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
            <h3>赔付报告</h3>
            <span className="tag">report</span>
          </div>
          <div className="stack">
            <div>
              <label>结论</label>
              <pre>{visionResult}</pre>
            </div>
            <div>
              <label>依据摘要</label>
              <pre>{visionReasons}</pre>
            </div>
            <div>
              <label>说明</label>
              <pre>可在此扩展赔付金额、规则引用与审核意见。</pre>
            </div>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}

export default DetectPage;
