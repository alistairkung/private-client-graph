import { PipelineNode } from "./PipelineNode";
import { researchText, type ResearchText } from "./presentation";
import "./analysis-pipeline.css";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";
export type PipelineConfiguration = {
  resolver: boolean;
  input: string;
  model: string;
  repetitions: string;
};
type Stage = "extract" | "resolve" | "graph";
type AnalysisPipelineProps = {
  configuration: PipelineConfiguration;
  extractionSettings?: ReactNode;
  resolverSettings?: (changeResolver: (enabled: boolean) => void) => ReactNode;
  editing?: { busy: boolean; changeResolver: (enabled: boolean) => void };
  appearance?: "standard" | "persistent";
  t?: ResearchText;
};

// Local visualization state lives here; execution and configuration writes belong to callers.
export function AnalysisPipeline({
  configuration,
  extractionSettings,
  resolverSettings,
  editing,
  appearance = "standard",
  t = researchText,
}: AnalysisPipelineProps) {
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
  const mutable = !!editing;
  const busy = editing?.busy ?? false;
  const resolved = configuration.resolver;
  function changeResolver(enabled: boolean) {
    if (!editing) return;
    editing.changeResolver(enabled);
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
    const optional = id === "resolve";
    const requirement = optional ? "Optional" : id === "extract" ? "Required for source" : "Required";
    return (
      <PipelineNode
        key={id}
        id={`${instance}-stage-${id}`}
        title={t(title)}
        type={`${t(type)} · ${t(requirement)}`}
        summary={summary}
        open={expanded === id}
        onToggle={() => setExpanded(expanded === id ? null : id)}
        expandLabel={t("Expand settings")}
        collapseLabel={t("Collapse settings")}
        regionLabel={t("{stage} settings", { stage: t(title) })}
        headerRef={optional ? resolverHeader : undefined}
        action={optional && mutable ? (
          <button
            type="button"
            className="remove-node"
            disabled={busy}
            aria-label={t("Bypass alias resolution")}
            onClick={() => changeResolver(false)}
          >×</button>
        ) : undefined}
      >
        {settings}
      </PipelineNode>
    );
  }
  const readOnly = (
    <p>
      {t("Frozen configuration · Read-only. No execution authority is granted by inspecting a stage.")}
    </p>
  );
  return (
    <section
      className={`research-visual pipeline-workspace ${appearance === "persistent" ? "pipeline-persistent" : ""}`}
      aria-label={t("Shared Analysis Pipeline")}
    >
      <div className="pipeline-heading">
        <h2>{t("Shared Analysis Pipeline")}</h2>
        <small>{t("Fixed stage order")}</small>
      </div>
      <div className="pipeline-viewport" ref={viewport}>
        <div className="pipeline-rail">
          {node(
            "extract",
            "Extract relationships",
            "Model",
            configuration.input,
            extractionSettings ?? <>
              {readOnly}
              <p>{configuration.input}</p>
              <p>{t("Model")}: {configuration.model}</p>
            </>,
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
                  aria-label={t("Add alias resolution")}
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
                      {t("Add generative resolver")}
                    </button>
                  </div>
                )}
              </>
            )}
            {!resolved && <small>{t("No-op")}</small>}
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
              t("Full source · {model} · {repetitions} repetitions", { model: configuration.model, repetitions: configuration.repetitions }),
              resolverSettings?.(changeResolver) ?? <>
                {readOnly}
                <p>{t("Model")}: {configuration.model}</p>
                <p>{t("Resolver repetitions")}: {configuration.repetitions}</p>
              </>,
            )}
            <div className="pipeline-connector" />
          </div>
          {node(
            "graph",
            "Build relationship graph",
            "Deterministic",
            t("Fixed validation and construction"),
            <p>
              {t("Required deterministic operation. No configurable strategy or removal.")}
            </p>,
          )}
          <div className="pipeline-connector" />
          <div className="pipeline-evaluation">
            <small>{t("Outside the pipeline")}</small>
            <strong>{t("Evaluate results")}</strong>
            <span>{t("Deterministic · Ground truth")}</span>
          </div>
        </div>
      </div>
      <div className="pipeline-navigation">
        <span>
          {mutable
            ? t("Select a node to configure it")
            : t("Frozen configuration · Read-only")}
        </span>
        {!resolved && mutable && (
          <button type="button" disabled={busy} onClick={() => setMenu(true)}>
            {t("Add optional stage")}
          </button>
        )}
        <button
          type="button"
          onClick={() => viewport.current?.scrollBy({ left: -320 })}
        >
          {t("Previous stages")}
        </button>
        <button
          type="button"
          onClick={() => viewport.current?.scrollBy({ left: 320 })}
        >
          {t("Next stages")}
        </button>
      </div>
    </section>
  );
}
