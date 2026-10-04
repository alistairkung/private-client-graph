import type { Evidence } from "./types";

export function EvidencePanel({
  items,
  practitioner = false,
  activeId,
  onSelect,
}: {
  items: Evidence[];
  practitioner?: boolean;
  activeId?: string;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="evidence-panel" aria-label="Supporting evidence">
      <p className="eyebrow">{practitioner ? "Supporting evidence" : "SUPPORTING EVIDENCE"}</p>
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
    </section>
  );
}
