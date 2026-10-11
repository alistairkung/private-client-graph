import type { Capabilities, Proposal } from "../shared/contracts";

type FieldProps = {
  proposal: Proposal;
  capabilities: Capabilities;
  update: (changes: Partial<Proposal>) => void;
  busy: boolean;
};

export function InputFields({
  proposal,
  capabilities,
  update,
  busy,
}: FieldProps) {
  return (
    <fieldset disabled={busy}>
      <legend>Inputs</legend>
      <label>
        Execution mode
        <select
          value={proposal.execution_mode}
          onChange={(event) =>
            update(
              event.target.value === "replay"
                ? {
                    execution_mode: "replay",
                    input_mode: "saved",
                    resolver: "none",
                    extraction_samples: 1,
                    resolver_repetitions: 1,
                    invocation_cap: 0,
                    task_call_cap: 0,
                  }
                : {
                    execution_mode:
                      event.target.value === "live" ? "live" : "recorded",
                    task_call_cap:
                      event.target.value === "live"
                        ? capabilities.live_task?.cap || 1
                        : 0,
                    resolver: "generative",
                    invocation_cap: 1,
                  },
            )
          }
        >
          <option value="replay">Saved replay · No provider calls</option>
          <option value="recorded">
            Recorded demonstration · Not live quality
          </option>
          {capabilities.live_enabled && (
            <option value="live">
              Live provider · Explicit approval required
            </option>
          )}
        </select>
      </label>
      <label>
        Input mode
        <select
          value={proposal.input_mode}
          disabled={proposal.execution_mode === "replay"}
          onChange={(event) =>
            update(
              event.target.value === "fresh"
                ? {
                    input_mode: "fresh",
                    input_ids: [capabilities.fresh_input_id],
                    extraction_samples: 1,
                    invocation_cap: 1,
                  }
                : {
                    input_mode: "saved",
                    input_ids: capabilities.inputs.map((input) => input.id),
                    extraction_samples: 1,
                    invocation_cap: proposal.resolver === "none" ? 0 : 1,
                  },
            )
          }
        >
          <option value="saved">Saved extraction snapshots</option>
          <option value="fresh">Fresh extraction samples</option>
        </select>
      </label>
      <p className="muted">
        Saved extraction with a generative resolver can still require paid calls
        in live execution. {capabilities.live_reason}
      </p>
      <label>
        Extraction samples
        <input
          type="number"
          min={1}
          max={capabilities.maximum_extraction_samples}
          value={proposal.extraction_samples}
          disabled={proposal.input_mode === "saved"}
          onChange={(event) =>
            update({ extraction_samples: Number(event.target.value) })
          }
        />
      </label>
      <small>
        Fresh samples each receive a separate extraction; all resolver
        repetitions share that sample.
      </small>
    </fieldset>
  );
}

export function PipelineFields({
  proposal,
  capabilities,
  update,
  busy,
}: FieldProps) {
  return (
    <fieldset disabled={busy}>
      <legend>Pipeline & repetitions</legend>
      <label>
        Resolver
        <select
          value={proposal.resolver}
          disabled={proposal.execution_mode === "replay"}
          onChange={(event) =>
            update(
              event.target.value === "none"
                ? {
                    resolver: "none",
                    resolver_repetitions: 1,
                    invocation_cap: proposal.input_mode === "fresh" ? 1 : 0,
                  }
                : { resolver: "generative", invocation_cap: 1 },
            )
          }
        >
          <option value="none">No resolution</option>
          <option value="generative">Generative · Full Source</option>
        </select>
      </label>
      <label>
        Resolver repetitions
        <input
          type="number"
          min={1}
          max={capabilities.maximum_resolver_repetitions}
          value={proposal.resolver_repetitions}
          disabled={proposal.resolver === "none"}
          onChange={(event) =>
            update({ resolver_repetitions: Number(event.target.value) })
          }
        />
      </label>
      <label>
        Model
        <select value={proposal.model} disabled>
          <option value="deepseek-flash">deepseek-flash</option>
        </select>
      </label>
      <label>
        Temperature (optional)
        <input
          type="number"
          min={0}
          max={2}
          step={0.1}
          disabled={proposal.execution_mode === "replay"}
          value={proposal.temperature ?? ""}
          onChange={(event) =>
            update({
              temperature:
                event.target.value === "" ? null : Number(event.target.value),
            })
          }
        />
      </label>
      <label>
        Provider timeout (seconds)
        <input
          type="number"
          min={1}
          max={300}
          disabled={proposal.execution_mode === "replay"}
          value={proposal.timeout_seconds}
          onChange={(event) =>
            update({ timeout_seconds: Number(event.target.value) })
          }
        />
      </label>
      <small>
        {proposal.execution_mode === "replay" &&
          "Provider settings do not affect saved replay. "}
        {capabilities.provider}. Thinking disabled; retries disabled.
      </small>
      {proposal.execution_mode === "live" && (
        <>
          <label>
            Proposed total task call cap
            <input
              type="number"
              min={1}
              max={10000}
              value={proposal.task_call_cap}
              aria-describedby="task-cap-help"
              onChange={(event) =>
                update({ task_call_cap: Number(event.target.value) })
              }
            />
          </label>
          <small id="task-cap-help">
            Shared across experiments in this local task. Freezing does not
            increase the allowance; approval is required.
          </small>
        </>
      )}
      <label>
        Invocation attempt cap
        <input
          type="number"
          min={0}
          max={38}
          value={proposal.invocation_cap}
          onChange={(event) =>
            update({ invocation_cap: Number(event.target.value) })
          }
        />
      </label>
      <small>
        Stop at this many new provider attempts, then explicitly review
        continuation. Replay uses zero.
      </small>
    </fieldset>
  );
}
