import { useLocale } from "./locale";
export function LanguageControl() {
  const {locale,setLocale,t} = useLocale();
  return <div className="language-control" role="group" aria-label={t("Language")}>
    <button type="button" lang="en" aria-pressed={locale === "en"} onClick={()=>setLocale("en")}>EN</button>
    <button type="button" lang="zh-CN" aria-pressed={locale === "zh-CN"} onClick={()=>setLocale("zh-CN")}>简体中文</button>
  </div>;
}
