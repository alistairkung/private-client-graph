import { useEffect, useRef, useState } from "react";
import {
  AnimatePresence,
  motion,
  MotionConfig,
  useReducedMotion,
} from "motion/react";
import { LocaleProvider, useLocale } from "../shared/locale";
import { Icon } from "../shared/Icon";
import { signOut } from "../shared/api";
import { ErrorNotice } from "../shared/Feedback";
import { Ledger } from "../ledger/Ledger";
import { Intake } from "../intake/Intake";
import { ReviewPage } from "../review/ReviewPage";
import { clearSessionState } from "../shared/session-state";
import { useAppPath } from "./navigation";
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
  const path = useAppPath();
  const reduced = useReducedMotion();
  const compact = useCompactLayout();
  const menuTrigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    setMenu(false);
  }, [path]);
  useEffect(() => {
    if (!menu) return;
    const close = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setMenu(false);
      menuTrigger.current?.focus();
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [menu]);
  const review = path.match(/^\/app\/(matters|matter-proposals)\/([^/]+)$/);
  const isNew = path === "/app/matter-proposals/new";
  return (
    <div className="atlas">
      <a className="skip-link" href="#main">
        {t("Skip to content")}
      </a>
      <AnimatePresence initial={false}>
        {compact && menu && (
          <motion.button
            key="shade"
            className="rail-shade"
            aria-label={t("Close menu")}
            onClick={() => setMenu(false)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.12 }}
          />
        )}
        {(!compact || menu) && (
          <motion.aside
            key="rail"
            className={"rail " + (menu ? "rail-open" : "")}
            inert={compact && !menu}
            initial={compact ? { x: reduced ? 0 : -16, opacity: 0 } : false}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: reduced ? 0 : -16, opacity: 0 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
          >
            <a href="/app" className="brand">
              <Icon name="atlas" />
              <span>
                Private Client
                <br />
                Graph
              </span>
            </a>
            <nav aria-label={t("Practitioner application")}>
              <a
                href="/app"
                aria-current={path === "/app" ? "page" : undefined}
              >
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
          </motion.aside>
        )}
      </AnimatePresence>
      <div className="app-body">
        <header className="topbar">
          <button
            ref={menuTrigger}
            className="mobile-menu icon-button"
            aria-label={t("Menu")}
            aria-expanded={menu}
            onClick={() => setMenu(!menu)}
          >
            <Icon name={menu ? "close" : "menu"} />
          </button>
          <a href="/app">{t("Matters")}</a>
          <span className="topbar-end">{t("Synthetic environment")}</span>
        </header>
        <div className="synthetic-banner">
          <span className="synthetic-dot" />
          {t(
            "Synthetic or fictional material only. Do not upload real client or personal information.",
          )}
        </div>
        <motion.main
          id="main"
          tabIndex={-1}
          key={path}
          initial={{ opacity: reduced ? 1 : 0.65 }}
          animate={{ opacity: 1 }}
          transition={{ duration: reduced ? 0 : 0.16 }}
        >
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
        </motion.main>
      </div>
    </div>
  );
}
function useCompactLayout() {
  const [compact, setCompact] = useState(
    () => window.matchMedia("(max-width: 900px)").matches,
  );
  useEffect(() => {
    const media = window.matchMedia("(max-width: 900px)");
    const update = () => setCompact(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  return compact;
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
    const outside = (event: PointerEvent) => {
      if (!busy && !region.current?.contains(event.target as Node))
        setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    return () => {
      document.removeEventListener("pointerdown", outside);
    };
  }, [open, busy]);
  async function logout() {
    setBusy(true);
    setError(undefined);
    try {
      await signOut();
      clearSessionState();
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
      onKeyDown={(event) => {
        if (event.key !== "Escape" || !open || busy) return;
        event.stopPropagation();
        event.preventDefault();
        setOpen(false);
        trigger.current?.focus();
      }}
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
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            className="account-panel"
            id="account-panel"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 3 }}
            transition={{ duration: 0.14, ease: [0.16, 1, 0.3, 1] }}
          >
            <h2>{t("Account")}</h2>
            <a
              href={
                import.meta.env.VITE_PCG_SHOWCASE_URL ??
                "https://localhost:8443/"
              }
            >
              {t("Public showcase")}
            </a>
            <button disabled={busy} onClick={logout}>
              {t(busy ? "Signing out…" : "Sign out")}
            </button>
            {error !== undefined && <ErrorNotice error={error} />}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
