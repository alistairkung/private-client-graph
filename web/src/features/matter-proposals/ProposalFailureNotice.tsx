import type { ProposalError } from "./types";
import { useEffect, useRef } from "react";

export function ProposalFailureNotice({ error }: { error: ProposalError }) {
  const alert = useRef<HTMLDivElement>(null);
  useEffect(() => { alert.current?.focus(); }, [error]);
  return <div className="intake-error" role="alert" tabIndex={-1} ref={alert}>
    <p>{error.message}</p>
    {error.resets_at && <p>Analysis is available again after <time dateTime={error.resets_at}>{new Date(error.resets_at).toLocaleString()}</time>.</p>}
    {error.outcome_unknown && <p><a href="/app">Check Matters and proposals</a></p>}
    {error.code === "authentication" && <p><a href="/auth/login?next=%2Fapp%2Fmatter-proposals%2Fnew">Sign in again</a></p>}
  </div>;
}
