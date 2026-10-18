import { Icon } from "../Icon";
import { useLocale, type Locale } from "../locale";
import "./public-header.css";

export function PublicHeader({ currentPage }: { currentPage?: "research" }) {
  const { locale, setLocale, t } = useLocale();
  return (
    <header className="public-header">
      <a className="public-header-brand" href="/" aria-label="Private Client Graph">
        <Icon name="atlas" />
        <span>Private Client Graph</span>
      </a>
      <nav aria-label={t("Main navigation")}>
        <a href="/research-results" aria-current={currentPage === "research" ? "page" : undefined}>
          {t("Research")}
        </a>
        <a className="public-header-enter" href="/app">
          {t("Open practitioner prototype")}
          <Icon name="arrow" />
        </a>
        <label>
          <span className="public-header-sr">{t("Language")}</span>
          <select value={locale} onChange={event => setLocale(event.target.value as Locale)}>
            <option value="en">EN</option>
            <option value="zh-CN">中文</option>
          </select>
        </label>
      </nav>
    </header>
  );
}
