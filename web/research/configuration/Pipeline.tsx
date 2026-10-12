import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import type { Capabilities, Proposal } from "../shared/contracts";
import { InputFields, PipelineFields } from "./Fields";

type Stage = "extract" | "resolve" | "graph";
type PipelineProps = {
  proposal?: Proposal;
  capabilities?: Capabilities;
  update?: (changes: Partial<Proposal>) => void;
  busy?: boolean;
  persistent?: boolean;
  frozen?: {
    resolver: boolean;
    input: string;
    model: string;
    repetitions: string;
  };
};

export function Pipeline({
  proposal,
  capabilities,
  update,
  busy = false,
  frozen,
  persistent = false,
}: PipelineProps) {
  const instance = useId();
  const [expanded, setExpanded] = useState<Stage | null>(null);
  const [menu, setMenu] = useState(false);
  const viewport = useRef<HTMLDivElement>(null);
  const add = useRef<HTMLButtonElement>(null);
  const insertion = useRef<HTMLDivElement>(null);
  const insertionMenu = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!menu) return;
    const frame = viewport.current?.getBoundingClientRect();
    const popup = insertionMenu.current?.getBoundingClientRect();
    if (frame && popup) {
      // Keep the entire anchored option visible in the horizontal rail on mobile.
      viewport.current?.scrollBy({
        left:
          Math.max(0, popup.right - frame.right + 12) +
          Math.min(0, popup.left - frame.left - 12),
        behavior: "instant",
      });
    }
    const dismiss = (event: PointerEvent) => {
      if (!insertion.current?.contains(event.target as Node)) setMenu(false);
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [menu]);
  const resolverHeader = useRef<HTMLButtonElement>(null);
  const mutable = !!(proposal && capabilities && update);
  const resolved = proposal
    ? proposal.resolver === "generative"
    : frozen?.resolver;
  function changeResolver(enabled: boolean) {
    if (!proposal || !update) return;
    update(
      enabled
        ? {
            resolver: "generative",
            execution_mode:
              proposal.execution_mode === "replay"
                ? "recorded"
                : proposal.execution_mode,
            invocation_cap: Math.max(1, proposal.invocation_cap),
          }
        : {
            resolver: "none",
            resolver_repetitions: 1,
            invocation_cap:
              proposal.input_mode === "fresh"
                ? Math.max(1, proposal.invocation_cap)
                : 0,
          },
    );
    setMenu(false);
    setExpanded(enabled ? "resolve" : null);
    requestAnimationFrame(() =>
      (enabled ? resolverHeader.current : add.current)?.focus(),
    );
  }
  function node(
    id: Stage,
    title: string,
    type: string,
    summary: string,
    settings: ReactNode,
  ) {
    const open = expanded === id;
    return (
      <section className={`pipeline-node ${open ? "expanded" : ""}`} key={id}>
        <button
          ref={id === "resolve" ? resolverHeader : undefined}
          type="button"
          className="node-header"
          aria-expanded={open}
          aria-controls={`${instance}-stage-${id}`}
          onClick={() => setExpanded(open ? null : id)}
        >
          <strong>{title}</strong>
          <small>
            {type} ·{" "}
            {id === "resolve"
              ? "Optional"
              : id === "extract"
                ? "Required for source"
                : "Required"}
          </small>
          <span>{summary}</span>
          <u>{open ? "Collapse settings" : "Expand settings"}</u>
        </button>
        {id === "resolve" && mutable && (
          <button
            type="button"
            className="remove-node"
            disabled={busy}
            aria-label="Bypass alias resolution"
            onClick={() => changeResolver(false)}
          >
            ×
          </button>
        )}
        <div
          id={`${instance}-stage-${id}`}
          role="region"
          aria-label={`${title} settings`}
          hidden={!open}
          className="node-settings"
        >
          {settings}
        </div>
      </section>
    );
  }
  const readOnly = (
    <p>
      Frozen configuration · Read-only. No execution authority is granted by
      inspecting a stage.
    </p>
  );
  return (
    <section
      className="pipeline-workspace"
      aria-label="Shared Analysis Pipeline"
    >
      <div className="pipeline-heading">
        <h2>Shared Analysis Pipeline</h2>
        <small>Fixed stage order</small>
      </div>
      <div className="pipeline-viewport" ref={viewport}>
        <div className="pipeline-rail">
          {node(
            "extract",
            "Extract relationships",
            "Model",
            proposal
              ? proposal.input_mode === "saved"
                ? "Saved replay · Extraction bypassed"
                : "Fresh extraction samples"
              : (frozen?.input ?? "Input unavailable"),
            mutable ? (
              <InputFields
                persistent={persistent}
                proposal={proposal!}
                capabilities={capabilities!}
                update={update!}
                busy={busy}
              />
            ) : (
              <>
                {readOnly}
                <p>
                  {proposal
                    ? `${proposal.input_mode} inputs · ${proposal.input_ids.join(", ")}`
                    : frozen?.input}
                </p>
                <p>
                  Model: {proposal?.model ?? frozen?.model ?? "Unavailable"}
                </p>
              </>
            ),
          )}
          <div
            ref={insertion}
            className={`pipeline-connector ${!resolved ? "eligible" : ""}`}
          >
            {!resolved && mutable && (
              <>
                <button
                  type="button"
                  className="insert-node"
                  ref={add}
                  disabled={busy}
                  aria-label="Add alias resolution"
                  aria-expanded={menu}
                  aria-controls={`${instance}-resolver-menu`}
                  onClick={() => setMenu(!menu)}
                >
                  <span>+</span>
                </button>
                {menu && (
                  <div
                    ref={insertionMenu}
                    id={`${instance}-resolver-menu`}
                    className="resolver-menu"
                    onKeyDown={(e) => {
                      if (e.key === "Escape") {
                        setMenu(false);
                        add.current?.focus();
                      }
                    }}
                  >
                    <button
                      type="button"
                      autoFocus
                      onClick={() => changeResolver(true)}
                    >
                      Add generative resolver
                    </button>
                  </div>
                )}
              </>
            )}
            {!resolved && <small>No-op</small>}
          </div>
          <div
            className={`resolver-slot ${resolved ? "present" : ""} ${expanded === "resolve" ? "expanded" : ""}`}
            inert={!resolved}
            aria-hidden={!resolved}
          >
            {node(
              "resolve",
              "Resolve aliases",
              "Model",
              `Full source · ${proposal?.model ?? frozen?.model ?? "Model unavailable"} · ${proposal?.resolver_repetitions ?? frozen?.repetitions ?? "?"} repetitions`,
              mutable ? (
                <>
                  <p>Provider settings are shared across this configuration.</p>
                  <p>Resolver repetitions are measurements of variability.</p>
                  <PipelineFields
                    proposal={proposal!}
                    capabilities={capabilities!}
                    update={(changes) => {
                      if (changes.resolver === "none") changeResolver(false);
                      else update!(changes);
                    }}
                    busy={busy}
                  />
                </>
              ) : (
                <>
                  {readOnly}
                  <p>Model: {proposal?.model ?? frozen?.model}</p>
                  <p>
                    Resolver repetitions:{" "}
                    {proposal?.resolver_repetitions ?? frozen?.repetitions}
                  </p>
                </>
              ),
            )}
            <div className="pipeline-connector" />
          </div>
          {node(
            "graph",
            "Build relationship graph",
            "Deterministic",
            "Fixed validation and construction",
            <p>
              Required deterministic operation. No configurable strategy or
              removal.
            </p>,
          )}
          <div className="pipeline-connector" />
          <div className="pipeline-evaluation">
            <small>Outside the pipeline</small>
            <strong>Evaluate results</strong>
            <span>Deterministic · Ground truth</span>
          </div>
        </div>
      </div>
      <div className="pipeline-navigation">
        <span>
          {mutable
            ? "Select a node to configure it"
            : "Frozen configuration · Read-only"}
        </span>
        {!resolved && mutable && (
          <button type="button" disabled={busy} onClick={() => setMenu(true)}>
            Add optional stage
          </button>
        )}
        <button
          type="button"
          onClick={() => viewport.current?.scrollBy({ left: -320 })}
        >
          Previous stages
        </button>
        <button
          type="button"
          onClick={() => viewport.current?.scrollBy({ left: 320 })}
        >
          Next stages
        </button>
      </div>
    </section>
  );
}
