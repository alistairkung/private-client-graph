import type { ReactNode, Ref } from "react";
import type { CanonicalGraph } from "../../shared/canonical-graph";
import { GraphView } from "./GraphView";

// Shared review surface for the landing demo, saved proposals, and accepted Matters.
export function RelationshipGraph({ graph, title, emptyTitle, selected, onSelect, panelRef, children }: {
  graph: CanonicalGraph;
  title: string;
  emptyTitle?: string;
  selected: number | null;
  onSelect: (index: number) => void;
  panelRef: Ref<HTMLElement>;
  children: ReactNode;
}) {
  return <section className="graph-panel panel" ref={panelRef} aria-label={title}>
    <div className="panel-heading"><h2>{title}</h2></div>
    <div className="graph-legend" aria-label="Graph legend">
      <span><i className="person-key" /> Person</span>
      <span><i className="trust-key" /> Trust</span>
      <span><i className="role-key" /> Trust role · no flow implied</span>
      <span><i className="directed-key" /> Parent → child</span>
      <span><i className="symmetric-key" /> Spouse / sibling</span>
    </div>
    <GraphView graph={graph} selected={selected} onSelect={onSelect} emptyTitle={emptyTitle} />
    {children}
  </section>;
}
