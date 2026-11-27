import { expect, test } from "@playwright/test";

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
  await expect(family).toContainText("Complete proofs");
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

test("keeps both measures readable and carries the selected metric between plots", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(`/#workspace=${experiment}&run=${control}`);
  const overview = page.getByRole("region", { name: "Evaluation Protocol v1 results" });
  await expect(overview).toContainText("Evidence-Grounded F1");
  await expect(overview).toContainText("0.00%");
  await page.getByText("Run history and selection", { exact: true }).click();
  const history = page.getByRole("region", { name: "Run history and performance" });
  const metric = history.getByRole("combobox", { name: "Metric" });
  await metric.selectOption("grounded");
  await expect(history.getByRole("heading", { name: "Evidence-Grounded F1 by Run" })).toBeVisible();
  await history.getByRole("tab", { name: "F1 by Run" }).press("ArrowRight");
  await expect(history.getByRole("tab", { name: "F1 vs Cost" })).toBeFocused();
  await expect(metric).toHaveValue("grounded");
  await expect(history.getByRole("heading", { name: "Evidence-Grounded F1 vs Cost" })).toBeVisible();
  await expect(history).toContainText("0/3 Runs plotted");
  const layout = await overview.locator(".run-quality-headlines").evaluate((headlines) => {
    const [graph, grounded] = Array.from(headlines.children, (item) => item.getBoundingClientRect());
    return { fits: headlines.scrollWidth <= headlines.clientWidth, sideBySide: graph.top === grounded.top };
  });
  expect(layout.fits).toBe(true);
  expect(layout.sideBySide).toBe((page.viewportSize()?.width ?? 0) >= 500);
});
