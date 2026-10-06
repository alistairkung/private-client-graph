import type { Evidence } from "../../shared/canonical-graph";

export function EvidencePanel({
  items,
  practitioner = false,
  activeId,
  onSelect,
  relationship,
  sourceLink,
}: {
  items: Evidence[];
  practitioner?: boolean;
  activeId?: string;
  onSelect: (id: string) => void;
  relationship?: string;
  sourceLink?: { id: string; onActivate: () => void };
}) {
  return (
    <section className="evidence-panel" aria-label="Supporting evidence">
      <h3>{relationship ?? "Supporting evidence"}</h3>
      {items.length ? (
        <div className="evidence-list">
          {items.map((item, index) => (
            <button
              key={item.id}
              className="evidence-choice"
              aria-pressed={activeId === item.id}
              onClick={() => onSelect(item.id)}
            >
              <span className="evidence-number">Evidence {index + 1}</span>
              <q>{item.supporting_text}</q>
            </button>
          ))}
        </div>
      ) : (
        <p>Select a relationship to follow its evidence into the source.</p>
      )}
      {sourceLink && <a className="evidence-source-link" href={`#${sourceLink.id}`} onClick={event => {
        event.preventDefault();
        sourceLink.onActivate();
      }}>View in source</a>}
    </section>
  );
}
