import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { useLocale } from "../../../shared/locale";
import { ErrorNotice } from "../../../shared/Feedback";
import { action } from "./api";
import { WorkspaceDiscovery } from "./WorkspaceDiscovery";

interface Status {
  connected: boolean;
  generation: string | null;
  expires: number | null;
  account: string;
  label: string;
  folder: string;
  label_name: string;
  folder_name: string;
}
const messages: Record<string, string> = {
  cancelled: "Google access was cancelled.",
  account: "Choose the designated synthetic account.",
  permissions: "Grant read-only access to both Gmail and Drive.",
  invalid: "The connection could not be verified. Connect again.",
  ended: "Workspace access ended. Reconnect and review your Sources again.",
};

export function WorkspaceConnection({
  onBusy,
}: {
  onBusy: (value: boolean) => void;
}) {
  const { t } = useLocale();
  const reduced = useReducedMotion();
  const [status, setStatus] = useState<Status>();
  const [notice, setNotice] = useState(
    () => new URLSearchParams(location.search).get("workspace") || "",
  );
  const [error, setError] = useState<unknown>();
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const revision = useRef(0);
  function ended() {
    revision.current++;
    setStatus(
      (old) =>
        old && { ...old, connected: false, generation: null, expires: null },
    );
    setNotice("ended");
    onBusy(false);
  }
  useEffect(() => {
    let active = true;
    async function refresh() {
      const ticket = ++revision.current;
      try {
        const current = await action<Status>("connection", {});
        if (active && ticket === revision.current) {
          setStatus((old) => {
            if (old?.connected && !current.connected) setNotice("ended");
            return current;
          });
          setError(undefined);
        }
      } catch (failure) {
        if (active && ticket === revision.current) {
          setStatus(undefined);
          setError(failure);
        }
      }
    }
    void refresh();
    window.addEventListener("focus", refresh);
    return () => {
      active = false;
      window.removeEventListener("focus", refresh);
    };
  }, [attempt]);
  useEffect(() => {
    if (!status?.expires) return;
    const timer = window.setTimeout(
      ended,
      Math.max(0, status.expires * 1000 - Date.now()),
    );
    return () => window.clearTimeout(timer);
  }, [status?.expires]);
  useEffect(() => {
    if (status) heading.current?.focus();
  }, [status?.connected]);
  async function connect() {
    setBusy(true);
    setError(undefined);
    try {
      const { url } = await action<{ url: string }>("connect", {});
      window.location.assign(url);
    } catch (failure) {
      setError(failure);
      setBusy(false);
    }
  }
  async function disconnect() {
    setBusy(true);
    setError(undefined);
    try {
      await action("disconnect", {});
      ended();
      setNotice("");
    } catch (failure) {
      setError(failure);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <section className="intake-form workspace-connection" aria-busy={busy}>
        <h2 ref={heading} tabIndex={-1}>
          {t(
            status?.connected
              ? "Workspace connected"
              : "Connect Google Workspace",
          )}
        </h2>
        {status && (
          <>
            <p>
              {status.account} · {t("Read-only access for this session")}
            </p>
            {status.connected ? (
              <motion.div
                key="connected"
                initial={{ opacity: reduced ? 1 : 0.4 }}
                animate={{ opacity: 1 }}
                transition={{ duration: reduced ? 0 : 0.16 }}
              >
                <button disabled={busy} onClick={disconnect}>
                  {t("Disconnect")}
                </button>
              </motion.div>
            ) : (
              <>
                <p>
                  {t(
                    "Google will request read-only access to Gmail and Drive. PCG searches only approved synthetic items in these locations.",
                  )}
                </p>
                <p>
                  {t("Drive folder")} · {status.folder_name}
                  <br />
                  {t("Gmail label")} · {status.label_name}
                </p>
                <p role="status">{Object.hasOwn(messages, notice) && t(messages[notice])}</p>
                <button
                  className="button primary"
                  disabled={busy}
                  onClick={connect}
                >
                  {t(
                    notice === "ended"
                      ? "Reconnect"
                      : "Connect Google Workspace",
                  )}
                </button>
              </>
            )}
          </>
        )}
        {!status && !error && (
          <p role="status">{t("Checking Workspace access…")}</p>
        )}
        {!!error && (
          <ErrorNotice error={error} retry={() => setAttempt((v) => v + 1)} />
        )}
      </section>
      {status?.connected && (
        <WorkspaceDiscovery
          key={status.generation}
          onBusy={onBusy}
          scope={status}
          onGrantLoss={ended}
        />
      )}
    </>
  );
}
