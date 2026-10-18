import { useEffect, useRef, useState } from "react";
import { MotionConfig } from "motion/react";
import { LocaleProvider, useLocale } from "../shared/locale";
import { Icon } from "../shared/Icon";
import { signOut } from "../shared/api";
import { ErrorNotice } from "../shared/Feedback";
import { Ledger } from "../ledger/Ledger";
import { Intake } from "../intake/Intake";
import { ReviewPage } from "../review/ReviewPage";
import "./app.css";

export function App() {
  return (
    <MotionConfig reducedMotion="user">
      <LocaleProvider>
        <Shell />
      </LocaleProvider>
    </MotionConfig>
  );
}
function Shell() {
  const { t, locale, setLocale } = useLocale();
  const [menu, setMenu] = useState(false);
  const path = window.location.pathname.replace(/\/$/, "");
  const review = path.match(/^\/app\/(matters|matter-proposals)\/([^/]+)$/);
  const isNew = path === "/app/matter-proposals/new";
  return (
    <div className="atlas">
      <a className="skip-link" href="#main">
        {t("Skip to content")}
      </a>
      <aside className={"rail " + (menu ? "rail-open" : "")}>
        <a href="/app" className="brand">
          <Icon name="atlas" />
          <span>
            Private Client
            <br />
            Graph
          </span>
        </a>
        <div className="rail-label">{t("Working Atlas")}</div>
        <nav aria-label={t("Practitioner application")}>
          <a href="/app" aria-current={path === "/app" ? "page" : undefined}>
            <Icon name="atlas" />
            {t("Matters")}
          </a>
          <a
            href="/app/matter-proposals/new"
            aria-current={isNew ? "page" : undefined}
          >
            <Icon name="plus" />
            {t("New proposal")}
          </a>
        </nav>
        <div className="rail-bottom">
          <p className="environment">
            <span />
            {t("Synthetic environment")}
          </p>
          <p>{t("Fictional material. Real review workflow.")}</p>
          <div className="utilities">
            <label className="language">
              <span className="sr-only">{t("Language")}</span>
              <select
                value={locale}
                onChange={(event) =>
                  setLocale(event.target.value as "en" | "zh-CN")
                }
              >
                <option value="en">English</option>
                <option value="zh-CN">简体中文</option>
              </select>
            </label>
            <Account />
          </div>
        </div>
      </aside>
      <div className="app-body">
        <header className="topbar">
          <button
            className="mobile-menu icon-button"
            aria-label={t("Menu")}
            aria-expanded={menu}
            onClick={() => setMenu(!menu)}
          >
            <Icon name={menu ? "close" : "menu"} />
          </button>
          <a href="/app">{t("Matters")}</a>
          <span className="topbar-divider" />
          <span>
            {t(
              isNew
                ? "New proposal"
                : review
                  ? "Review workspace"
                  : "Matter ledger",
            )}
          </span>
          <span className="topbar-end">{t("Evidence-led review")}</span>
        </header>
        <div className="synthetic-banner">
          <span className="synthetic-dot" />
          {t(
            "Synthetic or fictional material only. Do not upload real client or personal information.",
          )}
        </div>
        <main id="main">
          {isNew ? (
            <Intake />
          ) : review ? (
            <ReviewPage
              kind={review[1] as "matters" | "matter-proposals"}
              id={decodeURIComponent(review[2])}
            />
          ) : path === "/app" || path === "" ? (
            <Ledger />
          ) : (
            <section className="empty">
              <h1>{t("Page not found")}</h1>
              <a href="/app">{t("Back to Matters")}</a>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
function Account() {
  const { t } = useLocale();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const region = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) {
        setOpen(false);
        trigger.current?.focus();
      }
    };
    const outside = (event: PointerEvent) => {
      if (!busy && !region.current?.contains(event.target as Node))
        setOpen(false);
    };
    document.addEventListener("keydown", close);
    document.addEventListener("pointerdown", outside);
    return () => {
      document.removeEventListener("keydown", close);
      document.removeEventListener("pointerdown", outside);
    };
  }, [open, busy]);
  async function logout() {
    setBusy(true);
    setError(undefined);
    try {
      await signOut();
      window.location.assign("/app");
    } catch (failure) {
      setError(failure);
      setBusy(false);
    }
  }
  return (
    <div
      className="account"
      ref={region}
      onBlur={(event) => {
        if (!busy && !event.currentTarget.contains(event.relatedTarget))
          setOpen(false);
      }}
    >
      <button
        ref={trigger}
        className="icon-button"
        aria-label={t("Account menu")}
        aria-expanded={open}
        aria-controls="account-panel"
        onClick={() => setOpen(!open)}
        disabled={busy}
      >
        <Icon name="person" />
      </button>
      {open && (
        <div className="account-panel" id="account-panel">
          <h2>{t("Account")}</h2>
          <a
            href={
              import.meta.env.VITE_PCG_SHOWCASE_URL ?? "https://localhost:8443/"
            }
          >
            {t("Public showcase")}
          </a>
          <button disabled={busy} onClick={logout}>
            {t(busy ? "Signing out…" : "Sign out")}
          </button>
          {error !== undefined && <ErrorNotice error={error} />}
        </div>
      )}
    </div>
  );
}
