import { useState } from "react";
import type {
  EvidenceQuote,
  ProofTarget,
  ProofMember,
  RunObservation,
  Source,
} from "../shared/contracts";
import { edgeKey } from "./benchmarkEdges";
import { evidenceMetricLabels } from "./benchmark-metrics";
import { SourceReader, type Passage } from "./SourceReader";
import { percentMetric } from "../../src/shared/research/presentation";
import "./relationship-evidence.css";

type Edge = [string, string, string];
const proofLabels = {
  complete: "Complete proof",
  incomplete: "Incomplete proof",
  missed: "Missed relationship",
  without_graph: "Prediction unavailable",
};

export function RelationshipEvidence({
  observation,
  edge,
  onBack,
}: {
  observation: RunObservation;
  edge: Edge;
  onBack: () => void;
}) {
  const key = edgeKey(...edge);
  const sameEdge = (item: { edge: Edge }) => edgeKey(...item.edge) === key;
  const row = observation.relationships.find(sameEdge);
  const benchmark = observation.benchmark;
  const approved = benchmark?.expected_relationships.find(sameEdge);
  return (
    <EvidenceComparison
      key={JSON.stringify([observation.id, key])}
      edge={edge}
      target={benchmark?.proof_targets.find(sameEdge)}
      qualifiedExpected={Boolean(approved && (benchmark?.role === "natural" || benchmark?.role === "matched"))}
      expected={approved?.quotes ?? row?.expected ?? []}
      predicted={benchmark?.outcome === "scored" ? (row?.predicted ?? []) : []}
      sources={observation.sources ?? []}
      onBack={onBack}
    />
  );
}

type OpenPassage = (passage: Passage, trigger: HTMLButtonElement) => void;

function QuoteButton({
  passage,
  label,
  open,
}: {
  passage: Passage;
  label: string;
  open: OpenPassage;
}) {
  return (
    <button
      className="quote-preview"
      type="button"
      aria-label={`Read ${label} quotation from ${passage.source_id}: ${passage.text.slice(0, 72)}${passage.text.length > 72 ? "…" : ""}`}
      onClick={(event) => open(passage, event.currentTarget)}
    >
      <span className="quote-origin">
        {label} · {passage.source_id}
      </span>
      <q>{passage.text}</q>
    </button>
  );
}

export function EvidenceComparison({
  edge,
  target,
  qualifiedExpected = false,
  expected,
  predicted,
  sources,
  onBack,
}: {
  edge: Edge;
  target?: ProofTarget;
  qualifiedExpected?: boolean;
  expected: EvidenceQuote[];
  predicted: EvidenceQuote[];
  sources: Source[];
  onBack: () => void;
}) {
  const [reader, setReader] = useState<{
    passage: Passage;
    trigger: HTMLButtonElement;
    sequence: number;
  }>();
  const open: OpenPassage = (passage, trigger) => {
    setReader((previous) => ({
      passage,
      trigger,
      sequence: (previous?.sequence ?? 0) + 1,
    }));
  };
  function closeReader() {
    reader?.trigger.focus();
    setReader(undefined);
  }
  return (
    <section
      className="relationship-evidence"
      aria-label="Selected relationship evidence"
      tabIndex={-1}
    >
      <header>
        <h4>Supporting evidence</h4>
        <button className="secondary" type="button" onClick={onBack}>
          Return to selected relationship
        </button>
      </header>
      <p className="evidence-edge">
        {edge[0]} · {edge[1].replaceAll("_", " ")} · {edge[2]}
      </p>
      {target ? (
        <ProofAlternatives
          target={target}
          predicted={predicted}
          open={open}
          onChange={() => setReader(undefined)}
        />
      ) : qualifiedExpected && (
        <p>No formal proof target is annotated for this expected relationship.</p>
      )}
      {(!target || expected.length > 0 || predicted.length > 0) && (
        <details
          className="ordinary-quotes"
          open={target ? undefined : true}
          onToggle={(event) => {
            if (
              !event.currentTarget.open &&
              reader &&
              event.currentTarget.contains(reader.trigger)
            )
              setReader(undefined);
          }}
        >
          <summary>
            Other relationship quotations · {expected.length} approved ·{" "}
            {predicted.length} predicted
          </summary>
          <div>
            {expected.map((q) => (
              <QuoteButton key={q.id} passage={q} label="Approved" open={open} />
            ))}
            {predicted.map((q) => (
              <QuoteButton key={q.id} passage={q} label="Predicted" open={open} />
            ))}
            {!expected.length && !predicted.length && (
              <p>No retained quotations for this relationship.</p>
            )}
          </div>
        </details>
      )}
      {reader && (
        <SourceReader
          key={reader.sequence}
          passage={reader.passage}
          source={sources.find((s) => s.id === reader.passage.source_id)}
          onClose={closeReader}
        />
      )}
    </section>
  );
}

