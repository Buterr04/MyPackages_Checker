import { useState, type FormEvent } from "react";
import SpotlightCard from "../components/SpotlightCard";
import Topbar from "../components/Topbar";
import { apiFetch } from "../lib/api";

function RulesPage() {
  const [docResult, setDocResult] = useState("等待中...");
  const [docBusy, setDocBusy] = useState(false);
  const [ingestBusy, setIngestBusy] = useState(false);
  const [listBusy, setListBusy] = useState(false);
  const [listResult, setListResult] = useState("等待中...");

  const handleDocSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const file = form.querySelector<HTMLInputElement>("#doc-file")?.files?.[0];
    if (!file) {
      setDocResult("请选择一个文档文件。");
      return;
    }
    setDocBusy(true);
    setDocResult("正在提交...");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const data = await apiFetch("/docs/upload", { method: "POST", body: formData });
      setDocResult(JSON.stringify(data, null, 2));
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
      const data = await apiFetch("/docs/ingest", { method: "POST" });
      setDocResult(JSON.stringify(data, null, 2));
    } catch (err: any) {
      setDocResult(err?.message || String(err));
    } finally {
      setIngestBusy(false);
    }
  };

  const handleDocList = async () => {
    setListBusy(true);
    setListResult("查询中...");
    try {
      const data = await apiFetch("/docs/list");
      setListResult(JSON.stringify(data, null, 2));
    } catch (err: any) {
      setListResult(err?.message || String(err));
    } finally {
      setListBusy(false);
    }
  };

  return (
    <div className="shell">
      <Topbar />
      <header className="header-stack">
        <div>
          <h1>规则文档维护</h1>
          <div className="hint">上传或更新赔付条款文档，并刷新向量库。</div>
        </div>
      </header>

      <div className="grid">
        <SpotlightCard className="card">
          <div className="row">
            <h3>上传文档</h3>
            <span className="tag">/docs/upload</span>
          </div>
          <form id="doc-form" onSubmit={handleDocSubmit}>
            <label htmlFor="doc-file">选择文档文件</label>
            <input type="file" id="doc-file" name="doc-file" accept=".txt,.md,.json" />
            <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
              <button type="submit" id="doc-submit" disabled={docBusy}>
                上传
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

        <SpotlightCard className="card">
          <div className="row">
            <h3>查询文档</h3>
            <span className="tag">/docs/list</span>
          </div>
          <p>查看当前向量库中的文档 ID 与元数据。</p>
          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
            <button type="button" onClick={handleDocList} disabled={listBusy}>
              查询列表
            </button>
          </div>
          <div style={{ marginTop: 12 }}>
            <label>查询结果</label>
            <pre id="doc-list">{listResult}</pre>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}

export default RulesPage;
