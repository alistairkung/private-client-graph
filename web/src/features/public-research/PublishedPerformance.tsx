import { useState } from "react";
import { useLocale } from "../../shared/locale";
import { RunPerformanceChart } from "../../shared/research/RunPerformanceChart";
import type { PublicRun } from "./types";
import { publishedPerformanceRuns } from "./visual-data";

export function PublishedPerformance({ runs }: { runs: PublicRun[] }) {
  const { t } = useLocale();
  const [selected, select] = useState<string | null>(null);
  return <div className="research-figure">
    <RunPerformanceChart
      tactile
      experiment={{ name: t("Published A / A′ / B experiment"), runIds: runs.map(run => run.run_id) }}
      runs={publishedPerformanceRuns(runs, t)} selected={selected} select={select} t={t}
    />
    <aside className="research-figure-notes">
      <strong>{t("Three Runs. Three points.")}</strong>
      <p>{t("Run 1 = A · Fresh extraction")}<br />{t("Run 2 = A′ · Exact replay")}<br />{t("Run 3 = B · Resolution")}</p>
      <p>{t("One point per Run. The 0–1 F1 scale shows recorded scores; selecting a point reveals its identity and coverage.")}</p>
      <p>{t("A and B are Unpriced. Only A′ has a known zero provider cost; missing prices are never treated as zero.")}</p>
    </aside>
  </div>;
}
