import { useEffect } from "react";
import { PractitionerApp } from "./PractitionerApp";
import { ShowcaseApp } from "./ShowcaseApp";

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
