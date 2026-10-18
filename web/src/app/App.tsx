import { ResearchResultsApp } from "../features/public-research/ResearchResultsApp";
import { useLocale } from "../shared/locale";
import { useEffect } from "react";
import { PractitionerApp } from "../features/matters/PractitionerApp";
import { ShowcaseApp } from "../features/showcase/ShowcaseApp";

export function App() {
  const { t } = useLocale();
  const research = /^\/research-results\/?$/.test(window.location.pathname);
  const matterId = window.location.pathname.match(/^\/app\/matters\/([^/]+)\/?$/)?.[1];
  const proposalId = window.location.pathname.match(/^\/app\/matter-proposals\/([^/]+)\/?$/)?.[1];
  const practitioner = !!matterId || !!proposalId || ["/app", "/app/"].includes(window.location.pathname);
  useEffect(() => {
    document.title = research ? `${t("Research results")} · Private Client Graph`
      : practitioner
      ? `${t(matterId ? "Matter" : proposalId === "new" ? "Create Matter" : proposalId ? "Matter Proposal" : "Matters")} · Private Client Graph`
      : `${t("Public showcase")} · Private Client Graph`;
  }, [research, practitioner, matterId, proposalId, t]);
  if (research) return <ResearchResultsApp />;
  if (practitioner) return <PractitionerApp matterId={matterId} proposalId={proposalId} />;
  return <ShowcaseApp />;
}
