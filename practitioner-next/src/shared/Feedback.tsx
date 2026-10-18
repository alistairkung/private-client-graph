import { RequestFailure, existingPath } from "./api";
import { useLocale } from "./locale";
import { serviceMessages } from "./service-messages";
export function ErrorNotice({
  error,
  retry,
}: {
  error: unknown;
  retry?: () => void;
}) {
  const { t } = useLocale();
  const failure = error instanceof RequestFailure ? error : undefined;
  if (failure?.status === 401)
    return (
      <div className="notice error" role="alert">
        <h2>{t("Your session has expired")}</h2>
        <p>
          {t(
            "Sign in again to continue. Your current entries remain on this page.",
          )}
        </p>
        <a
          href={
            "/auth/login?next=" + encodeURIComponent(window.location.pathname)
          }
        >
          {t("Sign in")}
        </a>
      </div>
    );
  const detail = failure?.detail;
  const path = detail && existingPath(detail);
  const message =
    failure?.status === 403
      ? "This request was not allowed. Reload the page to restore your session."
      : detail
        ? Object.hasOwn(serviceMessages, detail.code)
          ? serviceMessages[detail.code]
          : "The request could not be completed. Check Matters before trying again."
        : "We could not load this workspace. Please try again.";
  return (
    <div className="notice error" role="alert">
      <p>{t(message)}</p>
      {detail?.outcome_unknown && (
        <p>
          {t(
            "The outcome is unknown. Check Matters before repeating this action. Your entries are preserved.",
          )}
        </p>
      )}
      {detail?.resets_at && (
        <p>
          {t("Available after: {time}", {
            time: new Date(detail.resets_at).toLocaleString(),
          })}
        </p>
      )}
      {path && <a href={path}>{t("Open existing record")}</a>}
      {retry && !detail?.outcome_unknown && detail?.retryable !== false && (
        <button onClick={retry}>{t("Try again")}</button>
      )}
      {detail?.outcome_unknown && <a href="/app">{t("Check Matters")}</a>}
    </div>
  );
}
export function Loading() {
  const { t } = useLocale();
  return (
    <div className="loading" role="status">
      <p>{t("Loading workspace…")}</p>
      <span />
      <span />
      <span />
    </div>
  );
}
export function NotFound({ proposal = false }: { proposal?: boolean }) {
  const { t } = useLocale();
  return (
    <section className="empty">
      <h1>{t(proposal ? "Matter Proposal not found" : "Matter not found")}</h1>
      <p>
        {t(
          "This record may no longer be available. Return to Matters to check its current state.",
        )}
      </p>
      <a className="button" href="/app">
        {t("Back to Matters")}
      </a>
    </section>
  );
}
