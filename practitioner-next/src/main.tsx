import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";

const LandingPage = lazy(() => import("./landing/LandingPage"));
const PractitionerApp = lazy(() =>
  import("./app/App").then(({ App }) => ({ default: App })),
);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Suspense fallback={<p role="status">Loading Private Client Graph…</p>}>
      {window.location.pathname === "/" ? <LandingPage /> : <PractitionerApp />}
    </Suspense>
  </StrictMode>,
);
