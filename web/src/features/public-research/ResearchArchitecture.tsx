import { useId, useState } from "react";
import { useLocale } from "../../shared/locale";
import { PipelineNode } from "../../shared/research/PipelineNode";
import type { PublicRun } from "./types";

export function ResearchArchitecture({ runs }: { runs: PublicRun[] }) {
  const { t } = useLocale();
  const id = useId();
  const [resolver, setResolver] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const model = runs.find(run => run.label === "A")?.calls[0]?.model ?? t("Unavailable");
  const stages = [
    {
      id: "extract",
      title: "Extract relationships",
      type: "Model",
      summary: "Ordered Sources → Source-attributed candidates",
      detail: "A single full-context call reads the ordered Sources and proposes semantic relationships with exact documentary Evidence.",
    },
    ...(resolver ? [{
      id: "resolve",
      title: "Resolve aliases",
      type: "Model · Optional",
      summary: "Frozen candidates → constrained endpoint edits",
      detail: "The optional generative resolver can correct endpoint names using the original Sources. It does not rewrite the documentary quotations or perform graph construction.",
    }] : []),
    {
      id: "construct",
      title: "Build relationship graph",
      type: "Deterministic",
      summary: "Fixed validation → CanonicalState",
      detail: "Deterministic validation and construction turn candidates into a canonical relationship graph. Evaluation against project-authored truth happens separately, outside this pipeline.",
    },
  ];
  return (
    <div className="research-architecture">
      <div className="research-controls" aria-label={t("Published configurations")}>
        <button aria-pressed={!resolver} onClick={() => setResolver(false)}>
          {t("Baseline configuration")}
        </button>
        <button aria-pressed={resolver} onClick={() => setResolver(true)}>
          {t("Resolver configuration")}
        </button>
      </div>
      <div className="research-chain-scroll" role="region" aria-label={t("Shared Analysis Pipeline")} tabIndex={0}>
        <div className="research-chain">
          {stages.map((stage, index) => (
            <div className="research-chain-stage" key={stage.id}>
              {index > 0 && <span className="research-chain-connector" aria-hidden="true">→</span>}
              <PipelineNode
                id={`${id}-${stage.id}`}
                title={t(stage.title)}
                type={t(stage.type)}
                summary={t(stage.summary)}
                open={expanded === stage.id}
                onToggle={() => setExpanded(expanded === stage.id ? null : stage.id)}
                expandLabel={t("Explore stage")}
                collapseLabel={t("Close stage")}
                regionLabel={t(stage.title)}
              >
                <p>{t(stage.detail)}</p>
                {stage.id !== "construct" && <p>{t("Model")}: {model}</p>}
              </PipelineNode>
            </div>
          ))}
        </div>
      </div>
      <p className="research-caption">
        {t("Select a stage to explore the published architecture. Configuration selection changes this explanation only; it never executes a pipeline.")}
      </p>
    </div>
  );
}
