import { type KeyboardEvent, type ReactNode } from "react";
import type {
  FamilyResearchContext,
  RunObservation,
} from "../shared/contracts";
import { metric } from "./RunChart";
import { formatF1Basis } from "./benchmark-metrics";

export type RenderCondition = (
  observation: RunObservation,
  selectedEdgeKey: string | null,
  onSelectedEdgeChange: (edgeKey: string | null) => void,
) => ReactNode;

export function EnvironmentConditionPanel({
  family,
  observations,
  context,
  activeCondition,
  selectCondition,
  selectedEdgeKeys,
  setSelectedEdgeKey,
  renderCondition,
}: {
  family: string;
  observations: RunObservation[];
  context: FamilyResearchContext | undefined;
  activeCondition: RunObservation | undefined;
  selectCondition: (condition: string) => void;
  selectedEdgeKeys: Record<string, string>;
  setSelectedEdgeKey: (condition: string, edgeKey: string | null) => void;
  renderCondition: RenderCondition;
}) {
  if (observations.length === 0) {
    return (
      <section
        className="condition-explorer"
        aria-label={`Environment Conditions for Family ${family}`}
      >
        <h4>Environment Conditions</h4>
        <p>No Environment Conditions are available.</p>
      </section>
    );
  }

  return (
    <section
      className="condition-explorer"
      aria-label={`Environment Conditions for Family ${family}`}
    >
      <div className="condition-heading">
        <h4>Environment Conditions</h4>
        <span>
          {observations.length}{" "}
          {observations.length === 1 ? "condition" : "conditions"}
        </span>
      </div>
      <div
        className="condition-tabs"
        role="tablist"
        aria-label={`Environment Conditions for Family ${family}`}
      >
        {observations.map((item, index) => {
          const condition = item.benchmark?.condition ?? "";
          const selected =
            condition === activeCondition?.benchmark?.condition;
          return (
            <button
              key={condition}
              id={`condition-tab-${condition}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`condition-panel-${condition}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => selectCondition(condition)}
              onKeyDown={(event) =>
                handleTabKeyDown(event, observations, index, selectCondition)
              }
            >
              <span>{condition}</span>
              <small>{conditionRole(item)}</small>
            </button>
          );
        })}
      </div>

      {activeCondition?.benchmark && (
        <div
          className="condition-panel"
          id={`condition-panel-${activeCondition.benchmark.condition}`}
          role="tabpanel"
          aria-labelledby={`condition-tab-${activeCondition.benchmark.condition}`}
          tabIndex={0}
        >
          <p className="condition-intent">
            {context?.condition_intents[activeCondition.benchmark.condition] ??
              activeCondition.benchmark.contrast ??
              "Condition research context unavailable."}
          </p>
          <ConditionFacts observation={activeCondition} />
          {renderCondition(
            activeCondition,
            selectedEdgeKeys[activeCondition.benchmark.condition] ?? null,
            (edgeKey) =>
              setSelectedEdgeKey(
                activeCondition.benchmark!.condition,
                edgeKey,
              ),
          )}
        </div>
      )}
    </section>
  );
}

function ConditionFacts({ observation }: { observation: RunObservation }) {
  const condition = observation.benchmark;
  if (!condition) return null;
  const graphCounts = condition.metrics;
  const graphBasis = formatF1Basis(graphCounts.tp, graphCounts.fp, graphCounts.fn);

  return (
    <dl className="condition-facts">
      <div>
        <dt>Graph F1</dt>
        <dd>
          {condition.graph
            ? `${metric(condition.graph.f1)} · ${graphBasis}`
            : "Unavailable"}
        </dd>
      </div>
      <div>
        <dt>Complete proofs</dt>
        <dd>
          {proofCount(
            condition.metrics.complete_proofs,
            condition.metrics.planned_proofs,
          )}
        </dd>
      </div>
    </dl>
  );
}

export function proofCount(complete: number, planned: number) {
  return planned ? `${complete} of ${planned} complete` : "Unavailable · 0 eligible";
}

function conditionRole(observation: RunObservation) {
  if (observation.benchmark?.role === "natural") return "Natural";
  if (observation.benchmark?.role === "matched") return "Matched";
  return "Role unavailable";
}

function handleTabKeyDown(
  event: KeyboardEvent<HTMLButtonElement>,
  observations: RunObservation[],
  index: number,
  select: (condition: string) => void,
) {
  let nextIndex: number | undefined;
  if (event.key === "ArrowRight") nextIndex = (index + 1) % observations.length;
  if (event.key === "ArrowLeft")
    nextIndex = (index - 1 + observations.length) % observations.length;
  if (event.key === "Home") nextIndex = 0;
  if (event.key === "End") nextIndex = observations.length - 1;
  if (nextIndex === undefined) return;
  event.preventDefault();
  const condition = observations[nextIndex].benchmark?.condition;
  if (condition) select(condition);
  document.getElementById(`condition-tab-${condition}`)?.focus();
}
