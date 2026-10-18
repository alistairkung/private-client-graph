import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { chinese } from "./translations";
export type Locale = "en" | "zh-CN";
export type Translate = (
  key: string,
  values?: Record<string, string | number>,
) => string;
const Context = createContext<{
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: Translate;
}>({ locale: "en", setLocale: () => {}, t: (key) => key });
export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(() => {
    try {
      return localStorage.getItem("pcg-locale") === "zh-CN" ? "zh-CN" : "en";
    } catch {
      return "en";
    }
  });
  useEffect(() => {
    document.documentElement.lang = locale;
    try {
      localStorage.setItem("pcg-locale", locale);
    } catch {
      /* Optional preference storage. */
    }
  }, [locale]);
  const t: Translate = (key, values = {}) =>
    (locale === "zh-CN" ? (chinese[key] ?? key) : key).replace(
      /\{(\w+)\}/g,
      (token, name: string) => String(values[name] ?? token),
    );
  return (
    <Context.Provider value={{ locale, setLocale, t }}>
      {children}
    </Context.Provider>
  );
}
export const useLocale = () => useContext(Context);
