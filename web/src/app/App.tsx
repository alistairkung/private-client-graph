import { DemoApp } from "../features/demo/DemoApp";
import { useLocale } from "../shared/locale";
import { useEffect } from "react";
import { PractitionerApp } from "../features/matters/PractitionerApp";
import { ShowcaseApp } from "../features/showcase/ShowcaseApp";

export function App() {
  const { t } = useLocale();
  const demo = window.location.pathname === "/demo" || window.location.pathname.startsWith("/demo/");
  const matterId = window.location.pathname.match(/^\/app\/matters\/([^/]+)\/?$/)?.[1];
  const proposalId = window.location.pathname.match(/^\/app\/matter-proposals\/([^/]+)\/?$/)?.[1];
  const practitioner = !!matterId || !!proposalId || ["/app", "/app/"].includes(window.location.pathname);
  useEffect(() => {
    document.title = demo ? `${t("Demo application")} · Private Client Graph` : practitioner
      ? `${t(matterId ? "Matter" : proposalId === "new" ? "Create Matter" : proposalId ? "Matter Proposal" : "Matters")} · Private Client Graph`
      : `${t("Public showcase")} · Private Client Graph`;
  }, [demo, practitioner, matterId, proposalId, t]);
  return demo ? <DemoApp /> : practitioner ? <PractitionerApp matterId={matterId} proposalId={proposalId} /> : <ShowcaseApp />;
}
