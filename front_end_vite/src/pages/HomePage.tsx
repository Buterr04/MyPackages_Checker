import GlassSurface from "../components/GlassSurface";
import SpotlightCard from "../components/SpotlightCard";
import Topbar from "../components/Topbar";

function HomePage() {
  return (
    <div className="shell">
      <Topbar />

      <section className="hero">
        <GlassSurface className="hero-badge" width="auto" height="40px" backgroundOpacity={0.1} borderRadius={999}>
          <span>包裹检测</span>
        </GlassSurface>

        <h1 className="hero-title">包裹智能识别赔付系统</h1>
        <p className="hero-subtitle">自动通过图像识别和规则文档，实现包裹破损的智能赔付决策。</p>

        <div className="hero-actions">
          <a className="hero-primary" style={{ width: "160px", height: "44px" }} href="/detect" >
            开始检测
          </a>
          <a href="/info">
            <GlassSurface className="hero-secondary" width="160px" height="44px" backgroundOpacity={0.08} borderRadius={999}>
              了解更多
            </GlassSurface>
          </a>
        </div>
      </section>

      <section className="feature-grid">
        {[
          {
            title: "图像识别",
            text: "上传包裹图片，自动识别破损并给出赔付建议。",
          },
          {
            title: "规则文档",
            text: "支持上传赔付条款，统一管理、可追溯。",
          },
          {
            title: "面单数据",
            text: "查询、维护或批量导入运单信息。",
          },
        ].map((item) => (
          <SpotlightCard key={item.title} className="card">
            <div className="row">
              <h3>{item.title}</h3>
              <span className="tag">Feature</span>
            </div>
            <p>{item.text}</p>
          </SpotlightCard>
        ))}
      </section>
    </div>
  );
}

export default HomePage;
