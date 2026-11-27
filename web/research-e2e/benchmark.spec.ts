import { expect, test } from "@playwright/test";
import type { BenchmarkV4Comparison, BenchmarkV4Summary, EvidenceQuality, SemanticEvidenceReport, SemanticComparison } from "../research/shared/contracts";

const experiment = "e".repeat(32);
const control = "1".repeat(32);
const treatment = "2".repeat(32);
const reordered = "3".repeat(32);
const workspace = `/api/research/v2/experiments/${experiment}`;

test("read-only import exposes protocol metrics, proof, unavailable and empty graphs", async ({
  page,
  request,
}) => {
  await page.goto(`/#workspace=${experiment}&run=${control}`);
  await expect(
    page.getByRole("heading", { name: /Benchmark v3/, level: 2 }),
  ).toBeVisible();
  const matrix = page.getByRole("table", {
    name: "Relationship confusion matrix · All conditions",
  });
  await expect(matrix).toBeVisible();
  const family = page.getByRole("button", { name: /Family F\b/ });
  await expect(family).toContainText("Identify the current trustee");
  await expect(family).toContainText("Proof Completion");
  await family.press("Enter");
  await expect(matrix).toHaveCount(1);
  await expect(page.getByRole("tab", { name: /F0/ })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  const expected = page.getByRole("region", {
    name: "Expected graph",
    exact: true,
  });
  await expected
    .getByRole("button", {
      name: /Morgan Example.*trustee of.*North Example Trust/i,
    })
    .press("Enter");
  const proof = page.getByRole("region", {
    name: "Sufficient Evidence Alternatives",
  });
  await expect(proof.getByText("Quotation differs")).toBeVisible();
  await expect(proof.getByText("Morgan was nominated earlier.")).toBeVisible();
  const member = proof.getByRole("button", {
    name: /Read approved quotation from register/i,
  });
  await member.press("Enter");
  const reader = page.getByRole("region", { name: "Source reader" });
  await expect(reader.locator("mark")).toHaveText(
    "Morgan is the current holder.",
  );
  await reader.getByRole("button", { name: "Close reader" }).press("Enter");
  await expect(member).toBeFocused();
  await proof.getByRole("button", { name: /Alternative 2,/ }).press("Enter");
  await expect(
    proof.getByText("Source missing from this relationship"),
  ).toBeVisible();

  await page.getByRole("tab", { name: /F0/ }).press("ArrowRight");
  await expect(page.getByRole("tab", { name: /F1/ })).toBeFocused();
  await expect(
    page.getByText("Prediction unavailable", { exact: true }).first(),
  ).toBeVisible();
  await expect(expected).toBeVisible();
  await expect(proof).toHaveCount(0);
  const failure = page.getByRole("region", { name: "Unavailable prediction" });
  await failure.getByText(/Retained candidates/).click();
  await expect(
    failure.getByRole("list", { name: "Parsed candidates" }),
  ).toContainText("Invalid quote absent from the Source.");
  await failure.getByText(/Frozen Sources/).click();
  await failure
    .getByRole("combobox", { name: "Source in retained order" })
    .selectOption("1");
  await expect(
    failure.getByRole("region", { name: "Full frozen Source" }),
  ).toContainText("Morgan was nominated earlier.");

  await page.getByRole("button", { name: /Family G\b/ }).press("Enter");
  const switchSide = page.getByRole("button", {
    name: "Predicted",
    exact: true,
  });
  if (await switchSide.isVisible()) await switchSide.click();
  await expect(
    page.getByRole("region", { name: "Predicted graph", exact: true }),
  ).toContainText(/graph constructed · 0 relationships/i);
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(await page.evaluate(() => window.innerWidth + 1));
  await expect(page).toHaveURL(new RegExp(control + "$"));

  expect(
    (
      await request.post(`${workspace}/runs/${control}/start`, { data: {} })
    ).status(),
  ).toBe(404);
  expect((await request.put(`${workspace}/draft`, { data: {} })).status()).toBe(
    404,
  );
  await expect(
    page.getByRole("button", { name: "Use as next draft" }),
  ).toHaveCount(0);
});

test("graph comparison uses the available width and keeps the inspected view through reflow", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 1560, height: 960 });
  await page.goto(`/#workspace=${experiment}&run=${control}`);
  await page.getByRole("button", { name: /Family F\b/ }).click();

  const comparison = page.getByRole("region", {
    name: "Environment Condition F0 graph comparison",
  });
  const expected = comparison.getByRole("region", { name: "Expected graph" });
  const predicted = comparison.getByRole("region", { name: "Predicted graph", includeHidden: true });
  const canvas = expected.getByRole("region", { name: "Relationship graph" });
  const options = comparison.getByText("Graph options", { exact: true });
  await options.click();
  const isolated = comparison.getByRole("checkbox", { name: /Show isolated entities/ });
  const graphNodes = canvas.locator(".react-flow__node");
  await expect(graphNodes).toHaveCount(2);
  await expect(isolated).not.toBeChecked();
  await comparison.getByText(/Expected Matter roster/).click();
  const roster = comparison.getByRole("list", { name: "Expected entities" });
  await expect(roster).toContainText("Dakota Example");
  const rosterBox = (await roster.boundingBox())!;
  const graphBox = (await expected.boundingBox())!;
  expect(rosterBox.y + rosterBox.height).toBeLessThanOrEqual(graphBox.y);

  await isolated.check();
  await expect(graphNodes).toHaveCount(3);
  await expect(predicted.locator(".react-flow__node")).toHaveCount(2);
  await isolated.uncheck();
  await expect(graphNodes).toHaveCount(2);
  await options.click();

  const compositionWidth = () => comparison.evaluate((el) => el.getBoundingClientRect().width);
  const availableWidth = () => comparison.evaluate((el) => el.parentElement!.clientWidth);
  expect(await compositionWidth()).toBeGreaterThan(900);
  expect(await compositionWidth()).toBeCloseTo(await availableWidth(), 0);
  expect((await expected.boundingBox())?.width).toBeCloseTo((await predicted.boundingBox())!.width, 0);

  const zoom = () => canvas.locator(".react-flow__viewport").evaluate((el) =>
    new DOMMatrixReadOnly(getComputedStyle(el).transform).a,
  );
  await canvas.getByRole("button", { name: "Fit graph" }).click();
  const fittedZoom = await zoom();
  await canvas.getByRole("button", { name: "Zoom out" }).click();
  await expect.poll(zoom).toBeLessThan(fittedZoom);
  const inspectedZoom = await zoom();

  const edge = canvas.getByRole("button", { name: /Morgan Example.*trustee of.*North Example Trust/i });
  await edge.press("Enter");
  const evidence = comparison.getByRole("region", { name: "Selected relationship evidence", exact: true });
  await expect(evidence).toContainText("Morgan Example");
  const list = comparison.getByRole("region", { name: "Relationship list" });
  const selected = list.getByRole("button", { name: /Morgan Example.*trustee of/ });
  await expect(selected).toHaveAttribute("aria-pressed", "true");
  const label = selected.getByText("Morgan Example", { exact: true });
  const labelColor = await label.evaluate((element) => getComputedStyle(element).color);
  await selected.hover();
  await expect(label).toHaveCSS("color", labelColor);
  await list.getByRole("button", { name: /Locate Morgan Example/ }).click();
  await expect(edge).toBeFocused();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(comparison.getByRole("button", { name: "Predicted", exact: true })).toBeVisible();
  await expect(predicted).toBeHidden();
  expect((await expected.boundingBox())?.width).toBeCloseTo(await compositionWidth(), 0);
  await expect.poll(zoom).toBeCloseTo(inspectedZoom, 3);
  await comparison.getByRole("button", { name: /^Relationships/ }).click();
  await expect(evidence).toContainText("Morgan Example");
  await comparison.getByRole("button", { name: "Graphs", exact: true }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth))
    .toBeLessThanOrEqual(391);

  await page.setViewportSize({ width: 1560, height: 960 });
  await expect(predicted).toBeVisible();
  await expect.poll(zoom).toBeCloseTo(inspectedZoom, 3);
  await canvas.getByRole("button", { name: "Fit graph" }).click();
  await expect.poll(zoom).toBeCloseTo(fittedZoom, 3);
});

