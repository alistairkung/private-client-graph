import "./review.css";
import { useCallback, useState } from "react";
import { EvidencePanel } from "./EvidencePanel";
import { GraphView } from "./GraphView";
import { SourcePanel } from "./SourcePanel";
import { locateEvidence } from "./graph-view";
import type { CanonicalGraph } from "../../shared/canonical-graph";

export function ReviewWorkspace({
  source,
  graph,
  sourceTitle,
  practitioner = false,
  embedded = false,
  graphTitle = "A connected view",
  emptyGraphTitle,
}: {
  source: string;
  sourceTitle?: string;
  practitioner?: boolean;
  embedded?: boolean;
  graphTitle?: string;
  emptyGraphTitle?: string;
  graph: CanonicalGraph;
}) {
  const [selected, setSelected] = useState<number | null>(null);
  const [activeId, setActiveId] = useState<string>();
  const [activation, setActivation] = useState(0);
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
      <section className="graph-panel panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Relationship review</p>
            <h2>{graphTitle}</h2>
          </div>
          {!practitioner && <span className="pill">
            {graph.relationships.length} relationships
          </span>}
        </div>
        <div className="graph-legend" aria-label="Graph legend">
          <span>
            <i className="person-key" /> Person
          </span>
          <span>
            <i className="trust-key" /> Trust
          </span>
          <span>
            <i className="role-key" /> Trust role · no flow implied
          </span>
          <span>
            <i className="directed-key" /> Parent → child
          </span>
          <span>
            <i className="symmetric-key" /> Spouse / sibling
          </span>
        </div>
        <GraphView
          embedded={embedded}
          graph={graph}
          selected={selected}
          onSelect={selectRelationship}
          emptyTitle={emptyGraphTitle}
        />
        {error && (
          <p role="alert" className="error-message">
            {error}
          </p>
        )}
        <EvidencePanel
          items={items}
          activeId={activeId}
          onSelect={setActiveId}
        />
      </section>
      <SourcePanel practitioner={practitioner} title={sourceTitle} source={source} span={span} activation={activation} />
    </div>
  );
}
