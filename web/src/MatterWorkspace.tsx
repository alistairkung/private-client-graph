import { useEffect, useState } from "react";
import { getMatter, type MatterDetail } from "./matters-api";
import { ReviewWorkspace } from "./ReviewWorkspace";

type MatterState =
  | { status: "loading" | "missing" | "failed" }
  | { status: "ready"; matter: MatterDetail };

export function MatterWorkspace({ id }: { id: string }) {
  const [state, setState] = useState<MatterState>({ status: "loading" });
  useEffect(() => {
    let active = true;
    getMatter(id).then(
      matter => {
        if (!active) return;
        setState(matter ? { status: "ready", matter } : { status: "missing" });
        document.title = `${matter?.title ?? "Matter not found"} · Private Client Graph`;
      },
      () => { if (active) setState({ status: "failed" }); },
    );
    return () => { active = false; };
  }, [id]);

  return <>
    <a className="matter-back" href="/app">Back to Matters</a>
    {state.status === "ready" ? <>
      <header className="matter-context">
        <h1>{state.matter.title}</h1>
        <p>Matter reference: {state.matter.external_reference}</p>
      </header>
      <ReviewWorkspace
        source={state.matter.authoritative_source.text}
        sourceTitle={state.matter.authoritative_source.title}
        graph={state.matter.current_graph}
        practitioner
      />
    </> : state.status === "loading" ? <p role="status">Loading Matter…</p> :
      <div role="alert">
        <h1>{state.status === "missing" ? "Matter not found" : "Matter could not be loaded."}</h1>
        <p>{state.status === "missing" ? "Return to Matters to choose an available Matter." : "Reload the page to try again."}</p>
      </div>}
  </>;
}
