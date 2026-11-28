import { expect, test } from "@playwright/test";

test("write home reviews and freezes a new experiment, then reuses it from Experiments", async ({ page, request }, info) => {
  const experimentName = `Workbench home replay ${info.project.name}`;
  const writes: string[] = [];
  page.on("request", sent => {
    if (sent.method() !== "GET" && sent.url().includes("/api/research/v2/")) writes.push(new URL(sent.url()).pathname);
  });
  await page.goto("/");
  const navigation = page.getByRole("navigation", { name: "Workbench navigation" });
  await expect(navigation.getByRole("link", { name: "New run" })).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("heading", { name: "New run", exact: true })).toBeVisible();

  const form = page.getByRole("form", { name: "New run setup" });
  await expect(form.getByRole("combobox")).toHaveCount(2);
  await form.getByRole("combobox", { name: "Experiment", exact: true }).selectOption("new");
  const name = form.getByRole("textbox", { name: "Experiment name" });
  await name.fill(experimentName);
  await expect(form.getByRole("combobox", { name: "Run preset" })).toHaveValue("fixtures");
  const review = form.getByRole("button", { name: "Review run" });
  await review.click();
  const dialog = page.getByRole("dialog", { name: "Review run" });
  await expect(dialog).toContainText(experimentName);
  await expect(dialog).toContainText("Provider-free replay");
  expect(writes).toEqual(["/api/research/v2/preview"]);

  await dialog.getByRole("button", { name: "Back to setup" }).click();
  await expect(review).toBeFocused();
  await review.click();
  await dialog.getByRole("button", { name: "Freeze Run" }).click();
  await expect(page.getByRole("dialog", { name: "Ready to start Run 1" })).toBeVisible();
  expect(writes.filter(path => path.endsWith("/experiments"))).toHaveLength(1);
  expect(writes.filter(path => path.endsWith("/runs"))).toHaveLength(1);
  expect(writes.filter(path => /\/(start|authorize)$/.test(path))).toHaveLength(0);

  const experimentId = new URLSearchParams(new URL(page.url()).hash.slice(1)).get("workspace");
  expect(experimentId).toBeTruthy();
  const path = `/api/research/v2/experiments/${experimentId}`;
  const before = await (await request.get(path)).json();
  await page.goto("/#experiments=1");
  await expect(navigation.getByRole("link", { name: "Experiments", exact: true })).toHaveAttribute("aria-current", "page");
  await page.getByRole("searchbox", { name: "Search experiments" }).fill(experimentName);
  const row = page.getByRole("row").filter({ hasText: experimentName });
  await expect(row.getByText("frozen", { exact: true })).toBeVisible();
  await row.getByRole("link", { name: `Use ${experimentName} for new run` }).click();
  await expect(form.getByRole("combobox", { name: "Experiment", exact: true })).toHaveValue(experimentId!);
  await review.click();
  await expect(dialog).toContainText(experimentName);
  const afterReview = await (await request.get(path)).json();
  expect(afterReview.draft.revision).toBe(before.draft.revision);
  await dialog.getByRole("button", { name: "Freeze Run" }).click();
  await expect(page.getByRole("dialog", { name: "Ready to start Run 2" })).toBeVisible();
  expect(writes.filter(write => write.endsWith("/experiments"))).toHaveLength(1);
  expect(writes.filter(write => /\/(start|authorize)$/.test(write))).toHaveLength(0);
});

test("a lost freeze response can be retried without creating another experiment or run", async ({ page, request }) => {
  let received: string | undefined;
  await page.route("**/api/research/v2/experiments/*/runs", async route => {
    if (route.request().method() !== "POST" || received) return route.continue();
    const response = await route.fetch();
    expect(response.ok()).toBeTruthy();
    received = (await response.json()).id;
    await route.fulfill({ status: 502, json: { detail: "The freeze response was interrupted." } });
  });
  await page.goto("/");
  const form = page.getByRole("form", { name: "New run setup" });
  await form.getByRole("combobox", { name: "Experiment", exact: true }).selectOption("new");
  await form.getByRole("textbox", { name: "Experiment name" }).fill("Recovered home replay");
  await form.getByRole("button", { name: "Review run" }).click();
  const dialog = page.getByRole("dialog", { name: "Review run" });
  await dialog.getByRole("button", { name: "Freeze Run" }).click();
  await expect(dialog.getByRole("alert")).toContainText("response was interrupted");
  await dialog.getByRole("button", { name: "Freeze Run" }).click();
  await expect(page.getByRole("dialog", { name: "Ready to start Run 1" })).toBeVisible();
  const params = new URLSearchParams(new URL(page.url()).hash.slice(1));
  expect(params.get("run")).toBe(received);
  const result = await (await request.get(`/api/research/v2/experiments/${params.get("workspace")}`)).json();
  expect(result.run_ids).toEqual([received]);
});

