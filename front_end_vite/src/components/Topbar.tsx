import { useMemo, useState } from "react";
import GlassSurface from "./GlassSurface";

function Topbar() {
  const [open, setOpen] = useState(false);
  const path = useMemo(() => window.location.pathname.toLowerCase(), []);
  const isActive = (href: string) => {
    const target = href.toLowerCase();
    return path === target || path === `${target}.html`;
  };
  return (
    <div className="topbar-sticky">
      <GlassSurface className="topbar-glass" height="46px" backgroundOpacity={0.1} borderRadius={999}>
        <div className="topbar-inner">
          <div className="topbar-logo" aria-hidden="true">
            <img src="/glass-box-256.png" alt="Menu Icon" />
          </div>
          <div className="topbar-actions">
            <nav className="topbar-links">
              <a className={isActive("/") ? "is-active" : ""} href="/">首页</a>
              <a className={isActive("/detect") ? "is-active" : ""} href="/detect">检测</a>
              <a className={isActive("/rules") ? "is-active" : ""} href="/rules">规则</a>
              <a className={isActive("/waybills") ? "is-active" : ""} href="/waybills">运单</a>
              <a className={isActive("/info") ? "is-active" : ""} href="/info">文档</a>
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
            <a className={isActive("/") ? "is-active" : ""} href="/">首页</a>
            <a className={isActive("/detect") ? "is-active" : ""} href="/detect">检测</a>
            <a className={isActive("/rules") ? "is-active" : ""} href="/rules">规则</a>
            <a className={isActive("/waybills") ? "is-active" : ""} href="/waybills">运单</a>
            <a className={isActive("/info") ? "is-active" : ""} href="/info">文档</a>
          </nav>
        </GlassSurface>
      </div>
    </div>
  );
}

export default Topbar;
