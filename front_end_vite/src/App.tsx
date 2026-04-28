import { useEffect, useMemo, useState } from "react";
import "./App.css";
import Aurora from "./components/Aurora";
import ErrorModal from "./components/ErrorModal";
import SplashCursor from "./components/SplashCursor";
import DetectPage from "./pages/DetectPage";
import HomePage from "./pages/HomePage";
import InfoPage from "./pages/InfoPage";
import RulesPage from "./pages/RulesPage";
import WaybillPage from "./pages/WaybillPage";
import { setGlobalApiErrorHandler, type ApiError } from "./lib/api";

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
  const [apiError, setApiError] = useState<ApiError | null>(null);

  useEffect(() => {
    setGlobalApiErrorHandler((error) => {
      setApiError(error);
    });
    return () => {
      setGlobalApiErrorHandler(null);
    };
  }, []);

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
      <ErrorModal
        open={Boolean(apiError)}
        message={apiError?.message || ""}
        detail={apiError?.detail ? JSON.stringify(apiError.detail, null, 2) : undefined}
        onClose={() => setApiError(null)}
      />
    </div>
  );
}

export default App;
