import { useEffect, useRef, useState } from "react";
import {
  AnimatePresence,
  motion,
  useReducedMotion,
} from "motion/react";
import { useLocale } from "../shared/locale";
import { Icon } from "../shared/Icon";
import { getProposals, signOut } from "../shared/api";
import { ErrorNotice } from "../shared/Feedback";
import { MatterLedger, ProposalLedger } from "../features/matters/Ledger";
import { useRecordCollection } from "../features/matters/useRecordCollection";
import { Intake } from "../features/matter-proposals/Intake";
import { ReviewPage } from "../features/review/ReviewPage";
import { clearSessionState } from "../shared/session-state";
import { mayLeave, useAppPath, useNavigationLock } from "./navigation";
import "./app.css";
import { AccessProvider, AccessNotice, WriteGate, useAccess } from "../shared/access";
import { CuratedExamples } from "../features/matters/CuratedExamples";

export function PractitionerApp() {
  return <AccessProvider><Shell /></AccessProvider>;
}

function Shell() {
  const { t, locale, setLocale } = useLocale();
  const [menu, setMenu] = useState(false);
  const path = useAppPath();
  const queue = useRecordCollection(getProposals, path);
  const pending = queue.result.status === "ready" ? queue.result.records.length : 0;
  const exampleId = path === "/app" ? new URLSearchParams(window.location.search).get("example") : null;
  const reduced = useReducedMotion();
  const compact = useCompactLayout("(max-width: 900px)");
  const compactNav = useCompactLayout("(max-width: 380px)");
  const menuTrigger = useRef<HTMLButtonElement>(null);
  const utilities = useRef<HTMLDivElement>(null);
  useEffect(() => {
    setMenu(false);
  }, [path, exampleId]);
  useEffect(() => {
    if (!menu || !compact) return;
    const close = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setMenu(false);
      menuTrigger.current?.focus();
    };
    const dismissOutside = (event: PointerEvent) => {
      const target = event.target as Node;
      if (!utilities.current?.contains(target) && !menuTrigger.current?.contains(target)) {
        setMenu(false);
      }
    };
    document.addEventListener("keydown", close);
    document.addEventListener("pointerdown", dismissOutside);
    return () => {
      document.removeEventListener("keydown", close);
      document.removeEventListener("pointerdown", dismissOutside);
    };
  }, [compact, menu]);
  const review = path.match(/^\/app\/(matters|matter-proposals)\/([^/]+)$/);
  const isNew = path === "/app/matter-proposals/new";
  const isQueue = path === "/app/review";
  const isMatters = path === "/app" && !exampleId;
  const currentMatters = isMatters ? "page" : review?.[1] === "matters" ? "location" : undefined;
  const currentReview = isQueue ? "page" : !isNew && review?.[1] === "matter-proposals" ? "location" : undefined;
  const title = isNew ? "New proposal" : isQueue ? "Review proposals" : exampleId ? "Curated examples" : "Matters";
  const count = new Intl.NumberFormat(locale).format(pending);
  const reviewLabel = pending > 0
    ? t(pending === 1 ? "Review, 1 proposal awaiting confirmation" : "Review, {count} proposals awaiting confirmation", { count })
    : t("Review");
  useEffect(() => {
    if (review && !isNew) return;
    document.title = `${t(title)} · Private Client Graph`;
  }, [path, isNew, title, t]);
  const examplesLink = (
    <a className="curated-link" href="/app?example=case-01" aria-current={exampleId ? "page" : undefined}>
      {t("Curated examples")}
    </a>
  );
  return (
    <div className="atlas">
      <a className="skip-link" href="#main">
        {t("Skip to content")}
      </a>
      <header className="practitioner-masthead">
        <div className="masthead-inner">
          <a href="/app" className="brand">
            <strong>Private Client Graph</strong>
            <span>{t("Practitioner application")}</span>
          </a>
          <button
            ref={menuTrigger}
            className="mobile-menu icon-button"
            aria-label={t("Menu")}
            aria-expanded={menu}
            aria-controls="practitioner-utilities"
            onClick={() => setMenu(!menu)}
          >
            <Icon name={menu ? "close" : "menu"} />
          </button>
          <nav className="workflow-nav" aria-label={t("Practitioner application")}>
            <a href="/app" aria-current={currentMatters}>
              {t("Matters")}
            </a>
            <a
              className="review-nav-link"
              href="/app/review"
              aria-current={currentReview}
              aria-label={reviewLabel}
            >
              {t("Review")}
              {pending > 0 && (
                <span className="review-count" aria-hidden="true">{pending > 99 ? "99+" : count}</span>
              )}
            </a>
            <a href="/app/matter-proposals/new" aria-current={isNew ? "page" : undefined}>
              {t("New proposal")}
            </a>
            {!compactNav && examplesLink}
          </nav>
          <div className="utilities" id="practitioner-utilities" ref={utilities} hidden={compact && !menu}>
            {compactNav && examplesLink}
            <label className="language">
              <span className="sr-only">{t("Language")}</span>
              <select value={locale} onChange={(event) => setLocale(event.target.value as "en" | "zh-CN")}>
                <option value="en">English</option>
                <option value="zh-CN">简体中文</option>
              </select>
            </label>
            <Account />
          </div>
        </div>
      </header>
      <div className="app-body">
        <div className="practitioner-disclosures">
          <p className="synthetic-banner">
            <span className="synthetic-dot" aria-hidden="true" />
            {t(
              "Synthetic or fictional material only. Do not upload real client or personal information.",
            )}
          </p>
          <p className="public-source-notice">{t("Sources, Matter Proposals and Matters are publicly readable, including proposals awaiting confirmation.")}</p>
        </div>
        <motion.main
          id="main"
          tabIndex={-1}
          key={path}
          initial={{ opacity: reduced ? 1 : 0.65 }}
          animate={{ opacity: 1 }}
          transition={{ duration: reduced ? 0 : 0.16 }}
        >
          <AccessNotice />
          {isNew ? (
            <Intake />
          ) : isQueue ? (
            <ProposalLedger collection={queue} />
          ) : exampleId ? (
            <CuratedExamples id={exampleId} />
          ) : review ? (
            <ReviewPage
              kind={review[1] as "matters" | "matter-proposals"}
              id={decodeURIComponent(review[2])}
            />
          ) : path === "/app" || path === "" ? (
            <MatterLedger />
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
function useCompactLayout(query: string) {
  const [compact, setCompact] = useState(
    () => window.matchMedia(query).matches,
  );
  useEffect(() => {
    const media = window.matchMedia(query);
    const update = () => setCompact(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, [query]);
  return compact;
}
function Account() {
  const { access, refresh } = useAccess();
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
  useNavigationLock(busy);
  async function logout() {
    if (!mayLeave("/app")) return;
    setBusy(true);
    setError(undefined);
    try {
      await signOut();
      clearSessionState();
      refresh();
      setOpen(false);
      setBusy(false);
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
              href="/"
            >
              {t("Public showcase")}
            </a>
            {access?.can_write && <button disabled={busy} onClick={logout}>
              {t(busy ? "Signing out…" : "Sign out")}
            </button>}
            {!access?.can_write && <WriteGate />}
            {error !== undefined && <ErrorNotice error={error} />}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
