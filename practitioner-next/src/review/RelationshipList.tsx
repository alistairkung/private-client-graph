import { useLayoutEffect, useRef } from "react";
import { useSessionState } from "../shared/session-state";
import type { CanonicalState } from "../shared/contracts";
import { useLocale } from "../shared/locale";
import { relationshipLabels, relationshipStatement } from "./presentation";

export function RelationshipList({
  state,
  selected,
  entity,
  onSelect,
  onClear,
  memoryKey = "review:list",
}: {
  state: CanonicalState;
  selected: number | null;
  entity: string | null;
  onSelect: (index: number) => void;
  onClear: () => void;
  memoryKey?: string;
}) {
  const { t } = useLocale();
  const [query, setQuery] = useSessionState(memoryKey + ":query", "");
  const [scroll, setScroll] = useSessionState(memoryKey + ":list-scroll", 0);
  const list = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    if (list.current) list.current.scrollTop = scroll;
  }, []);
  const relationships = state.relationships
    .map((relationship, index) => ({ relationship, index }))
    .filter(
      ({ relationship }) =>
        (!entity ||
          relationship.source === entity ||
          relationship.target === entity) &&
        relationshipStatement(state, relationship, t)
          .toLocaleLowerCase()
          .includes(query.toLocaleLowerCase()),
    );
  return (
    <div className="relationship-list">
      <label className="relationship-search">
        <span className="sr-only">{t("Find relationship")}</span>
        <input
          type="search"
          placeholder={t("Find a person, trust or relationship")}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      {entity && (
        <button className="text-button" onClick={onClear}>
          {t("Show all relationships")}
        </button>
      )}
      <div
        className="relationship-list-scroll"
        ref={list}
        onScroll={(event) => setScroll(event.currentTarget.scrollTop)}
      >
        {relationships.map(({ relationship, index }) => (
          <button
            key={index}
            id={"relationship-" + index}
            className={
              "relationship-row " + (selected === index ? "active" : "")
            }
            aria-pressed={selected === index}
            onClick={() => onSelect(index)}
          >
            <span>
              {
                state.entities.find((item) => item.id === relationship.source)
                  ?.name
              }
            </span>
            <span className="relationship-type">
              {t(relationshipLabels[relationship.type])}
            </span>
            <span>
              {
                state.entities.find((item) => item.id === relationship.target)
                  ?.name
              }
            </span>
          </button>
        ))}
        {!relationships.length && (
          <p className="empty-row">{t("No matching relationships.")}</p>
        )}
      </div>
    </div>
  );
}
