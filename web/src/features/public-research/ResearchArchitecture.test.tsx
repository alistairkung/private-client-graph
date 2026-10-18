import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import { LocaleProvider, useLocale } from "../../shared/locale";
import { ResearchArchitecture } from "./ResearchArchitecture";
import { PublishedPerformance } from "./PublishedPerformance";
import { publishedPerformanceRuns } from "./visual-data";
import type { PublicResearchSnapshot } from "./types";

const snapshot: PublicResearchSnapshot = JSON.parse(readFileSync(resolve(import.meta.dirname,
  "../../../../private_client_graph/published/research-results.v1.json"), "utf8"));

it("inspects all three frozen configurations using the Workbench rail without mutation controls", () => {
  const { container } = render(<ResearchArchitecture runs={snapshot.runs} />);
  expect(container.querySelectorAll(".pipeline-connector")).toHaveLength(3);
  expect(container.querySelector(".pipeline-evaluation")).toHaveTextContent("Outside the pipeline");
  const stage = screen.getByRole("button", { name: /Resolve aliases/ });
  fireEvent.click(stage);
  expect(stage).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByRole("region", { name: "Resolve aliases settings" })).toHaveTextContent("Frozen configuration · Read-only");
  for (const label of ["A", "A_prime"]) {
    fireEvent.change(screen.getByLabelText("Inspect Run"), { target: { value: label } });
    expect(screen.queryByRole("button", { name: /Resolve aliases/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Extract relationships/ }));
    expect(screen.getByRole("region", { name: "Extract relationships settings" })).toHaveTextContent(
      label === "A" ? "Ordered Sources · One extraction per case" : "Frozen extractions · No new extraction");
  }
  expect(screen.queryByRole("button", { name: /Execute|Authorize|Add|Bypass/ })).not.toBeInTheDocument();
  expect(screen.queryByRole("spinbutton")).not.toBeInTheDocument();
});

it("copies published scores and nullable costs without recalculating metrics or inventing private scope", () => {
  const runs = publishedPerformanceRuns(snapshot.runs);
  expect(runs.map(run => run.f1)).toEqual(snapshot.runs.map(run => run.metrics.micro_f1));
  expect(runs.map(run => run.cost.total)).toEqual([null, 0, null]);
  expect(runs.map(run => run.eligibility.f1_vs_cost)).toEqual([false, true, false]);
  expect(runs.every(run => run.scopeIdentity === null && run.lifecycle === null)).toBe(true);
  const changed = structuredClone(snapshot.runs);
  changed[0].metrics.micro_f1 = 0;
  expect(publishedPerformanceRuns(changed)[0].f1).toBe(0);
  expect(publishedPerformanceRuns(changed)[0].coverage).toEqual(changed[0].coverage);
});

function LanguageSwitch() {
  const { setLocale } = useLocale();
  return <><button onClick={() => setLocale("en")}>Test English</button><button onClick={() => setLocale("zh-CN")}>Test Chinese</button></>;
}
it("keeps chart selection and filters while translating shared inspection and Unpriced exclusions", () => {
  const { container } = render(<LocaleProvider><LanguageSwitch /><PublishedPerformance runs={snapshot.runs} /><ResearchArchitecture runs={snapshot.runs} /></LocaleProvider>);
  fireEvent.click(screen.getByText("Test English"));
  expect(container.querySelectorAll(".chart-point")).toHaveLength(3);
  const point = screen.getByRole("button", { name: "Run 3, F1 1.000, complete, 10/10 scored" });
  fireEvent.click(point);
  expect(point).toHaveAttribute("aria-pressed", "true");
  expect(container.querySelector(".chart-inspection")).toHaveTextContent(snapshot.runs[2].run_id);
  fireEvent.change(screen.getByLabelText("Input mode"), { target: { value: "fresh" } });
  expect(container.querySelectorAll(".chart-point")).toHaveLength(1);
  fireEvent.change(screen.getByLabelText("Input mode"), { target: { value: "all" } });
  fireEvent.click(screen.getByRole("tab", { name: "F1 vs Cost" }));
  expect(container.querySelectorAll(".chart-point")).toHaveLength(1);
  expect(container.querySelector(".chart-point")).toHaveAttribute("aria-label", "Run 2, F1 0.949, complete, 10/10 scored");
  expect(screen.getAllByText("Unpriced provider attempts; excluded from cost chart.")).toHaveLength(2);
  fireEvent.click(screen.getByText("Test Chinese"));
  expect(screen.getByRole("tab", { name: "F1 与成本" })).toHaveAttribute("aria-selected", "true");
  expect(screen.getAllByText("提供商调用尝试未定价；不纳入成本图表。")).toHaveLength(2);
  expect(container.querySelector(".chart-inspection")).toHaveTextContent(snapshot.runs[2].run_id);
  expect(screen.getByRole("button", { name: /运行 3 · 生成式解析器/ })).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(screen.getByRole("button", { name: /解析别名/ }));
  expect(within(screen.getByRole("region", { name: "解析别名设置" })).getByText(/冻结配置 · 只读/)).toBeVisible();
});
