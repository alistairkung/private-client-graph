import "./review.css";
import { useCallback, useId, useMemo, useRef, useState } from "react";
import { EvidencePanel } from "./EvidencePanel";
import { RelationshipGraph } from "./RelationshipGraph";
import { SourcePanel } from "./SourcePanel";
import { locateEvidence } from "./graph-view";
import type { CanonicalGraph } from "../../shared/canonical-graph";
import { presentRelationships } from "./relationship-presentation";

export function ReviewWorkspace({
  source,
  graph,
  sourceTitle,
  practitioner = false,
  graphTitle = "A connected view",
  emptyGraphTitle,
}: {
  source: string;
  sourceTitle?: string;
  practitioner?: boolean;
  graphTitle?: string;
  emptyGraphTitle?: string;
  graph: CanonicalGraph;
}) {
  const [selected, setSelected] = useState<number | null>(null);
  const [activeId, setActiveId] = useState<string>();
  const [activation, setActivation] = useState(0);
  const [sourceFocus, setSourceFocus] = useState(0);
  const highlightId = useId();
  const graphPanel = useRef<HTMLElement>(null);
  const presentation = useMemo(() => presentRelationships(graph), [graph]);
  const relationship =
    selected === null ? undefined : graph.relationships[selected];
  const items =
    relationship?.evidence_ids
      .map((id) => graph.evidence.find((item) => item.id === id))
      .filter((item) => item !== undefined) ?? [];
  const active = items.find((item) => item.id === activeId);
  let span: { start: number; end: number } | undefined;
  let error: string | undefined;
  if (
    relationship &&
    (items.length !== relationship.evidence_ids.length || !active)
  ) {
    error =
      "The selected evidence could not be located in the source. Reload the case to restore the review.";
  } else if (active) {
    try {
      span = locateEvidence(source, active.supporting_text);
    } catch (failure) {
      error = (failure as Error).message;
    }
  }
  const selectRelationship = useCallback(
    (index: number) => {
      setActivation((value) => value + 1);
      setSelected(index);
      setActiveId(graph.relationships[index].evidence_ids[0]);
    },
    [graph],
  );
  return (
    <div className="review-workspace">
      <RelationshipGraph graph={graph} title={graphTitle} selected={selected}
        onSelect={selectRelationship} emptyTitle={emptyGraphTitle} panelRef={graphPanel}>
        {error && (
          <p role="alert" className="error-message">
            {error}
          </p>
        )}
        <EvidencePanel
          practitioner={practitioner}
          items={items}
          activeId={activeId}
          onSelect={setActiveId}
          relationship={selected === null ? undefined : presentation.relationships[selected].description}
          sourceLink={span ? { id: highlightId, onActivate: () => setSourceFocus(value => value + 1) } : undefined}
        />
      </RelationshipGraph>
      <SourcePanel practitioner={practitioner} title={sourceTitle} source={source} span={span}
        activation={activation} highlightId={highlightId} focusRequest={sourceFocus}
        onReturn={() => {
          const button = graphPanel.current?.querySelector<HTMLButtonElement>(`button[data-edge-id="${selected}"]`);
          button?.focus();
          button?.scrollIntoView({ block: "center" });
        }} />
    </div>
  );
}
