import { BrandMark } from "../brand/BrandMark";
import { LanguageControl } from "../LanguageControl";
import { useLocale } from "../locale";
import "../../features/showcase/showcase.css";

export function PublicHeader() {
  const { t } = useLocale();
  const home = window.location.pathname === "/";
  const research = /^\/research-results\/?$/.test(window.location.pathname);
  return <header className="showcase-header folio-width">
    <a className="showcase-brand" href="/"><BrandMark />Private Client Graph</a>
    <nav aria-label={t("Public showcase")}>
      <a href={home ? "#approach" : "/#approach"}>{t("The approach")}</a>
      <a href={home ? "#case-01" : "/#case-01"}>{t("Explore cases")}</a>
      <a href="/research-results" aria-current={research ? "page" : undefined}>{t("Research results")}</a>
      <a href="/demo">{t("Demo application")}</a>
    </nav>
    <LanguageControl />
    <span className="showcase-notice">{t("Synthetic research prototype")}</span>
  </header>;
}
