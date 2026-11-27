import { useCallback, useState } from "react";
import type { BenchmarkRoster } from "../shared/contracts";
import { ReadState } from "../shared/presentation";
import { useRead } from "../shared/useRead";
import { benchmarkV4Input } from "./api";
import { ConditionInspection } from "./ConditionInspection";

export function BenchmarkV4Catalogue({ roster, executable }: {
  roster: BenchmarkRoster;
  executable: boolean;
}) {
  const [selected, setSelected] = useState(roster.inputs[0].id);
  const input = roster.inputs.find((item) => item.id === selected)!;
  const consensus = input.reference_methodology === "consensus_adjudication";
  const matters = Array.from(new Set(roster.inputs.map((item) => item.matter)));
  const inputs = roster.inputs.filter((item) => item.matter === input.matter);
  const reference = roster.definition.consensus;

  return (
    <section className="run-inspection">
      <div className="section-heading">
        <div>
          <h1>PCG Benchmark v4</h1>
          <p>{roster.definition.matter_count} Matters · {roster.definition.input_count} evaluation inputs</p>
        </div>
        {executable && <a href="#new=1">New experiment</a>}
      </div>
      <p>Mixed references. The frozen 34-Condition DeepSeek baseline remains in Benchmark v3 Research.</p>
      <p>Measured 35-input results appear in their experiment Runs.</p>
      <div className="section-heading">
        <label>
          Matter
          <select value={input.matter} onChange={(event) => {
            const first = roster.inputs.find((item) => item.matter === event.target.value);
            if (first) setSelected(first.id);
          }}>
            {matters.map((matter) => (
              <option key={matter} value={matter}>{matter === "U" ? "U revision 8" : `Matter ${matter}`}</option>
            ))}
          </select>
        </label>
        {consensus ? (
          <p>Single evaluation input · {input.source_count} Sources</p>
        ) : (
          <label>
            Environment Condition
            <select value={selected} onChange={(event) => setSelected(event.target.value)}>
              {inputs.map((item) => <option key={item.id}>{item.id}</option>)}
            </select>
          </label>
        )}
      </div>
      <details key={input.matter}>
        <summary>{consensus ? "Consensus adjudication" : "Original independent qualification"}</summary>
        {consensus ? (
          <p>{reference.reviewer_count} independent AI reviewers. The inclusion threshold was {reference.support_threshold}/{reference.reviewer_count}.
            All {reference.unanimous_relationships} included relationships were unanimous and separately supported by Source-body evidence.
            {reference.zero_support_propositions} other propositions received zero affirmative votes. {reference.limitation}</p>
        ) : (
          <p>This Matter uses the original frozen Benchmark v3 reference and Evaluation Protocol v1 proof-sufficiency contract.</p>
        )}
      </details>
      <FrozenInput key={selected} identity={selected} />
    </section>
  );
}

function FrozenInput({ identity }: { identity: string }) {
  const load = useCallback((signal: AbortSignal) => benchmarkV4Input(identity, signal), [identity]);
  const { data, error, retry } = useRead(load);
  if (!data) return <ReadState error={error} retry={retry} />;
  return <ConditionInspection runId="benchmark-v4" observation={data} />;
}
