import { useState } from "react";
import type { RunDetail, RunObservation } from "../shared/contracts";
import { metric } from "./RunChart";
import { formatF1Basis } from "./benchmark-metrics";
import {
  EnvironmentConditionPanel,
  type RenderCondition,
} from "./EnvironmentConditionPanel";
import { FamilyResearchPanel } from "./FamilyResearchPanel";
import "./family-explorer.css";

type FamilyId = string;

export function BenchmarkFamilyExplorer({
  run,
  renderCondition,
}: {
  run: RunDetail;
  renderCondition: RenderCondition;
}) {
  const [openFamily, setOpenFamily] = useState<FamilyId | null>(null);
  const [search, setSearch] = useState("");
  const [activeConditions, setActiveConditions] = useState<
    Record<FamilyId, string>
  >({});
  const [selectedEdgeKeys, setSelectedEdgeKeys] = useState<
    Record<string, string>
  >({});

  const benchmark = run.benchmark;
  const familyContext = run.family_context;
  if (!benchmark) return null;

  const conditionOrder = new Map(
    benchmark.observations.map(({ condition }, index) => [condition, index]),
  );
  const conditionByFamily = new Map<string, RunObservation[]>();
  for (const observation of run.observations) {
    const family = observation.benchmark?.family;
    if (!family) continue;
    const observations = conditionByFamily.get(family) ?? [];
    observations.push(observation);
    conditionByFamily.set(family, observations);
  }
  for (const observations of conditionByFamily.values()) {
    observations.sort((left, right) => {
      const leftCondition = left.benchmark?.condition ?? "";
      const rightCondition = right.benchmark?.condition ?? "";
      return (
        (conditionOrder.get(leftCondition) ?? Number.MAX_SAFE_INTEGER) -
          (conditionOrder.get(rightCondition) ?? Number.MAX_SAFE_INTEGER) ||
        leftCondition.localeCompare(rightCondition)
      );
    });
  }

  const query = normalizeSearch(search);
  const families = Object.entries(benchmark.families)
    .sort(([left], [right]) => left.localeCompare(right, "en"))
    .filter(([family]) =>
      familyMatchesSearch(
        family,
        familyContext?.families[family],
        conditionByFamily.get(family) ?? [],
        familyContext?.axis_definitions ?? {},
        query,
      ),
    );

  function toggleFamily(family: string) {
    if (openFamily === family) {
      setOpenFamily(null);
      return;
    }
    const matchingCondition = query
      ? conditionByFamily
          .get(family)
          ?.find((observation) =>
            normalizeSearch(observation.benchmark?.condition ?? "").includes(
              query,
            ),
          )?.benchmark?.condition
      : undefined;
    if (matchingCondition) selectCondition(family, matchingCondition);
    setOpenFamily(family);
  }

  function selectCondition(family: string, condition: string) {
    setActiveConditions((previous) => ({ ...previous, [family]: condition }));
  }

  function setSelectedEdgeKey(condition: string, edgeKey: string | null) {
    setSelectedEdgeKeys((previous) => {
      const next = { ...previous };
      if (edgeKey === null) delete next[condition];
      else next[condition] = edgeKey;
      return next;
    });
  }

  return (
    <section className="family-explorer" aria-label="Benchmark Families">
      <div className="family-explorer-heading">
        <h3>Benchmark Families</h3>
        <span>{Object.keys(benchmark.families).length} families</span>
      </div>

      <label className="family-search">
        <span>Find a family or Environment Condition</span>
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="For example, E001"
          aria-label="Find a family or Environment Condition"
        />
      </label>

      {!familyContext && (
        <p className="family-context-unavailable" role="status">
          Research context unavailable for this Run.
        </p>
      )}

      <div className="family-roster">
        {families.map(([family, scores]) => {
          const context = familyContext?.families[family];
          const observations = conditionByFamily.get(family) ?? [];
          const firstNatural =
            observations.find(
              (observation) => observation.benchmark?.role === "natural",
            ) ?? observations[0];
          const activeCondition =
            observations.find(
              (observation) =>
                observation.benchmark?.condition === activeConditions[family],
            ) ?? firstNatural;
          const expanded = openFamily === family;
          const panelId = `family-panel-${family}`;

          return (
            <FamilyRow
              key={family}
              family={family}
              scores={scores}
              context={context}
              axisDefinitions={familyContext?.axis_definitions ?? {}}
              observations={observations}
              activeCondition={activeCondition}
              expanded={expanded}
              panelId={panelId}
              selectCondition={(condition) =>
                selectCondition(family, condition)
              }
              selectedEdgeKeys={selectedEdgeKeys}
              setSelectedEdgeKey={setSelectedEdgeKey}
              renderCondition={renderCondition}
              toggle={() => toggleFamily(family)}
            />
          );
        })}
        {families.length === 0 && (
          <p role="status" className="family-no-results">
            No family or Environment Condition matches “{search}”.
          </p>
        )}
      </div>
    </section>
  );
}