test("live Benchmark v4 presets use ordered inputs and offer only verified extraction origins", async ({ page }) => {
  const experiment = "e".repeat(32);
  const verified = "a".repeat(32);
  const otherScope = "b".repeat(32);
  const commitment = "c".repeat(64);
  const inputs = Array.from({ length: 35 }, (_, index) => ({ sample_id: `sample_${index}` }));
  await page.route("**/api/research/v1/capabilities", async route => {
    const response = await route.fetch();
    await route.fulfill({ json: { ...await response.json(), live_enabled: true, live_task: { task_id: "fixture-task", cap: 72 } } });
  });
  await page.route("**/api/research/v2/benchmark-v4", route =>
    route.fulfill({ json: { sha256: commitment, definition: { input_count: 35 }, inputs } }),
  );
  const title = "Verified extractor example";
  const runIds = [verified, otherScope];
  await page.route("**/api/research/v2/experiments", route => route.fulfill({
    json: { items: [{ id: experiment, name: title, integrity: "verified", read_only_import: false, run_ids: runIds }] },
  }));
  await page.route(`**/api/research/v2/experiments/${experiment}`, route => route.fulfill({
    json: { id: experiment, name: title, read_only_import: false, run_ids: runIds, run_numbers: { [verified]: 1 } },
  }));
  await page.route(`**/api/research/v2/experiments/${experiment}/runs`, route => route.fulfill({
    json: runIds.map(id => ({
      id, experiment_id: experiment, benchmark_v4: { state: "complete" },
      plan: { task_id: "fixture-task", preview: { proposal: {
        execution_mode: "live", benchmark_v4_sha256: id === verified ? commitment : "d".repeat(64),
        input_mode: "fresh", resolver: "none", model: "deepseek-flash", temperature: 0.25, timeout_seconds: 70,
      } } },
    })),
  }));
  await page.route("**/api/research/v2/preview", route =>
    route.fulfill({ status: 422, json: { detail: "No private workload in this browser fixture." } }),
  );

  await page.goto("/");
  const preset = page.getByRole("combobox", { name: "Run preset" });
  await expect(preset).toHaveValue("extract");
  await preset.selectOption("resolve");
  await expect(page.getByText("35 frozen inputs · Uses verified extraction from Run 1")).toBeVisible();
  await expect(page.getByRole("combobox", { name: "Verified extraction" })).toHaveCount(0);
  await page.getByText("Advanced settings").click();
  await page.getByRole("spinbutton", { name: "Maximum provider calls for this invocation" }).fill("3");
  const [preview] = await Promise.all([
    page.waitForRequest(request => new URL(request.url()).pathname === "/api/research/v2/preview"),
    page.getByRole("button", { name: "Review run" }).click(),
  ]);
  expect(preview.postDataJSON()).toMatchObject({
    input_ids: inputs.map(item => item.sample_id), input_mode: "saved", execution_mode: "live",
    resolver: "generative", retained_experiment_id: experiment, retained_run_id: verified,
    invocation_cap: 3, task_call_cap: 72, temperature: 0.25, timeout_seconds: 70,
  });
  await expect(page.getByRole("alert")).toContainText("No private workload in this browser fixture.");
  await page.getByRole("combobox", { name: "Experiment", exact: true }).selectOption("new");
  await expect(preset).toHaveValue("extract");
  expect(await preset.locator('option[value="resolve"]').evaluate((option: HTMLOptionElement) => option.disabled)).toBe(true);
});