test("compatible imports compare the full roster and changed order withholds deltas", async ({
  page,
  request,
}) => {
  const compared = await request.get(
    `${workspace}/comparison?left=${control}&right=${treatment}`,
  );
  expect(compared.ok()).toBeTruthy();
  const compatible = await compared.json();
  expect(compatible.comparable_scope).toBe(true);
  expect(
    compatible.benchmark.conditions.map(
      (row: { condition: string }) => row.condition,
    ),
  ).toEqual(["F0", "F1", "G0"]);
  expect(compatible.benchmark.conditions[1]).toMatchObject({
    left_outcome: "validation_failure",
    right_outcome: "not_attempted",
    fn: 0,
  });

  await page.goto(`/#workspace=${experiment}&run=${control}`);
  const comparator = page.getByRole("combobox", {
    name: /Compare with (?:verified )?Run/,
  });
  await comparator.selectOption(treatment);
  await expect(
    page.getByRole("heading", { name: /Condition-aligned comparison/ }),
  ).toBeVisible();
  await expect(
    page.getByText(
      /validation failure.*not attempted|not attempted.*validation failure/i,
    ),
  ).toBeVisible();
  await comparator.selectOption(reordered);
  await expect(
    page.getByText(/order of the planned Conditions differs/i),
  ).toBeVisible();
  await expect(page.getByText(/deltas withheld/i)).toBeVisible();
});

