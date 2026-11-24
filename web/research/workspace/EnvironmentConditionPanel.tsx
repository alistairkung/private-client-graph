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
  researchDetails,
}: {
  family: string;
  observations: RunObservation[];
  context: FamilyResearchContext | undefined;
  activeCondition: RunObservation | undefined;
  selectCondition: (condition: string) => void;
  selectedEdgeKeys: Record<string, string>;
  setSelectedEdgeKey: (condition: string, edgeKey: string | null) => void;
  renderCondition: RenderCondition;
  researchDetails?: ReactNode;
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

  const condition = activeCondition?.benchmark;
  const single = observations.length === 1;
  const selector = single ? (
    <h4 id={`condition-tab-${condition?.condition}`} className="compact-condition-id">
      {condition?.condition} <span>{activeCondition && conditionRole(activeCondition)}</span>
    </h4>
  ) : (
    <div
      className="condition-tabs"
      role="tablist"
      aria-label={`Environment Conditions for Family ${family}`}
    >
      {observations.map((item, index) => {
        const id = item.benchmark?.condition ?? "";
        const selected = id === condition?.condition;
        return (
          <button
            key={id}
            id={`condition-tab-${id}`}
            type="button"
            role="tab"
            aria-selected={selected}
            aria-controls={`condition-panel-${id}`}
            tabIndex={selected ? 0 : -1}
            onClick={() => selectCondition(id)}
            onKeyDown={(event) =>
              handleTabKeyDown(event, observations, index, selectCondition)
            }
          >
            <span>{id}</span>
            <small>{conditionRole(item)}</small>
          </button>
        );
      })}
    </div>
  );

  return (
    <section
      className="condition-explorer redesigned-condition"
      aria-label={`Environment Conditions for Family ${family}`}
    >
      <div className="condition-workbench-header">
        <div className="condition-workbench-context">
          <div className="condition-workbench-selection">
            <span className="condition-workbench-label">
              {single ? "Environment Condition" : "Environment Conditions"}
            </span>
            {selector}
          </div>
          {condition && (
            <p className="condition-intent">
              {context?.condition_intents[condition.condition] ??
                condition.contrast ??
                "Condition research context unavailable."}
            </p>
          )}
        </div>
        {activeCondition && <ConditionFacts observation={activeCondition} />}
        {researchDetails && (
          <details className="condition-research-disclosure">
            <summary>Research details</summary>
            <div className="condition-research-content">{researchDetails}</div>
          </details>
        )}
      </div>

      {activeCondition && condition && (
        <div
          className="condition-panel"
          id={`condition-panel-${condition.condition}`}
          role={single ? "region" : "tabpanel"}
          aria-labelledby={`condition-tab-${condition.condition}`}
          tabIndex={0}
        >
          {renderCondition(
            activeCondition,
            selectedEdgeKeys[condition.condition] ?? null,
            (edgeKey) => setSelectedEdgeKey(condition.condition, edgeKey),
          )}
        </div>
      )}
    </section>
  );
}

function ConditionFacts({ observation }: { observation: RunObservation }) {
  const condition = observation.benchmark;
  if (!condition) return null;
  const { graph, metrics } = condition;
  return (
    <dl className="condition-facts">
      <div>
        <dt>Graph F1</dt>
        <dd>
          {graph ? (
            <>
              <strong>{metric(graph.f1)}</strong>
              <small>{formatF1Basis(graph.tp, graph.fp, graph.fn)}</small>
            </>
          ) : "Unavailable"}
        </dd>
      </div>
      <div>
        <dt>Complete proofs</dt>
        <dd>
          <strong>
            {metrics.planned_proofs
              ? `${metrics.complete_proofs}/${metrics.planned_proofs}`
              : "Unavailable"}
          </strong>
          <small>{metrics.planned_proofs ? "Annotated relationships" : "0 eligible"}</small>
        </dd>
      </div>
    </dl>
  );
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
