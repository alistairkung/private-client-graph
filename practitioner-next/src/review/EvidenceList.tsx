import type { CanonicalState, Relationship } from "../shared/contracts";
import { useLocale } from "../shared/locale";
import { Icon } from "../shared/Icon";

export function EvidenceList({
  state,
  relationship,
  evidenceId,
  onSelect,
}: {
  state: CanonicalState;
  relationship: Relationship;
  evidenceId: string | null;
  onSelect: (id: string) => void;
}) {
  const { t } = useLocale();
  return (
    <div className="evidence-list">
      {relationship.evidence_ids.map((id, index) => {
        const item = state.evidence.find((evidence) => evidence.id === id);
        const source = state.sources.find(
          (source) => source.id === item?.source_id,
        );
        return (
          <button
            key={id}
            className={"evidence-item " + (evidenceId === id ? "active" : "")}
            aria-pressed={evidenceId === id}
            onClick={() => onSelect(id)}
          >
            <span className="evidence-meta">
              <strong>
                {t("Evidence {number} of {total}", {
                  number: index + 1,
                  total: relationship.evidence_ids.length,
                })}
              </strong>
              <span>{id}</span>
            </span>
            {source && <span className="evidence-source">{source.title}</span>}
            {item ? (
              <q>{item.supporting_text}</q>
            ) : (
              <span className="error-text">
                {t("This Evidence item could not be found.")}
              </span>
            )}
            {item && !source && (
              <span className="error-text">
                {t(
                  "The Evidence source could not be found. Select a source to continue.",
                )}
              </span>
            )}
            <span className="evidence-jump">
              {t("View in source")}
              <Icon name="arrow" />
            </span>
          </button>
        );
      })}
    </div>
  );
}