function FamilyRow({
  family,
  scores,
  context,
  axisDefinitions,
  observations,
  activeCondition,
  expanded,
  panelId,
  selectCondition,
  selectedEdgeKeys,
  setSelectedEdgeKey,
  renderCondition,
  toggle,
}: {
  family: string;
  scores: NonNullable<RunDetail["benchmark"]>["families"][string];
  context:
    NonNullable<RunDetail["family_context"]>["families"][string] | undefined;
  axisDefinitions: Record<string, string>;
  observations: RunObservation[];
  activeCondition: RunObservation | undefined;
  expanded: boolean;
  panelId: string;
  selectCondition: (condition: string) => void;
  selectedEdgeKeys: Record<string, string>;
  setSelectedEdgeKey: (condition: string, edgeKey: string | null) => void;
  renderCondition: RenderCondition;
  toggle: () => void;
}) {
  const outcomes = scores.all_conditions;
  const f1Basis = formatF1Basis(outcomes.tp, outcomes.fp, outcomes.fn);
  const conditionRepeatsFamilyScores =
    expanded && observations.length === 1 &&
    activeCondition?.benchmark?.outcome === "scored";

  return (
    <article className={`family-row${expanded ? " is-expanded" : ""}`}>
      <button
        className={`family-row-trigger${conditionRepeatsFamilyScores ? " family-row-trigger-compact" : ""}`}
        type="button"
        aria-expanded={expanded}
        aria-controls={panelId}
        id={`family-trigger-${family}`}
        onClick={toggle}
      >
        <span className="family-row-main">
          <span className="family-row-id">Family {family}</span>
          <span className="family-row-description">
            {context?.description ??
              "Family description unavailable for this Run."}
          </span>
          <span className="family-row-axis">
            <span>Primary difficulty</span>
            <strong>
              {context ? axisLabel(context.primary_axis) : "Unavailable"}
            </strong>
          </span>
        </span>
        {!conditionRepeatsFamilyScores && <span className="family-row-metrics">
          <span className="family-metric">
            <span>Graph F1</span>
            <strong>{metric(scores.all_condition_micro_f1)}</strong>
            <small>{f1Basis}</small>
          </span>
          <span className="family-metric">
            <span>Complete proofs</span>
            <strong>
              {scores.planned_proofs
                ? `${scores.complete_proofs}/${scores.planned_proofs}`
                : "Unavailable"}
            </strong>
            <small>
              {!scores.planned_proofs
                ? "0 eligible"
                : scores.complete_proofs === 0
                  ? "None complete"
                  : "Annotated relationships"}
            </small>
          </span>
        </span>}
        <span
          className={`family-row-disclosure${expanded ? " is-expanded" : ""}`}
          aria-hidden="true"
        >
          <svg viewBox="0 0 16 16" focusable="false">
            <path d="m5 3 6 5-6 5" />
          </svg>
        </span>
      </button>

      <div
        className="family-panel-region"
        id={panelId}
        aria-labelledby={`family-trigger-${family}`}
        hidden={!expanded}
      >
        {expanded && (
          <div className="family-panel">
            <EnvironmentConditionPanel
              family={family}
              observations={observations}
              context={context}
              activeCondition={activeCondition}
              selectCondition={selectCondition}
              selectedEdgeKeys={selectedEdgeKeys}
              setSelectedEdgeKey={setSelectedEdgeKey}
              renderCondition={renderCondition}
              researchDetails={
                <>
                  <FamilyResearchPanel
                    context={context}
                    axisDefinitions={axisDefinitions}
                  />
                  <dl className="family-expanded-metrics">
                    <div>
                      <dt>Construction coverage</dt>
                      <dd>
                        {scores.valid_graphs} of {scores.planned_conditions} valid
                      </dd>
                    </div>
                    <div>
                      <dt>Exact graphs</dt>
                      <dd>
                        {scores.exact_graphs} of {scores.planned_conditions}
                      </dd>
                    </div>
                  </dl>
                </>
              }
            />
            <button
              type="button"
              className="secondary close-family"
              onClick={() => {
                toggle();
                document.getElementById(`family-trigger-${family}`)?.focus();
              }}
            >
              Close Family {family}
            </button>
          </div>
        )}
      </div>
    </article>
  );
}

function familyMatchesSearch(
  family: string,
  context:
    NonNullable<RunDetail["family_context"]>["families"][string] | undefined,
  observations: RunObservation[],
  axisDefinitions: Record<string, string>,
  query: string,
) {
  if (!query) return true;
  const axisTerms = context
    ? [
        context.primary_axis,
        axisLabel(context.primary_axis),
        axisDefinitions[context.primary_axis],
        ...(context.secondary_axes ?? []).flatMap((axis) => [
          axis,
          axisLabel(axis),
          axisDefinitions[axis],
        ]),
      ]
    : [];
  const searchableText = [
    family,
    context?.description,
    ...axisTerms,
    ...observations.map((item) => item.benchmark?.condition),
  ]
    .filter((value): value is string => Boolean(value))
    .map(normalizeSearch);
  return searchableText.some((value) => value.includes(query));
}

function normalizeSearch(value: string) {
  return value.trim().toLocaleLowerCase().replace(/\s+/g, " ");
}

function axisLabel(axis: string) {
  return axis
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
