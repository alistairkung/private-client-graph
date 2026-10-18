import { lazy, Suspense } from "react";
import { useLocale } from "../shared/locale";
const LandingPage = lazy(() => import("../features/landing/LandingPage"));
const PractitionerApp = lazy(() => import("./PractitionerApp").then(module => ({ default: module.PractitionerApp })));
const ResearchResultsApp = lazy(() => import("../features/public-research/ResearchResultsApp").then(module => ({ default: module.ResearchResultsApp })));

export function App() {
  const { t } = useLocale();
  const path = window.location.pathname;
  return <Suspense fallback={<p role="status">{t("Loading…")}</p>}>
    {/^\/research-results\/?$/.test(path) ? <ResearchResultsApp />
      : /^\/app(?:\/|$)/.test(path) ? <PractitionerApp /> : <LandingPage />}
  </Suspense>;
}
