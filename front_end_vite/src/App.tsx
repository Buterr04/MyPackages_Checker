import { useMemo } from "react";
import "./App.css";
import Aurora from "./components/Aurora";
import SplashCursor from "./components/SplashCursor";
import DetectPage from "./pages/DetectPage";
import HomePage from "./pages/HomePage";
import InfoPage from "./pages/InfoPage";
import RulesPage from "./pages/RulesPage";
import WaybillPage from "./pages/WaybillPage";

function usePage() {
  return useMemo(() => {
    const path = window.location.pathname.toLowerCase();
    if (path === "/detect" || path === "/detect.html") return "detect";
    if (path === "/rules" || path === "/rules.html") return "rules";
    if (path === "/info" || path === "/info.html") return "info";
    if (path === "/waybills" || path === "/waybills.html") return "waybills";
    return "home";
  }, []);
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
        {page === "detect" ? (
          <DetectPage />
        ) : page === "rules" ? (
          <RulesPage />
        ) : page === "info" ? (
          <InfoPage />
        ) : page === "waybills" ? (
          <WaybillPage />
        ) : (
          <HomePage />
        )}
      </div>
    </div>
  );
}

export default App;
