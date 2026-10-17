import { useLocale } from "../../shared/locale";
import { useEffect, useState } from "react";
import { getMatters } from "./api";
import type { MatterSummary } from "./types";

type CollectionState =
  | { status: "loading" }
  | { status: "failed" }
  | { status: "ready"; matters: MatterSummary[] };

export function MatterLedger() {
  const { t } = useLocale();
  const [state, setState] = useState<CollectionState>({ status: "loading" });
  useEffect(() => {
    let active = true;
    getMatters().then(
      matters => { if (active) setState({ status: "ready", matters }); },
      () => { if (active) setState({ status: "failed" }); },
    );
    return () => { active = false; };
  }, []);

  return (
    <table className="matter-register" aria-label={t("Matters")}>
      <thead>
        <tr><th scope="col">{t("Matter reference")}</th><th scope="col">{t("Matter")}</th></tr>
      </thead>
      <tbody>
        {state.status === "ready" && state.matters.length > 0
          ? state.matters.map(matter => (
            <tr key={matter.id}>
              <td colSpan={2}>
                <a
                  href={`/app/matters/${matter.id}`}
                  className="matter-row"
                >
                  <span className="matter-reference">{matter.external_reference}</span>
                  <span className="matter-title">{matter.title}</span>
                </a>
              </td>
            </tr>
          ))
          : <tr><td colSpan={2}><CollectionMessage state={state} /></td></tr>}
      </tbody>
    </table>
  );
}

function CollectionMessage({ state }: { state: CollectionState }) {
  const { t } = useLocale();
  if (state.status === "loading") {
    return <div className="ledger-empty" role="status">{t("Loading Matters…")}</div>;
  }
  if (state.status === "failed") {
    return <div className="ledger-empty" role="alert">
      <p>{t("Matters could not be loaded.")}</p>
      <p>{t("Reload the page to try again.")}</p>
      <button onClick={() => window.location.reload()}>{t("Reload page")}</button>
    </div>;
  }
  return <div className="ledger-empty">
    <p>{t("No accepted Matters yet")}</p>
    <p>{t("Accepted Matters will appear here.")}</p>
  </div>;
}
