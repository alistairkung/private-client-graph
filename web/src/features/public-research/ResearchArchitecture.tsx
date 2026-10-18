import { useState } from "react";
import { useLocale } from "../../shared/locale";
import { AnalysisPipeline } from "../../shared/research/AnalysisPipeline";
import { runName } from "./RunComparison";
import { ResearchRunSwitch } from "./ResearchRunSwitch";
import type { PublicRun, RunLabel } from "./types";
import { publishedPipeline } from "./visual-data";

export function ResearchArchitecture({ runs }: { runs: PublicRun[] }) {
  const { t } = useLocale();
  const [label, setLabel] = useState<RunLabel>("B");
  const run = runs.find(value => value.label === label);
  if (!run) return null;
  return <div className="research-figure">
    <div className="research-figure-controls">
      <strong>{t("Published configuration")}</strong>
      <ResearchRunSwitch
        label={t("Inspect Run")}
        value={label}
        onChange={setLabel}
        options={runs.map(value => ({
          value: value.label,
          label: `${runName(value.label)} · ${t(value.label === "A" ? "Fresh baseline" : value.label === "A_prime" ? "Exact replay" : "With resolver")}`,
        }))}
      />
    </div>
    <AnalysisPipeline key={label} configuration={publishedPipeline(run, runs, t)} appearance="persistent" t={t} />
    <aside className="research-figure-notes">
      <strong>{t("The same chain.")}</strong>
      <p>{t("Inspect A, A′ or B. Select a stage to explore its frozen configuration.")}</p>
      <p>{t("A′ reuses A’s frozen extractions. B adds resolution to those same records; construction and evaluation remain deterministic.")}</p>
    </aside>
  </div>;
}
