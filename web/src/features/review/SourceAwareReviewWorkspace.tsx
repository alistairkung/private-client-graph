import "./review.css";
import "./source-aware-review.css";
import { useId, useMemo, useRef, useState } from "react";
import type { CanonicalState } from "../../shared/canonical-state";
import { EvidencePanel } from "./EvidencePanel";
import { RelationshipGraph } from "./RelationshipGraph";
import { SourcePanel } from "./SourcePanel";
import { presentRelationships } from "./relationship-presentation";
import { evidenceSource } from "./source-aware-review";

export function SourceAwareReviewWorkspace({ state, practitioner = false, graphTitle = "Relationships", emptyGraphTitle }: {
  state: CanonicalState; practitioner?: boolean; graphTitle?: string; emptyGraphTitle?: string;
}) {
  const [selected, setSelected] = useState<number | null>(null);
  const [activeId, setActiveId] = useState<string>();
  const [sourceId, setSourceId] = useState(state.sources[0]?.id);
  const [activation, setActivation] = useState(0);
  const [focus, setFocus] = useState(0);
  const highlightId = useId();
  const graphPanel = useRef<HTMLElement>(null);
  const presentation = useMemo(() => presentRelationships(state), [state]);
  const relationship = selected === null ? undefined : state.relationships[selected];
  const items = relationship?.evidence_ids.flatMap(id => state.evidence.filter(item => item.id === id)) ?? [];
  const active = items.find(item => item.id === activeId);
  const source = state.sources.find(item => item.id === sourceId) ?? state.sources[0];
  let span: { start: number; end: number } | undefined;
  let error: string | undefined;
  if (relationship && (items.length !== relationship.evidence_ids.length || !active)) {
    error = "The selected Evidence could not be found. Reload the case.";
  } else if (active) {
    try {
      const located = evidenceSource(state, active);
      if (source?.id === located.source.id) span = located.span;
    } catch (failure) {
      error = (failure as Error).message;
    }
  }
  function selectEvidence(id: string) {
    const evidence = state.evidence.find(item => item.id === id);
    setActiveId(id);
    if (evidence) setSourceId(evidence.source_id);
    setActivation(value => value + 1);
  }
  return <div className="source-aware-review">
    <nav className="source-selector" aria-label="Sources">
      <h3>Sources</h3>
      <ul>{state.sources.map((item, index) => <li key={item.id}>
        <button type="button" aria-pressed={source?.id === item.id} onClick={() => { setSourceId(item.id); setActivation(value => value + 1); }}>
          <span>Source {index + 1}</span> {item.title}
        </button>
      </li>)}</ul>
    </nav>
    <div className="review-workspace">
      <RelationshipGraph panelRef={graphPanel} graph={state} title={graphTitle} selected={selected} emptyTitle={emptyGraphTitle} onSelect={index => {
        setSelected(index); selectEvidence(state.relationships[index].evidence_ids[0]);
      }}>
        {error && <p role="alert">{error}</p>}
        <EvidencePanel items={items} practitioner={practitioner} activeId={activeId} onSelect={selectEvidence}
          relationship={selected === null ? undefined : presentation.relationships[selected].description}
          sourceLink={active && !error ? { id: highlightId, onActivate: () => { setSourceId(active.source_id); setFocus(value => value + 1); } } : undefined} />
        {active && <p className="evidence-attribution">Evidence from Source {state.sources.findIndex(item => item.id === active.source_id) + 1}: {state.sources.find(item => item.id === active.source_id)?.title}</p>}
      </RelationshipGraph>
      {source ? <SourcePanel practitioner={practitioner} title={source.title} source={source.text} span={span}
        activation={activation} highlightId={highlightId} focusRequest={focus} onReturn={() => {
          const button = graphPanel.current?.querySelector<HTMLButtonElement>(`button[data-edge-id="${selected}"]`);
          button?.focus(); button?.scrollIntoView({ block: "center" });
        }} /> : <p>No Sources available.</p>}
    </div>
  </div>;
}