function ProofAlternatives({
  target,
  predicted,
  open,
  onChange,
}: {
  target: ProofTarget;
  predicted: EvidenceQuote[];
  open: OpenPassage;
  onChange: () => void;
}) {
  const alternatives = target.alternatives;
  const counts = alternatives.map(
    ({ members }) => members.filter((member) => member.attached).length,
  );
  const [index, setIndex] = useState(() =>
    Math.max(
      0,
      alternatives.findIndex(
        ({ members }, i) => members.length > 0 && counts[i] === members.length,
      ),
    ),
  );
  return (
    <section aria-label="Sufficient Evidence Alternatives">
      <h5>Sufficient Evidence Alternatives</h5>
      <p>
        {proofLabels[target.status]}
        {target.joint_only && " · Multiple Sources required"}
      </p>
      {target.best_alternative_coverage != null && (
        <p>{evidenceMetricLabels.joint_only_coverage} for this relationship · {percentMetric(target.best_alternative_coverage)}</p>
      )}
      {alternatives.length > 1 && (
        <div
          className="proof-choices"
          role="group"
          aria-label="Choose evidence alternative"
        >
          {alternatives.map(({ members }, i) => {
            const complete = counts[i] === members.length && members.length > 0;
            return (
              <button
                type="button"
                key={i}
                aria-pressed={i === index}
                aria-label={`Alternative ${i + 1}, ${complete ? "complete" : "incomplete"}, ${counts[i]} of ${members.length} attached`}
                onClick={() => {
                  setIndex(i);
                  onChange();
                }}
              >
                <b>
                  {i + 1} {complete ? "✓" : "○"}
                </b>
                <small>
                  {counts[i]}/{members.length}
                </small>
              </button>
            );
          })}
        </div>
      )}
      <ul
        className="proof-members"
        aria-label={`Members of alternative ${index + 1}`}
      >
        {alternatives[index]?.members.map((member) => {
          const attached = predicted.filter(
            (q) => q.source_id === member.source_id,
          );
          const status = memberStatus(target.status, member, attached);
          return (
            <li key={JSON.stringify([member.source_id, member.text])}>
              <span className="member-status" data-kind={status.kind}>
                <span aria-hidden="true">{status.glyph}</span>{" "}
                <span>{status.label}</span>
              </span>
              <QuoteButton passage={member} label="Approved" open={open} />
              {status.kind === "mismatch" &&
                attached.map((q) => (
                  <QuoteButton
                    key={q.id}
                    passage={q}
                    label="Attached"
                    open={open}
                  />
                ))}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function memberStatus(
  status: ProofTarget["status"],
  member: ProofMember,
  attached: EvidenceQuote[],
) {
  if (status === "without_graph")
    return { kind: "unavailable", glyph: "○", label: "Prediction unavailable" };
  if (status === "missed")
    return { kind: "missing", glyph: "−", label: "Relationship missing" };
  if (member.attached)
    return { kind: "exact", glyph: "✓", label: "Exact quotation attached" };
  return attached.length
    ? { kind: "mismatch", glyph: "≠", label: "Quotation differs" }
    : {
        kind: "missing",
        glyph: "−",
        label: "Source missing from this relationship",
      };
}
