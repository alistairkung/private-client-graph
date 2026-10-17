import { useLocale } from "../../shared/locale";
import { proposalFailureMessage } from "./error-presentation";
import type { ProposalError } from "./types";
import { useEffect, useRef } from "react";

export function ProposalFailureNotice({ error }: { error: ProposalError }) {
  const { t, locale } = useLocale();
  const alert = useRef<HTMLDivElement>(null);
  useEffect(() => { alert.current?.focus(); }, [error]);
  return <div className="intake-error" role="alert" tabIndex={-1} ref={alert}>
    <p>{t(proposalFailureMessage(error))}</p>
    {error.resets_at && <p>{t("Analysis is available again after")} <time dateTime={error.resets_at}>{new Date(error.resets_at).toLocaleString(locale)}</time>.</p>}
    {error.outcome_unknown && <p><a href="/app">{t("Check Matters and proposals")}</a></p>}
    {error.code === "authentication" && <p><a href="/auth/login?next=%2Fapp%2Fmatter-proposals%2Fnew">{t("Sign in again")}</a></p>}
  </div>;
}
