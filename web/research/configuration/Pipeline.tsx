import { AnalysisPipeline, type PipelineConfiguration } from "../../src/shared/research/AnalysisPipeline";
import type { Capabilities, Proposal } from "../shared/contracts";
import { InputFields, PipelineFields } from "./Fields";

type PipelineProps = {
  proposal?: Proposal;
  capabilities?: Capabilities;
  update?: (changes: Partial<Proposal>) => void;
  busy?: boolean;
  persistent?: boolean;
  frozen?: PipelineConfiguration;
};

export function Pipeline({ proposal, capabilities, update, busy = false, persistent = false, frozen }: PipelineProps) {
  const mutable = !!(proposal && capabilities && update);
  const configuration = proposal ? {
    resolver: proposal.resolver === "generative",
    input: proposal.input_mode === "saved" ? "Saved replay · Extraction bypassed" : "Fresh extraction samples",
    model: proposal.model,
    repetitions: String(proposal.resolver_repetitions),
  } : frozen ?? { resolver: false, input: "Input unavailable", model: "Unavailable", repetitions: "?" };
  function changeResolver(enabled: boolean) {
    if (!proposal || !update) return;
    update(enabled ? {
      resolver: "generative",
      execution_mode: proposal.execution_mode === "replay" ? "recorded" : proposal.execution_mode,
      invocation_cap: Math.max(1, proposal.invocation_cap),
    } : {
      resolver: "none",
      resolver_repetitions: 1,
      invocation_cap: proposal.input_mode === "fresh" ? Math.max(1, proposal.invocation_cap) : 0,
    });
  }
  return <AnalysisPipeline
    configuration={configuration}
    editing={mutable ? { busy, changeResolver } : undefined}
    extractionSettings={mutable ? <InputFields persistent={persistent} proposal={proposal!} capabilities={capabilities!} update={update!} busy={busy} /> : proposal ? <>
      <p>Frozen configuration · Read-only. No execution authority is granted by inspecting a stage.</p>
      <p>{proposal.input_mode} inputs · {proposal.input_ids.join(", ")}</p>
      <p>Model: {proposal.model}</p>
    </> : undefined}
    resolverSettings={mutable ? changeResolverStage => <>
      <p>Provider settings are shared across this configuration.</p>
      <p>Resolver repetitions are measurements of variability.</p>
      <PipelineFields proposal={proposal!} capabilities={capabilities!} update={changes => {
        if (changes.resolver === "none") changeResolverStage(false);
        else update!(changes);
      }} busy={busy} />
    </> : undefined}
  />;
}
