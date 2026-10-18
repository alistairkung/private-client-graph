import { useEffect, useId, useRef, useState } from "react";
import { BrandMark } from "../brand/BrandMark";
import { LanguageControl } from "../LanguageControl";
import { useLocale } from "../locale";
import "./showcase-foundations.css";
import "./public-header.css";

const compactNavigation = "(max-width: 1350px)";

export function PublicHeader() {
  const { t } = useLocale();
  const research = /^\/research-results\/?$/.test(window.location.pathname);
  const id = useId();
  const [compact, setCompact] = useState(() => window.matchMedia?.(compactNavigation).matches ?? false);
  const [expanded, setExpanded] = useState(false);
  const navigation = useRef<HTMLDivElement>(null);
  const toggle = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!window.matchMedia) return;
    const media = window.matchMedia(compactNavigation);
    const resize = () => { setCompact(media.matches); setExpanded(false); };
    media.addEventListener("change", resize);
    return () => media.removeEventListener("change", resize);
  }, []);
  useEffect(() => {
    if (!expanded) return;
    const dismiss = (event: PointerEvent) => {
      if (!navigation.current?.contains(event.target as Node)) setExpanded(false);
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [expanded]);

  return (
    <header className="showcase-header folio-width">
      <a className="showcase-brand" href="/"><BrandMark />Private Client Graph</a>
      <div className="public-navigation" ref={navigation} onKeyDown={event => {
        if (event.key === "Escape" && expanded) {
          setExpanded(false);
          toggle.current?.focus();
        }
      }}>
        <button
          type="button"
          className="public-navigation-toggle"
          ref={toggle}
          hidden={!compact}
          aria-expanded={expanded}
          aria-controls={id}
          onClick={() => setExpanded(!expanded)}
        >
          {t("Menu")}
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7h18M3 17h18" /></svg>
        </button>
        <div id={id} className="public-navigation-panel" hidden={compact && !expanded}>
        <nav aria-label={t("Public showcase")}
          onClick={event => { if ((event.target as Element).closest("a")) setExpanded(false); }}>
          <a href="/#landing-main">{t("The approach")}</a>
          <a href="/app?example=case-01">{t("Explore cases")}</a>
          <a href="/research-results" aria-current={research ? "page" : undefined}>{t("Research results")}</a>
          <a href="/app">{t("Practitioner application")}</a>
        </nav>
        {compact && <div className="public-navigation-language" onClick={event => {
          if ((event.target as Element).closest("button")) {
            setExpanded(false);
            toggle.current?.focus();
          }
        }}>
          <LanguageControl />
          <span className="showcase-notice">{t("Synthetic research prototype")}</span>
        </div>}
        </div>
      </div>
      {!compact && <LanguageControl />}
      {!compact && <span className="showcase-notice">{t("Synthetic research prototype")}</span>}
    </header>
  );
}
