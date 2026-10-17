import { useLocale } from "./locale";

export function LanguageControl({ compact = false }: { compact?: boolean }) {
  const { locale, setLocale, t } = useLocale();
  if (compact) return <label className="language-dropdown">
    <span className="language-dropdown-display" aria-hidden="true">
      {locale === "en" ? "EN" : "简中"}
      <svg viewBox="0 0 16 16" fill="none"><path d="m4 6 4 4 4-4" /></svg>
    </span>
    <select aria-label={t("Language")} value={locale}
      onChange={event => setLocale(event.target.value === "zh-CN" ? "zh-CN" : "en")}>
      <option value="en" lang="en">English</option>
      <option value="zh-CN" lang="zh-CN">简体中文</option>
    </select>
  </label>;

  return <div className="language-control" role="group" aria-label={t("Language")}>
    <button type="button" lang="en" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>EN</button>
    <button type="button" lang="zh-CN" aria-pressed={locale === "zh-CN"} onClick={() => setLocale("zh-CN")}>简体中文</button>
  </div>;
}
