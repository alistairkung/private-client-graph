import { OutcomeMatrix } from "../../shared/research/OutcomeMatrix";
import { useId, useLayoutEffect, useRef, useState } from "react";
import { useLocale } from "../../shared/locale";
import { SourcePanel } from "./recorded-review/SourcePanel";
import { runName } from "./RunComparison";
import { ResearchAccordion } from "./ResearchAccordion";
import { ResearchRunSwitch } from "./ResearchRunSwitch";
import type { PublicCase, PublicObservation, PublicOutcome, PublicQuote, PublicSource, RunLabel } from "./types";

type Selection = { run: RunLabel; outcomeId: string };
type Filter = "all" | "errors" | "missing" | "extra" | "provenance_failure" | "source_attribution_failure";

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
  const [activeRun, setActiveRun] = useState<RunLabel>("A_prime");
  const [filter, setFilter] = useState<Filter>("all");
  const [selection, setSelection] = useState<Selection | null>(null);
  const [quote, setQuote] = useState<PublicQuote | null>(null);
  const [sourceId, setSourceId] = useState("");
  const [occurrence, setOccurrence] = useState(0);
  const [sourceOpen, setSourceOpen] = useState(false);
  const [sourceNavigation, setSourceNavigation] = useState(0);
  const sourceSection = useRef<HTMLElement>(null);
  const sourceJump = useRef<HTMLButtonElement>(null);
  useLayoutEffect(() => {
    if (!sourceNavigation) return;
    sourceSection.current?.focus({ preventScroll: true });
    sourceSection.current?.scrollIntoView({ behavior: "instant", block: "start" });
  }, [sourceNavigation]);
  const selectedCase = cases.find(item => item.case_id === caseId);
  const observation = selectedCase?.observations.find(item => item.run_label === activeRun);
  const relationships = observation?.relationships.filter(item => matchesFilter(observation, item, filter)) ?? [];
  const outcome = selection?.run === activeRun
    ? relationships.find(item => item.id === selection.outcomeId)
    : undefined;
  const attributionFailures = outcome ? sourcePairFailures(observation, outcome) : [];
  const source = selectedCase?.sources.find(item => item.id === sourceId) ?? selectedCase?.sources[0];
  const edits = selectedCase?.observations.find(item => item.run_label === "B")?.edits ?? [];

  function clearInspection() {
    setSelection(null);
    setQuote(null);
    setSourceOpen(false);
    setSourceId("");
    setOccurrence(0);
  }
  function selectCase(id: string) {
    setCaseId(id);
    clearInspection();
  }
  function selectQuote(value: PublicQuote) {
    setQuote(value);
    setSourceId(value.source_id);
    setOccurrence(0);
  }
  function selectOutcome(run: RunLabel, value: PublicOutcome) {
    setSelection({ run, outcomeId: value.id });
    setSourceOpen(false);
    const evidence = value.predicted[0] ?? value.expected[0];
    if (evidence) selectQuote(evidence);
    else setQuote(null);
  }
  function selectEdit(index: number) {
    const edit = edits[index];
    const target = selectedCase?.observations.find(item => item.run_label === "B")?.relationships.find(item => item.id === edit.outcome_id);
    if (!target) return;
    setActiveRun("B");
    setFilter("all");
    selectOutcome("B", target);
    const evidence = target.predicted.find(item => item.source_id === edit.source_id && item.text === edit.supporting_text);
    if (evidence) selectQuote(evidence);
  }
  const recordedSpan = quote && quote.source_id === source?.id ? quote.occurrences[occurrence] : undefined;
  const codepoints = Array.from(source?.text ?? "");
  const span = recordedSpan ? {
    start: codepoints.slice(0, recordedSpan[0]).join("").length,
    end: codepoints.slice(0, recordedSpan[1]).join("").length,
  } : undefined;
  return <section id="cases" className="research-section">
    <div className="research-section-title">
      <h2>{t("Follow the recorded difference")}</h2>
      <button onClick={() => { selectCase("heldout_03"); setFilter("all"); setCaseNavigation(value => value + 1); }}>
        {t("Inspect the two corrections")}
      </button>
    </div>
    <p>{t("Choose a case, then inspect one Run at a time. The comparison remains visible. No case is selected by default.")}</p>
    <label className="research-case-picker">
      {t("Benchmark case")}
      <select value={caseId} onChange={event => selectCase(event.target.value)}>
        <option value="">{t("Select a case")}</option>
        {cases.map(item => <option key={item.case_id} value={item.case_id}>{item.case_id} · {item.name}</option>)}
      </select>
    </label>
    <div className="research-workspace">
      {!selectedCase ? <div className="research-empty">
        <h3>{t("Ten cases. Inspect every result.")}</h3>
        <p>{t("Select a case, or follow the two corrections to see the exact change and original Evidence.")}</p>
      </div> : <div className="research-case-detail">
        <header aria-live="polite">
          <h3 ref={caseHeading} tabIndex={-1}>{selectedCase.name}</h3>
          <p>{selectedCase.description}</p>
          {!edits.length && <p>{t("Unchanged relationship results across A, A′ and B.")}</p>}
        </header>
        {!!edits.length && <div className="research-edits">
          <h4>{t("Recorded endpoint corrections")}</h4>
          {edits.map((edit, index) => <button key={`${edit.candidate_index}-${edit.endpoint}`} onClick={() => selectEdit(index)}>
            {edit.original_name} → {edit.resolved_name}<span>{edit.relationship_type} · {edit.other_endpoint}</span>
          </button>)}
        </div>}
        <div className="research-case-comparison">
          <label>{t("Baseline Run")}
            <select value={baseline} onChange={event => {
              const next = event.target.value as RunLabel;
              setBaseline(next);
              if (activeRun !== "B") setActiveRun(next);
              clearInspection();
            }}><option value="A_prime">A′</option><option value="A">A</option></select>
          </label>
          <div className="research-table-scroll">
            <OutcomeMatrix caption={t("Relationship outcome matrix")}
              headings={[t("Configuration"), t("Matched · TP"), t("Extra · FP"), t("Missing · FN")]}
              rows={[baseline, "B" as const].map(label => {
                const result = selectedCase.observations.find(item => item.run_label === label)!;
                return { id: label, label: runName(label), values: (["tp", "fp", "fn"] as const).map(metric => result.evaluation[metric]) };
              })} />
          </div>
        </div>
        <div className="research-inspection">
          <div className="research-relationship-list">
            <ResearchRunSwitch label={t("Relationship Run")} value={activeRun}
              options={[baseline, "B" as const].map(label => ({ value: label, label: t("Run {run}", { run: runName(label) }) }))}
              onChange={label => { setActiveRun(label); clearInspection(); }} />
            <label>{t("Recorded outcome filter")}
              <select value={filter} onChange={event => { setFilter(event.target.value as Filter); clearInspection(); }}>
                {([ ["all", "All recorded relationships"], ["errors", "Relationship errors"], ["missing", "False negatives"], ["extra", "False positives"], ["provenance_failure", "Approved-quote failures"], ["source_attribution_failure", "Source-pair failures"] ] as const).map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}
              </select>
            </label>
            <section aria-label={t("Run {run} relationships", { run: runName(activeRun) })}>
              <h4>{t("Run {run}", { run: runName(activeRun) })}</h4>
              {relationships.length ? relationships.map(item => <button key={item.id} aria-pressed={outcome?.id === item.id} onClick={() => selectOutcome(activeRun, item)}>
                <span>{item.edge.join(" · ")}</span>
                <small>{outcomeLabel(item.outcome, t)}</small>
                {!!sourcePairFailures(observation, item).length && <small>{t("Matched relationship; Source-pair mismatch")}</small>}
              </button>) : <p>{filter === "errors" ? t("No recorded relationship errors.") : t("No recorded relationships match this filter.")}</p>}
            </section>
          </div>
          <div className="research-source-inspection">
            {outcome ? <>
              <h4>{t("Selected relationship")} · {selection && runName(selection.run)}</h4>
              <p>{outcome.edge.join(" · ")}</p>
              <p>{outcomeLabel(outcome.outcome, t)}</p>
              {!!attributionFailures.length && <section aria-label={t("Recorded Source-pair failures")}>
                <p>{t("Recorded Source-pair mismatch. The retained diagnostic does not classify the reason. Compare the exact Source and quote with the approved Evidence below.")}</p>
                <EvidenceChoices title={t("Recorded Source-pair failures")} items={attributionFailures} active={quote} onSelect={selectQuote} sources={selectedCase.sources} />
              </section>}
              <EvidenceChoices title={t("Expected approved Evidence")} items={outcome.expected} active={quote} onSelect={selectQuote} sources={selectedCase.sources} />
              <EvidenceChoices title={t("Predicted Evidence")} items={outcome.predicted} active={quote} onSelect={selectQuote} sources={selectedCase.sources} />
            </> : <p>{t("Select a relationship to inspect its Evidence.")}</p>}
            <button ref={sourceJump} onClick={() => { setSourceOpen(true); setSourceNavigation(value => value + 1); }}>{t("View in original Source")}</button>
            {sourceOpen && source && <section ref={sourceSection} className="research-full-source" aria-label={t("Original Source")} tabIndex={-1}>
              <button onClick={() => { setSourceOpen(false); sourceJump.current?.focus({ preventScroll: true }); }}>{t("Back to selected relationship")}</button>
              <label htmlFor={sourceSelectId}>{t("Original Source")}</label>
              <select id={sourceSelectId} value={source.id} onChange={event => { setSourceId(event.target.value); setOccurrence(0); }}>
                {selectedCase.sources.map(item => <option key={item.id} value={item.id}>{item.title} · {item.id}</option>)}
              </select>
              <p className="research-id">{source.id}</p>
              {quote?.source_id === source.id && !quote.occurrences.length && <p>{t("The exact quote was not found in this Source. No approximate highlight is substituted.")}</p>}
              {quote?.source_id === source.id && quote.occurrences.length > 1 && <label>{t("Exact quote occurrence")}
                <select value={occurrence} onChange={event => setOccurrence(Number(event.target.value))}>
                  {quote.occurrences.map((_, index) => <option key={index} value={index}>{index + 1} / {quote.occurrences.length}</option>)}
                </select>
              </label>}
              <SourcePanel source={source.text} title={source.title} span={span} revealRequest={sourceNavigation} />
            </section>}
            {outcome && <ResearchAccordion key={`${activeRun}-${outcome.id}`} className="research-record-identifiers" items={[{
              id: "identifiers", title: t("Record identifiers"), content: <>
                <dl className="research-metadata">
                  <dt>{t("Relationship outcome ID")}</dt><dd>{outcome.id}</dd>
                </dl>
                {([["Expected approved Evidence", outcome.expected], ["Predicted Evidence", outcome.predicted]] as const).map(([label, items]) => <section key={label}>
                  <h4>{t(label)}</h4>
                  {items.map(item => <dl className="research-metadata" key={`${item.source_id}-${item.id}`}>
                    <dt>{t("Evidence ID")}</dt><dd>{item.id}</dd>
                    <dt>{t("Source identity")}</dt><dd>{item.source_id}</dd>
                  </dl>)}
                </section>)}
              </>,
            }]} />}
          </div>
        </div>
      </div>}
    </div>
  </section>;
}

function matchesFilter(observation: PublicObservation | undefined, outcome: PublicOutcome, filter: Filter) {
  if (filter === "all") return true;
  if (filter === "errors") return outcome.outcome === "missing" || outcome.outcome === "extra";
  if (filter === "source_attribution_failure") return sourcePairFailures(observation, outcome).length > 0;
  return outcome.outcome === filter;
}

function EvidenceChoices({
  title,
  items,
  active,
  onSelect,
  sources,
}: {
  title: string;
  items: PublicQuote[];
  sources: PublicSource[];
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
              {t("Source")}: {sources.find(source => source.id === item.source_id)?.title ?? item.source_id} · {item.source_id}
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
