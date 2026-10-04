import { useEffect } from "react";
import { PractitionerApp } from "../features/matters/PractitionerApp";
import { ShowcaseApp } from "../features/showcase/ShowcaseApp";

export function App() {
  const matterId = window.location.pathname.match(/^\/app\/matters\/([^/]+)\/?$/)?.[1];
  const proposalId = window.location.pathname.match(/^\/app\/matter-proposals\/([^/]+)\/?$/)?.[1];
  const practitioner = !!matterId || !!proposalId || ["/app", "/app/"].includes(window.location.pathname);
  useEffect(() => {
    document.title = practitioner
      ? `${matterId ? "Matter" : proposalId === "new" ? "Create Matter" : proposalId ? "Matter Proposal" : "Matters"} · Private Client Graph`
      : "Public showcase · Private Client Graph";
  }, [practitioner, matterId, proposalId]);
  return practitioner ? <PractitionerApp matterId={matterId} proposalId={proposalId} /> : <ShowcaseApp />;
}
