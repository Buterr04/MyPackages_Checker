import { useState } from "react";
import GlassSurface from "./GlassSurface";

function Topbar() {
  const [open, setOpen] = useState(false);
  return (
    <div className="topbar-sticky">
      <GlassSurface className="topbar-glass" height="46px" backgroundOpacity={0.1} borderRadius={999}>
        <div className="topbar-inner">
          <div className="topbar-logo" aria-hidden="true">
            RB
          </div>
          <div className="topbar-actions">
            <nav className="topbar-links">
              <a href="/">首页</a>
              <a href="/detect">检测</a>
              <a href="/rules">规则</a>
              <a href="/waybills">运单</a>
              <a href="/info">文档</a>
            </nav>
            <button
              className="topbar-menu"
              type="button"
              aria-label="Toggle menu"
              aria-expanded={open}
              onClick={() => setOpen((prev) => !prev)}
            >
              ☰
            </button>
          </div>
        </div>
      </GlassSurface>
      <div className="topbar-mobile" data-open={open ? "true" : "false"}>
        <GlassSurface className="topbar-mobile-glass" width="100%" height="auto" backgroundOpacity={0.08} borderRadius={18}>
          <nav className="topbar-mobile-links">
            <a href="/">首页</a>
            <a href="/detect">检测</a>
            <a href="/rules">规则</a>
            <a href="/waybills">运单</a>
            <a href="/info">文档</a>
          </nav>
        </GlassSurface>
      </div>
    </div>
  );
}

export default Topbar;
