import { useLocale } from "../../shared/locale";
import { useEffect, useLayoutEffect, useState } from "react";
import { getMatter } from "./api";
import type { MatterDetail } from "./types";
import { ReviewWorkspace } from "../review/ReviewWorkspace";
import { SourceAwareReviewWorkspace } from "../review/SourceAwareReviewWorkspace";
import { consumeMatterCreation } from "./creation-notice";

type MatterState =
  | { status: "loading" | "missing" | "failed" }
  | { status: "ready"; matter: MatterDetail };

export function MatterWorkspace({ id }: { id: string }) {
  const { t } = useLocale();
  const [state, setState] = useState<MatterState>({ status: "loading" });
  const [created, setCreated] = useState(false);
  useEffect(() => {
    let active = true;
    getMatter(id).then(
      matter => {
        if (!active) return;
        setState(matter ? { status: "ready", matter } : { status: "missing" });
        if (matter) setCreated(consumeMatterCreation(id));

      },
      () => { if (active) setState({ status: "failed" }); },
    );
    return () => { active = false; };
  }, [id]);

  useLayoutEffect(() => {
    document.title = `${state.status === "ready" ? state.matter.title : t("Matter not found")} · Private Client Graph`;
  }, [state, t]);

  return <>
    <a className="matter-back" href="/app">{t("Back to Matters")}</a>
    {state.status === "ready" ? <>
      <header className="matter-context">
        <h1>{state.matter.title}</h1>
        <p>{t("Matter reference: {reference}", { reference: state.matter.external_reference })}</p>
      </header>
      {created && <p className="matter-created" role="status">{t("Matter created. The whole proposal is now accepted current Matter state.")}</p>}
      {state.matter.state ? <SourceAwareReviewWorkspace key={id} state={state.matter.state}
        graphTitle={t("Accepted relationships")} practitioner />
        : state.matter.authoritative_source ? <ReviewWorkspace
        source={state.matter.authoritative_source.text}
        sourceTitle={state.matter.authoritative_source.title}
        graph={state.matter.current_graph}
        graphTitle={t("Accepted relationships")}
        practitioner
      /> : <p role="alert">{t("The complete Source state is unavailable. Reload to try again.")}</p>}
    </> : state.status === "loading" ? <p role="status">{t("Loading Matter…")}</p> :
      <div role="alert">
        <h1>{state.status === "missing" ? t("Matter not found") : t("Matter could not be loaded.")}</h1>
        <p>{state.status === "missing" ? t("Return to Matters to choose an available Matter.") : t("Reload the page to try again.")}</p>
      </div>}
  </>;
}
