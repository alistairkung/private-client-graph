import { useEffect } from "react";
import { PractitionerApp } from "../features/matters/PractitionerApp";
import { ShowcaseApp } from "../features/showcase/ShowcaseApp";

export function App() {
  const matterId = window.location.pathname.match(/^\/app\/matters\/([^/]+)\/?$/)?.[1];
  const practitioner = !!matterId || ["/app", "/app/"].includes(window.location.pathname);
  useEffect(() => {
    document.title = practitioner
      ? `${matterId ? "Matter" : "Matters"} · Private Client Graph`
      : "Public showcase · Private Client Graph";
  }, [practitioner, matterId]);
  return practitioner ? <PractitionerApp matterId={matterId} /> : <ShowcaseApp />;
}
