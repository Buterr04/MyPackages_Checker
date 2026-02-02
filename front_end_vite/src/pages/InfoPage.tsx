import SpotlightCard from "../components/SpotlightCard";
import Topbar from "../components/Topbar";

function InfoPage() {
  return (
    <div className="shell">
      <Topbar />
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

export default InfoPage;
