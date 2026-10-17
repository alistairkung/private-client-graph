import { useLocale } from "../../shared/locale";
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
  const { t } = useLocale();
  return <section className="graph-panel panel" ref={panelRef} aria-label={t(title)}>
    <div className="panel-heading"><h2>{t(title)}</h2></div>
    <div className="graph-legend" aria-label={t("Graph legend")}>
      <span><i className="person-key" /> {t("Person")}</span>
      <span><i className="trust-key" /> {t("Trust")}</span>
      <span><i className="role-key" /> {t("Trust role \u00b7 no flow implied")}</span>
      <span><i className="directed-key" /> {t("Parent \u2192 child")}</span>
      <span><i className="symmetric-key" /> {t("Spouse / sibling")}</span>
    </div>
    <GraphView graph={graph} selected={selected} onSelect={onSelect} emptyTitle={emptyTitle} />
    {children}
  </section>;
}
