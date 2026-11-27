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

test("unified evaluation shows both F1 scores and compares completed evidence assessments", async ({ page }, testInfo) => {
  const graph = (inputs: number) => ({
    inputs, valid_graphs: inputs, without_graph: 0, exact_graphs: 0,
    precision: 105 / 115, recall: 105 / 113, f1: 210 / 228, counts: { tp: 105, fp: 10, fn: 8 }, outcomes: {},
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

  const exactAdjustment = {
    f1: 0.7979152656355077, incomplete_recovered_proofs: 56,
    weight_numerator: 71, weight_denominator: 113, proofs_completed_by_equivalence: 0,
  };
  const assessment: SemanticEvidenceReport = {
    methodology: "Ground-Truth-Aligned Evidence Evaluation", state: "complete", run_id: control, plan_sha256: "fixture", graph_f1: graph(34),
    evidence_adjusted_f1: {
      ...exactAdjustment, f1: 0.7998247328861775, incomplete_recovered_proofs: 55, proofs_completed_by_equivalence: 1,
    },
    scope_note: "Approved members define the comparison. Preserve stated dates, timing and authority.",
    evaluator: { version: "pcg-semantic-evidence-equivalence", prompt_sha256: "prompt", model: "deepseek-v4-pro",
      observation_origin: "offline_fixture",
      settings: { model: "deepseek-v4-pro", temperature: 0, timeout_seconds: 90, max_retries: 0, thinking: "disabled" } },
    target_summary: { formal_targets: 71, pair_verdicts: { Equivalent: 1, "Partially Equivalent": 1 },
      semantic_outcomes: { judged: 1, invalid_judgment: 1, deterministic_delivery_failure: 4, no_eligible_comparison: 65 },
      candidate_pairs: 3,
      evidence_support: { count: 21, targets: 71, rate: 21 / 71 },
      proof_completion: { count: 12, targets: 71, rate: 12 / 71 },
      multi_source_evidence_coverage: { targets: 30, matched_target_equivalents: 13, mean: 13 / 30 },
      exact_matched_members: 25, unmatched_required_members: 100, targets_with_added_matches: 1, additional_matched_members: 1, newly_completed_proofs: 1 },
    operations: { planned_attempts: 2, reserved_attempts: 2, reused_judgments: 0,
      known_estimated_peak_usd: 0.013, reserved_attempts_without_usage: 0, mean_latency_seconds: 2.5 },
    targets: [
      { id: "first", condition: "F0", edge: ["Morgan Example", "trustee_of", "North Example Trust"],
        status: "judged", deterministic: { exact_outcome: "incomplete", joint_only: true, best_exact_pair_coverage: 0.5 },
        members: [
          { id: "M1", source: "S1", source_id: "register", text: "Morgan is the current holder." },
          { id: "M2", source: "S2", source_id: "deed", text: "The appointment took effect on 1 June." },
        ],
        quotations: [
          { id: "Q1", source: "S1", source_id: "register", text: "Morgan is the current holder." },
          { id: "Q2", source: "S2", source_id: "deed", text: "The appointment had effect from the first of June." },
          { id: "Q3", source: "S2", source_id: "deed", text: "The appointment took effect." },
          { id: "Q4", source: "S3", source_id: "memo", text: "An unrelated memorandum mentions Morgan." },
        ],
        exact_matches: { M1: "Q1" }, semantic_members: ["M2"],
        routes: [{ members: ["M1", "M2"], matched_members: ["M1", "M2"], complete: true }],
        candidate_pairs: [{ member_id: "M2", quotation_id: "Q2" }, { member_id: "M2", quotation_id: "Q3" }],
        decisions: [
          { member_id: "M2", quotation_id: "Q2", verdict: "Equivalent", reason: "Same operative date.", material_differences: [] },
          { member_id: "M2", quotation_id: "Q3", verdict: "Partially Equivalent", reason: "The date is missing.", material_differences: ["No effective date in the quoted text."] },
        ], error: null, invalid_response: null, provider: null, reuse: null },
      { id: "invalid", condition: "F1", edge: ["Dana Example", "trustee_of", "North Example Trust"],
        status: "invalid_judgment", deterministic: { exact_outcome: "incomplete", joint_only: false, best_exact_pair_coverage: 0 },
        members: [{ id: "M1", source: "S1", source_id: "register", text: "Dana is the current holder." }],
        quotations: [{ id: "Q1", source: "S1", source_id: "register", text: "Dana is listed as holder." }],
        exact_matches: {}, semantic_members: [], routes: [{ members: ["M1"], matched_members: [], complete: false }],
        candidate_pairs: [{ member_id: "M1", quotation_id: "Q1" }], decisions: [],
        error: "Invalid equivalence judgment schema", invalid_response: '{"verdict":"Supported"}', provider: null, reuse: null },
    ],
  };
  let evaluationReads = 0;
  let selectedState: SemanticEvidenceReport["state"] = "exact_only";
  function selectedReport(): SemanticEvidenceReport {
    if (selectedState === "complete") return {
      ...assessment,
      targets: [assessment.targets[0]],
      target_summary: { ...assessment.target_summary, candidate_pairs: 2,
        semantic_outcomes: { judged: 1, deterministic_delivery_failure: 4, no_eligible_comparison: 66 },
      },
    };
    const exact = selectedState === "exact_only";
    return {
      ...assessment, state: selectedState, plan_sha256: exact ? null : assessment.plan_sha256,
      evidence_adjusted_f1: exactAdjustment,
      operations: exact ? null : assessment.operations,
      target_summary: {
        ...assessment.target_summary,
        evidence_support: { count: 16, targets: 71, rate: 16 / 71 },
        proof_completion: { count: 11, targets: 71, rate: 11 / 71 },
        multi_source_evidence_coverage: { targets: 30, matched_target_equivalents: 12, mean: 0.4 },
      },
    };
  }

  await page.route(`**/semantic-evidence/runs/${control}`, (route) => {
    evaluationReads += 1;
    return route.fulfill({ json: selectedReport() });
  });
  await page.route("**/semantic-evidence/comparison?*", (route) => {
    const comparable = selectedState === "complete";
    const semantic: SemanticComparison = {
      methodology: assessment.methodology, scope_note: assessment.scope_note, comparable,
      evaluator: assessment.evaluator, formal_targets: 71, paired_valid_targets: 1,
      left: { ...assessment, run_id: treatment, evidence_adjusted_f1: exactAdjustment, target_summary: {
        ...assessment.target_summary, evidence_support: { count: 20, targets: 71, rate: 20 / 71 },
        proof_completion: { count: 11, targets: 71, rate: 11 / 71 }, newly_completed_proofs: 0,
      } }, right: selectedReport(),
      transitions: comparable ? [{ id: "first", condition: "F0", edge: assessment.targets[0].edge,
        left: { status: "judged", exact_outcome: "incomplete", complete: false, reused: false },
        right: { status: "judged", exact_outcome: "incomplete", complete: true, reused: false },
        changed_members: [{ member_id: "M2", source_id: "deed", quotation: "The appointment took effect on 1 June.",
          left: "unmatched", right: "semantic" }],
      }] : [],
    };
    return route.fulfill({ json: semantic });
  });

  await page.goto(`/#workspace=${experiment}&run=${control}`);
  await page.getByText("Run history and selection", { exact: true }).click();
  const metric = page.getByRole("combobox", { name: "Performance metric" });
  await metric.selectOption("qualified_graph");
  const graphPoint = page.getByRole("tabpanel", { name: "By Run" }).getByRole("button", {
    name: /^Run \d+, Qualified Graph F1/, pressed: true,
  });
  await graphPoint.focus();
  await expect(graphPoint).toBeFocused();
  await page.getByRole("tab", { name: "By Run" }).press("ArrowRight");
  await expect(page.getByRole("tab", { name: "Vs Cost" })).toBeFocused();
  await expect(metric).toHaveValue("qualified_graph");
  await expect(page.getByRole("heading", { name: "Qualified Graph F1 vs Cost" })).toBeVisible();
  await expect(page).toHaveURL(new RegExp(control + "$"));

  const evaluation = page.getByRole("region", { name: "PCG Evaluation", exact: true });
  await expect(evaluation.getByRole("heading", { name: "PCG Evaluation" })).toBeVisible();
  await expect(evaluation.getByText("Exact-only baseline · combined evaluation pending", { exact: true })).toBeVisible();
  const performance = evaluation.locator("dl[aria-label='Performance metrics']");
  const evidence = evaluation.locator("dl[aria-label='Supporting evidence metrics']");
  await expect(performance.locator("dt")).toHaveText(["Graph F1", "Evidence-Adjusted F1"]);
  await expect(evidence.locator("dt")).toHaveText(["Evidence Support", "Proof Completion", "Multi-Source Evidence Coverage"]);
  await expect(performance.getByText("92.11%", { exact: true })).toBeVisible();
  await expect(performance.getByText("79.79%", { exact: true })).toBeVisible();
  await expect(performance.getByText("56 incomplete recovered proofs · Exact-only")).toBeVisible();
  await expect(evidence.getByText("22.54%", { exact: true })).toBeVisible();
  await expect(evidence.getByText("15.49%", { exact: true })).toBeVisible();
  await expect(evidence.getByText("40.00%", { exact: true })).toBeVisible();
  const matrix = evaluation.getByRole("table", { name: "Relationship confusion matrix · 34 qualified Conditions" });
  await expect(matrix.getByRole("cell", { name: /105 TP/ })).toBeVisible();
  await expect(matrix.getByRole("cell", { name: /10 FP/ })).toBeVisible();
  await expect(matrix.getByRole("cell", { name: /8 FN/ })).toBeVisible();

  const comparator = page.getByRole("combobox", { name: "Compare with verified Run" });
  await comparator.selectOption(treatment);
  const table = page.getByRole("table", { name: "PCG Evaluation comparison" });
  await expect(table.getByRole("row", { name: /Evidence Support/ })).toContainText("22.54%");
  await expect(table.getByRole("columnheader", { name: /Selected Run.*Exact-only baseline/ })).toBeVisible();
  const graphRow = table.getByRole("row", { name: /^Graph F1/ });
  const adjustedRow = table.getByRole("row", { name: /^Evidence-Adjusted F1/ });
  await expect(graphRow.getByRole("cell").last()).toHaveText("0.00 pp");
  await expect(adjustedRow.getByRole("cell").last()).toHaveText("Unavailable");

  selectedState = "pending";
  await evaluation.getByText("Evidence diagnostics", { exact: true }).press("Enter");
  await evaluation.getByRole("button", { name: "Refresh evaluation" }).click();
  await expect(evaluation.getByText("Exact-only baseline · combined evaluation pending or interrupted")).toBeVisible();
  await expect(performance.getByText("79.79%", { exact: true })).toBeVisible();
  await expect(evidence.getByText("15.49%", { exact: true })).toBeVisible();
  await expect(evidence.getByText("16.90%", { exact: true })).toHaveCount(0);

  await evaluation.getByText("Evidence diagnostics", { exact: true }).press("Enter");
  const adjustment = evaluation.locator("dl").filter({ hasText: "Evidence penalty weight (α)" });
  await expect(adjustment.locator("dd")).toHaveText(["71/113", "56", "0", "Exact-only"]);
  await expect(evaluation.getByText(/2\/3 eligible pairs judged · 1 partially equivalent.*1 invalid judgment.*4 delivery failures/)).toBeVisible();
  await expect(evaluation.getByText(/25 exact · 1 equivalent added · 100 unmatched/)).toBeVisible();
  await expect(evaluation.getByText(/2.5s mean latency/)).toBeVisible();
  await evaluation.getByText("Inspect formal targets (2)").press("Enter");
  const filter = evaluation.getByRole("combobox", { name: "Filter formal targets" });
  await filter.selectOption("added");
  await evaluation.getByText(/F0 · Morgan Example.*Complete proof/).press("Enter");
  await expect(evaluation.getByText("The appointment took effect on 1 June.", { exact: true })).toBeVisible();
  await expect(evaluation.getByText("The appointment had effect from the first of June.", { exact: true })).toBeVisible();
  await expect(evaluation.getByText("Exact match · actual PCG quotation · Q1")).toBeVisible();
  await expect(evaluation.getByText("No effective date in the quoted text.")).toBeVisible();
  await expect(evaluation.getByText(/Complete · 2\/2 members matched/)).toBeVisible();
  await evaluation.getByText("Other attached quotations (1)").press("Enter");
  await expect(evaluation.getByText("An unrelated memorandum mentions Morgan.")).toBeVisible();
  await filter.selectOption("invalid_judgment");
  await evaluation.getByText(/F1 · Dana Example.*Incomplete proof/).press("Enter");
  await evaluation.getByText("Retained invalid response", { exact: true }).press("Enter");
  await expect(evaluation.getByText('{"verdict":"Supported"}', { exact: true })).toBeVisible();

  selectedState = "complete";
  await evaluation.getByRole("button", { name: "Refresh evaluation" }).click();
  await expect(evaluation.getByText("Combined evaluation complete", { exact: true })).toBeVisible();
  await expect(performance.getByText("92.11%", { exact: true })).toBeVisible();
  await expect(performance.getByText("79.98%", { exact: true })).toBeVisible();
  await evaluation.getByText("Evidence diagnostics", { exact: true }).press("Enter");
  await expect(adjustment.locator("dd")).toHaveText(["71/113", "55", "1", "Exact and equivalent"]);
  await expect(evidence.getByText("29.58%", { exact: true })).toBeVisible();
  await expect(evidence.getByText("16.90%", { exact: true })).toBeVisible();
  await expect(evidence.getByText("43.33%", { exact: true })).toBeVisible();
  expect(evaluationReads).toBe(3);
  if (testInfo.project.name === "research-desktop") {
    const tops = await performance.locator("dt").evaluateAll((items) => items.map((item) => item.getBoundingClientRect().top));
    expect(new Set(tops).size).toBe(1);
  }

  await page.getByRole("button", { name: "Refresh comparison" }).click();
  const supportRow = table.getByRole("row", { name: /Evidence Support/ });
  await expect(graphRow.getByRole("cell").last()).toHaveText("0.00 pp");
  await expect(adjustedRow.getByRole("cell").last()).toHaveText("+0.19 pp");
  await expect(supportRow.getByRole("cell").nth(0)).toContainText("28.17%");
  await expect(supportRow.getByRole("cell").nth(1)).toContainText("29.58%");
  await expect(supportRow.getByRole("cell").nth(2)).toContainText("+1.41 pp");
  await page.getByText("Evidence comparison diagnostics").press("Enter");
  await page.getByText("F0 · Morgan Example · trustee of · North Example Trust", { exact: true }).press("Enter");
  await expect(page.getByText("M2 · unmatched → semantic")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
});