test("evidence quality controls and comparison fit the viewport and retain keyboard selection", async ({ page }) => {
  const graph = (inputs: number) => ({
    inputs, valid_graphs: inputs, without_graph: 0, exact_graphs: 0,
    precision: 1, recall: 0.5, f1: 2 / 3, counts: { tp: 2, fp: 0, fn: 2 }, outcomes: {},
  });
  const quality: EvidenceQuality = {
    version: "deterministic_evidence_quality_v1", state: "complete",
    scope_sha256: "fixture", scoring_sha256: "fixture", qualified_reference_sha256: "fixture",
    observation_origin: "offline_fixture",
    planned_inputs: 35, observed_inputs: 35, qualified_inputs: 34, observed_qualified_inputs: 34,
    expected_relationships: 113, observed_proof_targets: 71, observed_joint_targets: 30,
    combined_graph: graph(35), qualified_graph: graph(34),
    complete_proof: { complete: 11, targets: 71, rate: 11 / 71 },
    joint_only_complete_proof: { complete: 1, targets: 30, rate: 1 / 30 },
    joint_only_coverage: { targets: 30, mean: 0.4 },
  };
  const summary: BenchmarkV4Summary = {
    scope_sha256: quality.scope_sha256, scoring_sha256: quality.scoring_sha256,
    observation_origin: quality.observation_origin, state: quality.state,
    combined: quality.combined_graph, qualified: quality.qualified_graph,
    consensus: graph(1), by_matter: {},
    consensus_evidence: { adjudicated_relationships: 6, reference_citations: 8, matched_citations: 4, assessed: true },
  };
  // The browser server retains the v3 fixture. Add only the v4 reporting payload
  // to its real reads so this test can exercise viewport and keyboard behavior.
  await page.route(`**${workspace}/runs/*`, async (route) => {
    const response = await route.fetch();
    if (!response.ok() || ![control, treatment].some((id) => new URL(route.request().url()).pathname.endsWith(id))) {
      await route.fulfill({ response });
      return;
    }
    await route.fulfill({ response, json: { ...await response.json(), benchmark_v4: summary, quality } });
  });
  await page.route(`**${workspace}/comparison?*`, async (route) => {
    const response = await route.fetch();
    const comparison: BenchmarkV4Comparison = {
      left: summary, right: summary, left_proofs: null, right_proofs: null,
      left_usage: null, right_usage: null, shared_extraction_run_id: null,
      left_quality: quality, right_quality: quality,
      quality_delta: { combined_graph: 0, qualified_graph: 0, complete_proof: 0, joint_only_coverage: 0 },
    };
    await route.fulfill({ response, json: { ...await response.json(), benchmark_v4: comparison } });
  });

  const assessment: SemanticEvidenceReport = {
    status: "Exploratory and unverified", run_id: control, plan_sha256: "fixture",
    temporal_limitation: "Benchmark v4 targets have no explicit assessment cutoff. Temporal correctness at that cutoff remains unverified.",
    evaluator: { version: "pcg-semantic-evidence-v1", prompt_sha256: "prompt", model: "deepseek-v4-pro",
      observation_origin: "offline_fixture",
      settings: { model: "deepseek-v4-pro", temperature: 0, timeout_seconds: 90, max_retries: 0, thinking: "disabled" } },
    target_summary: { formal_targets: 71, recovered_targets: 67, verdicts: { Supported: 1 },
      semantic_outcomes: { judged: 1, invalid_judgment: 1, unattempted: 65, deterministic_delivery_failure: 4 },
      flags: { potentially_sufficient_overlooked_by_exact_matching: 1 },
      potentially_sufficient_overlooked_by_exact_matching: { count: 1, formal_target_denominator: 71,
        recovered_exact_incomplete_denominator: 56, recovered_exact_incomplete_judged: 1 } },
    operations: { planned_attempts: 69, reserved_attempts: 2, reused_judgments: 0,
      known_estimated_peak_usd: 0.013, reserved_attempts_without_usage: 0, mean_latency_seconds: 2.5 },
    controls: [],
    targets: [
      { id: "first", condition: "F0", edge: ["Morgan Example", "trustee_of", "North Example Trust"],
        status: "judged", flags: ["potentially_sufficient_overlooked_by_exact_matching", "joint_only_supported_with_one_cited_source"], control: null,
        deterministic: { exact_outcome: "incomplete", joint_only: true, best_exact_pair_coverage: 0.5,
          matches_any_approved_pair: [], approved_route_source_set_present: false },
        quotations: [{ id: "Q1", source: "S1", source_id: "register", text: "Morgan is the current holder." }],
        judgment: { verdict: "Supported", facts: [
          { fact: "relationship", status: "satisfied", quotation_ids: ["Q1"], reason: "The register identifies the current holder." },
          { fact: "timing", status: "satisfied", quotation_ids: ["Q1"], reason: "The register identifies the holder as current." },
        ] }, error: null, invalid_response: null, provider: null, reuse: null },
      { id: "invalid", condition: "F1", edge: ["Dana Example", "trustee_of", "North Example Trust"],
        status: "invalid_judgment", flags: [], control: null, deterministic: null, quotations: [],
        judgment: null, error: "Invalid judgment schema", invalid_response: '{"verdict":"unsupported"}',
        provider: null, reuse: null },
    ],
  };
  let semanticReads = 0;
  await page.route(`**/semantic-evidence/runs/${control}`, async (route) => {
    semanticReads += 1;
    await route.fulfill({ json: assessment });
  });
  const semantic: SemanticComparison = {
    status: assessment.status, temporal_limitation: assessment.temporal_limitation,
    evaluator: assessment.evaluator, formal_targets: 71, paired_valid_targets: 1,
    left: { ...assessment, run_id: treatment }, right: assessment,
    transitions: [{ id: "first", condition: "F0", edge: assessment.targets[0].edge,
      left: { status: "judged", verdict: "Partially Supported", exact_outcome: "incomplete",
        potentially_sufficient: false, reused: false },
      right: { status: "judged", verdict: "Supported", exact_outcome: "incomplete",
        potentially_sufficient: true, reused: false },
      facts_comparable: true, changed_facts: [
        { fact: "relationship", left: "missing", right: "satisfied" },
        { fact: "timing", left: "missing", right: "satisfied" },
      ],
    }],
  };
  await page.route("**/semantic-evidence/comparison?*", (route) => route.fulfill({ json: semantic }));

  await page.goto(`/#workspace=${experiment}&run=${control}`);
  await page.getByText("Run history and selection", { exact: true }).click();
  const metric = page.getByRole("combobox", { name: "Performance metric" });
  await metric.selectOption("joint_only_coverage");
  const coveragePoint = page.getByRole("tabpanel", { name: "By Run" }).getByRole("button", {
    name: /^Run \d+, Multi-Source Evidence Coverage/,
    pressed: true,
  });
  await coveragePoint.focus();
  await expect(coveragePoint).toBeFocused();
  await expect(coveragePoint).toHaveAccessibleDescription(/Average percentage of required evidence recovered for relationships that need multiple Sources\. Uses the best-matching approved proof route\./);

  const runTab = page.getByRole("tab", { name: "By Run" });
  await runTab.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "Vs Cost" })).toBeFocused();
  await expect(metric).toHaveValue("joint_only_coverage");
  await expect(metric).toHaveAccessibleDescription("30 multi-Source proof targets · qualified cohort");
  await expect(page.getByRole("heading", { name: "Multi-Source Evidence Coverage vs Cost" })).toBeVisible();
  await expect(page).toHaveURL(new RegExp(control + "$"));

  await page.getByRole("combobox", { name: "Compare with verified Run" }).selectOption(treatment);
  const table = page.getByRole("table", { name: "Evidence quality comparison" });
  await expect(table.getByRole("row", { name: /Proof Completion.*qualified cohort/ })).toBeVisible();
  await expect(table.getByRole("row", { name: /Multi-Source Evidence Coverage/ })).toBeVisible();
  for (const element of [metric, table]) {
    expect(await element.evaluate((node) => {
      const { left, right } = node.getBoundingClientRect();
      return left >= 0 && right <= window.innerWidth + 1;
    })).toBe(true);
  }

  const protocol = page.getByRole("region", { name: "Evaluation Protocol v1 results" });
  await expect(protocol.getByText("15.49%", { exact: true })).toBeVisible();
  await expect(protocol.getByText("11 of 71 formal targets", { exact: false })).toBeVisible();
  await expect(protocol.getByText("1 / 30", { exact: true })).toBeVisible();
  await expect(protocol.getByText("40.00%", { exact: true })).toBeVisible();
  const semanticSummary = protocol.getByRole("region", { name: "Semantic Evidence — AI-assessed, unverified" });
  await expect(semanticSummary.getByText("1 / 71", { exact: true })).toBeVisible();
  await expect(semanticSummary.getByText("Potentially sufficient missed proofs")).toBeVisible();
  await expect(semanticSummary.getByText("0 targets with potential partial support beyond exact matches")).toBeVisible();
  await expect(semanticSummary.getByText(/1 invalid judgment.*4 delivery failures/)).toBeVisible();
  await expect(semanticSummary.getByText("Timing unverified.")).toBeVisible();
  await expect(semanticSummary.getByText("Inspect formal targets (2)")).not.toBeVisible();
  expect(semanticReads).toBe(1);

  await semanticSummary.getByText("Inspect semantic assessment", { exact: true }).press("Enter");
  await expect(semanticSummary.getByText(assessment.temporal_limitation)).toBeVisible();
  await semanticSummary.getByText("Inspect formal targets (2)").press("Enter");
  expect(semanticReads).toBe(1);
  const filter = page.getByRole("combobox", { name: "Filter formal targets" });
  await filter.selectOption("Supported");
  await page.getByText(/F0 · Morgan Example.*Supported/).press("Enter");
  await expect(page.getByText("Morgan is the current holder.", { exact: true })).toBeVisible();
  await expect(page.getByText("The register identifies the current holder.", { exact: false })).toBeVisible();
  await expect(page.getByText("timing (assessment cutoff unavailable) · satisfied", { exact: true })).toBeVisible();
  await expect(page.getByText(/Multi-Source Evidence Coverage 50.0%/)).toBeVisible();
  await expect(page.getByText("Multi-Source target · Supported using one cited Source")).toBeVisible();
  await filter.selectOption("invalid_judgment");
  await page.getByText(/F1 · Dana Example.*Invalid judgment/).press("Enter");
  await page.getByText("Retained invalid response", { exact: true }).press("Enter");
  await expect(page.getByText('{"verdict":"unsupported"}', { exact: true })).toBeVisible();

  await page.getByText("Semantic Evidence — AI-assessed, unverified comparison", { exact: true }).press("Enter");
  await expect(page.getByText("1/71 formal targets have two valid judgments.")).toBeVisible();
  await page.getByText("F0 · Morgan Example · trustee of · North Example Trust", { exact: true }).press("Enter");
  await expect(page.getByText("relationship · missing → satisfied")).toBeVisible();
  await expect(page.getByText("timing (assessment cutoff unavailable) · missing → satisfied")).toBeVisible();
  await expect(page.getByText(assessment.temporal_limitation)).toHaveCount(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
});
