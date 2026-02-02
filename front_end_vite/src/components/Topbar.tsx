import GlassSurface from "./GlassSurface";

function Topbar() {
  return (
    <div className="topbar-sticky">
      <GlassSurface className="topbar-glass" width="90%" height="50px" backgroundOpacity={0.1} borderRadius={999}>
        <div className="topbar-inner">
          <div className="topbar-logo" aria-hidden="true">
            RB
          </div>
          <div className="topbar-actions">
            <nav className="topbar-links">
              <a href="/">Home</a>
              <a href="/detect">Detect</a>
              <a href="/info">Docs</a>
              <a href="/waybills">Waybills</a>
            </nav>
            <div className="topbar-menu">☰</div>
          </div>
        </div>
      </GlassSurface>
    </div>
  );
}

export default Topbar;
