import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { useLocale } from "../../../shared/locale";
import { RequestFailure } from "../../../shared/api";
import { Icon } from "../../../shared/Icon";
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
const recovery: Record<string, [string, string]> = {
  cancelled: ["Google access was cancelled.", "Connect again"],
  account: [
    "Choose the designated synthetic account.",
    "Choose the pilot account",
  ],
  permissions: [
    "Grant read-only access to both Gmail and Drive.",
    "Review permissions",
  ],
  invalid: [
    "The connection could not be verified. Connect again.",
    "Connect again",
  ],
  ended: [
    "Workspace access ended. Reconnect and review your Sources again.",
    "Reconnect",
  ],
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
  const prompt = Object.hasOwn(recovery, notice) ? recovery[notice] : undefined;
  const [error, setError] = useState<unknown>();
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const connectButton = useRef<HTMLButtonElement>(null);
  const wasConnected = useRef(false);
  const revision = useRef(0);
  const [search, setSearch] = useState(0);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      onBusy(false);
    };
  }, [onBusy]);
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
          // Status uses POST for privacy, but checking it has no mutation to replay.
          setError(
            failure instanceof RequestFailure && failure.status === 0
              ? new RequestFailure(0, {
                  code: "connection",
                  message: "",
                  retryable: true,
                })
              : failure,
          );
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
    if (!status) return;
    if (status.connected && !wasConnected.current) heading.current?.focus();
    if (!status.connected && (wasConnected.current || prompt || attempt > 0))
      connectButton.current?.focus();
    wasConnected.current = status.connected;
  }, [status?.connected, prompt, attempt]);
  async function connect() {
    setBusy(true);
    onBusy(true);
    setError(undefined);
    try {
      const { url } = await action<{ url: string }>("connect", {});
      if (mounted.current) window.location.assign(url);
    } catch (failure) {
      setError(failure);
      setBusy(false);
      if (mounted.current) onBusy(false);
    }
  }
  async function disconnect() {
    setBusy(true);
    onBusy(true);
    setError(undefined);
    try {
      await action("disconnect", {});
      ended();
      setNotice("");
    } catch (failure) {
      setError(failure);
    } finally {
      setBusy(false);
      if (mounted.current) onBusy(false);
    }
  }
  return (
    <>
      <section
        className={
          "workspace-connection" +
          (status?.connected
            ? " is-connected"
            : status
              ? " connection-setup"
              : "")
        }
        aria-busy={busy}
      >
        {status?.connected ? (
          <>
            <h2 ref={heading} tabIndex={-1}>
              {t("Workspace connected")}
            </h2>
            <p className="connection-account">
              {status.account} · {t("Read-only access for this session")}
            </p>
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
          </>
        ) : (
          status && (
            <>
              <div className="connection-intro">
                <h2>{t("Connect your Workspace")}</h2>
                <p>
                  {t(
                    "Use the synthetic account shown here to grant read-only access to Gmail and Drive for this session.",
                  )}
                </p>
              </div>
              <dl className="connection-scope">
                <div>
                  <dt>{t("Google account")}</dt>
                  <dd>{status.account}</dd>
                </div>
                <div>
                  <dt>{t("Drive folder")}</dt>
                  <dd>{status.folder_name}</dd>
                </div>
                <div>
                  <dt>{t("Gmail label")}</dt>
                  <dd>{status.label_name}</dd>
                </div>
              </dl>
              <div className="connection-action">
                <p>
                  {t(
                    "Only approved synthetic items in these locations can be searched.",
                  )}
                </p>
                {prompt && (
                  <p className="connection-recovery" role="status">
                    {t(prompt[0])}
                  </p>
                )}
                <button
                  className="button primary"
                  ref={connectButton}
                  disabled={busy}
                  onClick={connect}
                >
                  {t(prompt?.[1] ?? "Continue to Google")} <Icon name="arrow" />
                </button>
              </div>
            </>
          )
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
          key={status.generation + "/" + search}
          onBusy={onBusy}
          scope={status}
          onGrantLoss={ended}
          onStaleSearch={() => {
            setSearch((value) => value + 1);
            setAttempt((value) => value + 1);
          }}
        />
      )}
    </>
  );
}
