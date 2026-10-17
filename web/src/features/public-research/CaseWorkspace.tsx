import { OutcomeMatrix } from "../../shared/research/OutcomeMatrix";
import { useId, useLayoutEffect, useRef, useState } from "react";
import { useLocale } from "../../shared/locale";
import { SourcePanel } from "../review/SourcePanel";
import { percent, runName } from "./RunComparison";
import type {
  PublicCase,
  PublicObservation,
  PublicOutcome,
  PublicQuote,
  RunLabel,
} from "./types";
type Selection = { run: RunLabel; outcomeId: string };
type Filter =
  | "all"
  | "errors"
  | "missing"
  | "extra"
  | "provenance_failure"
  | "source_attribution_failure";
export function CaseWorkspace({ cases }: { cases: PublicCase[] }) {
  const { t } = useLocale();
  const sourceSelectId = useId();
  const [caseId, setCaseId] = useState("");
  const [caseNavigation, setCaseNavigation] = useState(0);
  const caseHeading = useRef<HTMLHeadingElement>(null);
  useLayoutEffect(() => {
    if (!caseNavigation) return;
    caseHeading.current?.focus({ preventScroll: true });
    caseHeading.current?.scrollIntoView({ behavior: "instant", block: "start" });
  }, [caseNavigation]);
  const [baseline, setBaseline] = useState<RunLabel>("A_prime");
  const [filter, setFilter] = useState<Filter>("all");
  const [selection, setSelection] = useState<Selection | null>(null);
  const [quote, setQuote] = useState<PublicQuote | null>(null);
  const [sourceId, setSourceId] = useState("");
  const [occurrence, setOccurrence] = useState(0);
  const selectedCase = cases.find((item) => item.case_id === caseId);
  const observation = selectedCase?.observations.find(
    (item) => item.run_label === selection?.run,
  );
  const outcome = observation?.relationships.find(
    (item) => item.id === selection?.outcomeId,
  );
  const attributionFailures = outcome
    ? sourcePairFailures(observation, outcome)
    : [];
  const source =
    selectedCase?.sources.find((item) => item.id === sourceId) ??
    selectedCase?.sources[0];
  const edits =
    selectedCase?.observations.find((item) => item.run_label === "B")?.edits ??
    [];
  function selectCase(id: string) {
    setCaseId(id);
    setCaseNavigation((previous) => previous + 1);
    setSelection(null);
    setQuote(null);
    setSourceId("");
    setOccurrence(0);
  }
  function selectQuote(value: PublicQuote) {
    setQuote(value);
    setSourceId(value.source_id);
    setOccurrence(0);
  }
  function selectOutcome(run: RunLabel, value: PublicOutcome) {
    setSelection({ run, outcomeId: value.id });
    const evidence = value.predicted[0] ?? value.expected[0];
    if (evidence) selectQuote(evidence);
    else setQuote(null);
  }
  function selectEdit(index: number) {
    const edit = edits[index];
    const target = selectedCase?.observations
      .find((item) => item.run_label === "B")
      ?.relationships.find((item) => item.id === edit.outcome_id);
    if (!target) return;
    selectOutcome("B", target);
    const evidence = target.predicted.find(
      (item) =>
        item.source_id === edit.source_id && item.text === edit.supporting_text,
    );
    if (evidence) selectQuote(evidence);
  }
  const recordedSpan =
    quote?.source_id === source?.id
      ? quote?.occurrences[occurrence]
      : undefined;
  const codepoints = Array.from(source?.text ?? "");
  const span = recordedSpan
    ? {
        start: codepoints.slice(0, recordedSpan[0]).join("").length,
        end: codepoints.slice(0, recordedSpan[1]).join("").length,
      }
    : undefined;
  return (
    <section id="cases" className="research-section">
      <div className="research-section-title">
        <h2>{t("Follow the recorded difference")}</h2>
        <button
          onClick={() => {
            selectCase("heldout_03");
            setFilter("all");
          }}
        >
          {t("Inspect the two corrections")}
        </button>
      </div>
      <p>
        {t(
          "Choose any case to inspect retained outcomes. The paired view compares A′ with B; the original A baseline remains available. No case is selected by default.",
        )}
      </p>
      <div className="research-workspace">
        <nav className="research-case-index" aria-label={t("Benchmark cases")}>
          {cases.map((item) => (
            <button
              key={item.case_id}
              aria-pressed={caseId === item.case_id}
              onClick={() => selectCase(item.case_id)}
            >
              <strong>{item.case_id}</strong>
              <span>{item.name}</span>
              <small>
                {item.observations.some((value) => value.edits.length)
                  ? t("Recorded endpoint edits")
                  : t("Unchanged relationship results")}
              </small>
              {item.observations.map((value) => (
                <small key={value.run_label}>
                  {runName(value.run_label)} · {t("F1")}{" "}
                  {percent(value.evaluation.f1)}
                </small>
              ))}
            </button>
          ))}
        </nav>
        {!selectedCase ? (
          <div className="research-empty">
            <h3>{t("Ten cases. Inspect every result.")}</h3>
            <p>
              {t(
                "Select a case, or follow the two corrections to see the exact change and original Evidence.",
              )}
            </p>
          </div>
        ) : (
          <div className="research-case-detail">
            <header aria-live="polite">
              <h3 ref={caseHeading} tabIndex={-1}>
                {selectedCase.name}
              </h3>
              <p>{selectedCase.description}</p>
              {!edits.length && (
                <p>{t("Unchanged relationship results across A, A′ and B.")}</p>
              )}
            </header>
            {!!edits.length && (
              <div className="research-edits">
                <h4>{t("Recorded endpoint corrections")}</h4>
                {edits.map((edit, index) => (
                  <button
                    key={`${edit.candidate_index}-${edit.endpoint}`}
                    onClick={() => selectEdit(index)}
                  >
                    {edit.original_name} → {edit.resolved_name}
                    <span>
                      {edit.relationship_type} · {edit.other_endpoint}
                    </span>
                  </button>
                ))}
              </div>
            )}
            <div className="research-table-scroll">
              <OutcomeMatrix caption={t("Relationship outcome matrix")}
                headings={[t("Configuration"), t("Matched · TP"), t("Extra · FP"), t("Missing · FN")]}
                rows={[baseline, "B" as const].map(label => {
                  const result = selectedCase.observations.find(item => item.run_label === label)!;
                  return { id: label, label: runName(label),
                    values: (["tp", "fp", "fn"] as const).map(metric => result.evaluation[metric]),
                  };
                })} />
            </div>
            <div className="research-controls">
              <label>
                {t("Baseline Run")}
                <select
                  value={baseline}
                  onChange={(event) =>
                    setBaseline(event.target.value as RunLabel)
                  }
                >
                  <option value="A_prime">A′</option>
                  <option value="A">A</option>
                </select>
              </label>
              <label>
                {t("Recorded outcome filter")}
                <select
                  value={filter}
                  onChange={(event) => setFilter(event.target.value as Filter)}
                >
                  <option value="all">{t("All recorded relationships")}</option>
                  <option value="errors">{t("Relationship errors")}</option>
                  <option value="missing">{t("False negatives")}</option>
                  <option value="extra">{t("False positives")}</option>
                  <option value="provenance_failure">
                    {t("Approved-quote failures")}
                  </option>
                  <option value="source_attribution_failure">
                    {t("Source-pair failures")}
                  </option>
                </select>
              </label>
            </div>
            <div className="research-inspection">
              <div className="research-pair">
                {[baseline, "B" as const].map((label) => (
                  <RelationshipList
                    key={label}
                    observation={selectedCase.observations.find(
                      (item) => item.run_label === label,
                    )}
                    label={label}
                    filter={filter}
                    selection={selection}
                    onSelect={(value) => selectOutcome(label, value)}
                  />
                ))}
              </div>
              <div className="research-source-inspection">
                {outcome && (
                  <>
                    <h4>
                      {t("Selected relationship")} ·{" "}
                      {selection && runName(selection.run)}
                    </h4>
                    <p>{outcome.edge.join(" · ")}</p>
                    <p>{outcomeLabel(outcome.outcome, t)}</p>
                    {!!attributionFailures.length && (
                      <section aria-label={t("Recorded Source-pair failures")}>
                        <p>
                          {t(
                            "Recorded Source-pair mismatch. The retained diagnostic does not classify the reason. Compare the exact Source and quote with the approved Evidence below.",
                          )}
                        </p>
                        <EvidenceChoices
                          title={t("Recorded Source-pair failures")}
                          items={attributionFailures}
                          active={quote}
                          onSelect={selectQuote}
                        />
                      </section>
                    )}
                    <EvidenceChoices
                      title={t("Expected approved Evidence")}
                      items={outcome.expected}
                      active={quote}
                      onSelect={selectQuote}
                    />
                    <EvidenceChoices
                      title={t("Predicted Evidence")}
                      items={outcome.predicted}
                      active={quote}
                      onSelect={selectQuote}
                    />
                  </>
                )}
                <label htmlFor={sourceSelectId}>{t("Original Source")}</label>
                <select
                  id={sourceSelectId}
                  value={source?.id ?? ""}
                  onChange={(event) => {
                    setSourceId(event.target.value);
                    setOccurrence(0);
                  }}
                >
                  {selectedCase.sources.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.title} · {item.id}
                    </option>
                  ))}
                </select>
                {source && (
                  <>
                    <p className="research-id">{source.id}</p>
                    {quote?.source_id === source.id && (
                      <>
                        {!quote.occurrences.length && (
                          <p>
                            {t(
                              "The exact quote was not found in this Source. No approximate highlight is substituted.",
                            )}
                          </p>
                        )}
                        {quote.occurrences.length > 1 && (
                          <label>
                            {t("Exact quote occurrence")}
                            <select
                              value={occurrence}
                              onChange={(event) =>
                                setOccurrence(Number(event.target.value))
                              }
                            >
                              {quote.occurrences.map((_, index) => (
                                <option key={index} value={index}>
                                  {index + 1} / {quote.occurrences.length}
                                </option>
                              ))}
                            </select>
                          </label>
                        )}
                      </>
                    )}
                    <SourcePanel
                      source={source.text}
                      title={source.title}
                      span={span}
                      activation={occurrence}
                    />
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
function RelationshipList({
  observation,
  label,
  filter,
  selection,
  onSelect,
}: {
  observation: PublicObservation | undefined;
  label: RunLabel;
  filter: Filter;
  selection: Selection | null;
  onSelect: (value: PublicOutcome) => void;
}) {
  const { t } = useLocale();
  const relationships =
    observation?.relationships.filter((item) => {
      if (filter === "all") return true;
      if (filter === "errors") {
        return item.outcome === "missing" || item.outcome === "extra";
      }
      if (filter === "source_attribution_failure") {
        return sourcePairFailures(observation, item).length > 0;
      }
      return item.outcome === filter;
    }) ?? [];
  return (
    <section aria-label={t("Run {run} relationships", { run: runName(label) })}>
      <h4>{t("Run {run}", { run: runName(label) })}</h4>
      {observation && (
        <p>
          {t("F1")} {percent(observation.evaluation.f1)} ·{" "}
          {t("False positives")} {observation.evaluation.fp} ·{" "}
          {t("False negatives")} {observation.evaluation.fn}
        </p>
      )}
      {relationships.length ? (
        relationships.map((item) => (
          <button
            key={item.id}
            aria-pressed={
              selection?.run === label && selection.outcomeId === item.id
            }
            onClick={() => onSelect(item)}
          >
            <span>{item.edge.join(" · ")}</span>
            <small>{outcomeLabel(item.outcome, t)}</small>
            {!!sourcePairFailures(observation, item).length && (
              <small>{t("Matched relationship; Source-pair mismatch")}</small>
            )}
          </button>
        ))
      ) : (
        <p>
          {filter === "errors"
            ? t("No recorded relationship errors.")
            : t("No recorded relationships match this filter.")}
        </p>
      )}
    </section>
  );
}
function EvidenceChoices({
  title,
  items,
  active,
  onSelect,
}: {
  title: string;
  items: PublicQuote[];
  active: PublicQuote | null;
  onSelect: (value: PublicQuote) => void;
}) {
  const { t } = useLocale();
  return (
    <section className="research-quotes">
      <h4>{title}</h4>
      {items.length ? (
        items.map((item) => (
          <button
            key={`${item.source_id}-${item.id}`}
            aria-pressed={active === item}
            onClick={() => onSelect(item)}
          >
            <span>
              {t("Source")}: {item.source_id}
            </span>
            <q>{item.text}</q>
          </button>
        ))
      ) : (
        <p>{t("No retained Evidence in this group.")}</p>
      )}
    </section>
  );
}
function outcomeLabel(
  value: PublicOutcome["outcome"],
  t: (key: string) => string,
) {
  switch (value) {
    case "matched":
      return t("Matched relationship; approved-quote check passed");
    case "missing":
      return t("False negative — expected relationship missing");
    case "extra":
      return t("False positive — predicted relationship not expected");
    case "provenance_failure":
      return t("Matched relationship; approved-quote mismatch");
    case "source_attribution_failure":
      return t("Matched relationship; Source-pair mismatch");
  }
}

// Join saved diagnostics by exact retained identities; no scoring or name normalization.
function sourcePairFailures(
  observation: PublicObservation | undefined,
  outcome: PublicOutcome,
): PublicQuote[] {
  const failures = observation?.source_attribution.failures ?? [];
  return outcome.predicted.filter((quote) =>
    failures.some(
      (failure) =>
        failure.edge.length === outcome.edge.length &&
        failure.edge.every((endpoint, index) => endpoint === outcome.edge[index]) &&
        failure.evidence_id === quote.id &&
        failure.source_id === quote.source_id &&
        failure.supporting_text === quote.text,
    ),
  );
}
