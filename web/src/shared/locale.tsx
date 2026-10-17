import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { catalogue } from "./locale-catalogue";

export type Locale = "en" | "zh-CN";
type Values = Record<string, string | number>;

export function translate(locale: Locale, key: string, values: Values = {}) {
  const text = locale === "zh-CN" ? catalogue[key] ?? key : key;
  return text.replace(/\{(\w+)\}/g, (token, name: string) => String(values[name] ?? token));
}

const LocaleContext = createContext({
  locale: "en" as Locale,
  setLocale: (_locale: Locale) => {},
  t: (key: string, values?: Values) => translate("en", key, values),
});

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(preferredLocale);
  useEffect(() => {
    document.documentElement.lang = locale;
    try {
      window.localStorage.setItem("pcg-locale", locale);
    } catch {
      // Preference storage is optional.
    }
  }, [locale]);
  const value = useMemo(() => ({
    locale,
    setLocale,
    t: (key: string, values?: Values) => translate(locale, key, values),
  }), [locale]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale() {
  return useContext(LocaleContext);
}

function preferredLocale(): Locale {
  try {
    return window.localStorage.getItem("pcg-locale") === "zh-CN" ? "zh-CN" : "en";
  } catch {
    return "en";
  }
}
