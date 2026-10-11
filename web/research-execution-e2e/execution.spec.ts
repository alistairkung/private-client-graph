import { test, expect } from "@playwright/test";

test("configure, freeze, run replay and inspect exact Evidence", async ({
  page,
}) => {
  await page.goto("/#legacy-new=1");
  // The pipeline workspace is the execution-enabled entry point.
  await expect(
    page.getByRole("heading", { name: "New experiment", exact: true }),
  ).toBeVisible();
  await page
    .getByText("Experiment settings and invocation limits", { exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Review execution" }),
  ).toBeVisible();
  await expect(
    page.getByRole("spinbutton", { name: "Temperature (optional)" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("spinbutton", { name: "Provider timeout (seconds)" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Customize inputs" }).click();
  await page.getByRole("button", { name: "Clear selection" }).click();
  await page.getByRole("checkbox", { name: /case_03_fixture/ }).check();
  await page.getByRole("button", { name: "Apply inputs" }).click();
  // Freezing rebuilds the retained-artifact index and can exceed the UI assertion
  // timeout on CI. Await the command, then verify the resulting page separately.
  const [frozenResponse] = await Promise.all([
    page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname === "/api/research/v1/plans" &&
        response.request().method() === "POST",
      { timeout: 15_000 },
    ),
    page.getByRole("button", { name: "Review frozen plan" }).click(),
  ]);
  expect(frozenResponse.status()).toBe(200);
  await expect(
    page.getByRole("heading", { name: "Frozen experiment" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Execution · frozen", exact: true }),
  ).toBeVisible();
  const inputs = page.getByRole("region", {
    name: "Selected inputs",
    exact: true,
  });
  await expect(inputs).toContainText("case_03_fixture");
  await expect(inputs).toContainText("authored");
  const configuration = page.locator(".frozen-layout");
  const run = page.getByRole("button", { name: "Run replay", exact: true });
  const reviewBounds = await configuration.boundingBox();
  const runBounds = await run.boundingBox();
  expect(runBounds!.y).toBeGreaterThanOrEqual(
    reviewBounds!.y + reviewBounds!.height,
  );
  await expect(
    page.getByText("Plan digest", { exact: true }),
  ).not.toBeVisible();
  await page.getByText("Frozen configuration", { exact: true }).click();
  await page.getByText("Plan identity and digest", { exact: true }).click();
  await expect(page.getByText("Plan digest", { exact: true })).toBeVisible();
  await run.click();
  await expect(
    page.getByRole("heading", { name: "Execution · complete", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Execution · complete", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Inspect persisted results" }).click();
  await expect(
    page.getByText("Saved replay · No resolution · No provider calls."),
  ).toBeVisible();
  await page.getByRole("link", { name: "Investigate", exact: true }).click();
  await page
    .getByRole("link", { name: "Baseline Missing: 1", exact: true })
    .click();
  await page.locator(".relationship-list a").first().click();
  await expect(
    page.getByText("No predicted relationship", { exact: true }),
  ).toBeVisible();
  const quote = await page
    .locator(".evidence-group")
    .filter({ hasText: "Expected Evidence" })
    .locator("blockquote")
    .first()
    .innerText();
  await page
    .getByRole("button", { name: "View expected in Source" })
    .first()
    .click();
  await expect(
    page
      .getByRole("article", { name: "Frozen Source" })
      .locator("mark")
      .first(),
  ).toHaveText(quote);
  await expect(
    page.getByRole("article", { name: "Frozen Source" }),
  ).toBeFocused();
});

test("recorded checkpoint requires explicit continuation and preserves plan when editing", async ({
  page,
}) => {
  await page.goto("/#legacy-new=1");
  await page.getByRole("button", { name: /Extract relationships/ }).click();
  await page
    .getByRole("combobox", { name: "Execution mode", exact: true })
    .selectOption("recorded");
  await page.getByRole("button", { name: /Resolve aliases/ }).click();
  await page
    .getByRole("spinbutton", { name: "Resolver repetitions", exact: true })
    .fill("2");
  await page.getByRole("button", { name: "Customize inputs" }).click();
  await page.getByRole("button", { name: "Clear selection" }).click();
  await page.getByRole("checkbox", { name: /case_03_fixture/ }).check();
  await page.getByRole("button", { name: "Apply inputs" }).click();
  await page.getByRole("button", { name: "Review frozen plan" }).click();
  await page
    .getByRole("button", { name: "Run recorded demonstration", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Execution · stopped", exact: true }),
  ).toBeVisible();
  const frozenUrl = page.url();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Execution · stopped", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Review continuation" }).click();
  await expect(page.getByText(/Provider attempts remaining: 1/)).toBeVisible();
  await page
    .getByRole("button", { name: "Continue offline execution" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Execution · complete", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Edit configuration" }).click();
  await page.getByRole("button", { name: /Resolve aliases/ }).click();
  await expect(
    page.getByRole("spinbutton", { name: "Resolver repetitions", exact: true }),
  ).toHaveValue("2");
  await expect(
    page.getByRole("button", { name: "Review frozen plan" }),
  ).toBeVisible();
  await page.goto(frozenUrl);
  await expect(
    page.getByRole("heading", { name: "Execution · complete", exact: true }),
  ).toBeVisible();
});

test("configuration reflows and is operable by keyboard", async ({
  page,
}, info) => {
  await page.goto("/#legacy-new=1");
  await expect(
    page.getByRole("heading", { name: "New experiment", exact: true }),
  ).toBeVisible();
  const mode = page.getByRole("combobox", {
    name: "Execution mode",
    exact: true,
  });
  await page.getByRole("button", { name: /Extract relationships/ }).click();
  await mode.selectOption("recorded");
  await page.getByRole("button", { name: "Customize inputs" }).click();
  const input = page.getByRole("checkbox", { name: /case_03_fixture/ });
  await input.focus();
  await page.keyboard.press("Space");
  await expect(input).not.toBeChecked();
  await page.keyboard.press("Space");
  await expect(input).toBeChecked();
  await page.getByRole("button", { name: "Apply inputs" }).click();
  await expect(
    page.getByRole("button", { name: "Review frozen plan" }),
  ).toBeEnabled();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `../.impeccable/review/research-execution/configuration-${info.project.name}.png`,
    fullPage: true,
    animations: "disabled",
  });
  await page.getByRole("button", { name: "Review frozen plan" }).focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("button", { name: "Run recorded demonstration" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `../.impeccable/review/research-execution/frozen-${info.project.name}.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("connector rail keeps settings inline and runs into the comparison bench", async ({
  page,
}, info) => {
  await page.goto("/#legacy-new=1");
  await expect(
    page.getByText("6 benchmark inputs selected", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Ready for plan review", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: `../.impeccable/review/workspace/ready-${info.project.name}.png`,
    fullPage: true,
    animations: "disabled",
  });
  const add = page.getByRole("button", {
    name: "Add alias resolution",
    exact: true,
  });
  await add.focus();
  await page.keyboard.press("Enter");
  await page.getByRole("button", { name: "Add generative resolver" }).click();
  await expect(add).toHaveCount(0);
  const resolver = page.getByRole("region", {
    name: "Resolve aliases settings",
    exact: true,
  });
  await expect(resolver).toBeVisible();
  await resolver
    .getByRole("spinbutton", { name: "Resolver repetitions" })
    .fill("2");
  await page.getByRole("button", { name: /Build relationship graph/ }).click();
  await expect(resolver).not.toBeVisible();
  await page.getByRole("button", { name: /Resolve aliases/ }).click();
  await expect(
    resolver.getByRole("spinbutton", { name: "Resolver repetitions" }),
  ).toHaveValue("2");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `../.impeccable/review/workspace/pipeline-${info.project.name}.png`,
    fullPage: true,
    animations: "disabled",
  });
  await page.getByRole("button", { name: "Bypass alias resolution" }).click();
  await expect(add).toBeFocused();
  await page.getByRole("button", { name: /Extract relationships/ }).click();
  await page
    .getByRole("combobox", { name: "Execution mode", exact: true })
    .selectOption("replay");
  await page.getByRole("button", { name: "Customize inputs" }).click();
  await page.getByRole("button", { name: "Clear selection" }).click();
  await expect(
    page.getByRole("button", { name: "Apply inputs" }),
  ).toBeDisabled();
  await page.getByRole("checkbox", { name: /case_03_fixture/ }).check();
  await page.getByRole("button", { name: "Apply inputs" }).click();
  await page.getByRole("button", { name: "Review frozen plan" }).click();
  await page.getByRole("button", { name: "Run replay", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Execution · complete" }),
  ).toBeVisible();
  const planUrl = page.url();
  await page
    .getByRole("link", { name: "Baseline missing: 1", exact: true })
    .click();
  await page.locator(".bench-inspection .relationship-list a").first().click();
  await page
    .getByRole("button", { name: "View expected in Source" })
    .first()
    .click();
  await expect(
    page
      .getByRole("article", { name: "Frozen Source" })
      .locator("mark")
      .first(),
  ).toBeVisible();
  expect(page.url()).toContain("plan=");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `../.impeccable/review/workspace/bench-${info.project.name}.png`,
    fullPage: true,
    animations: "disabled",
  });
  await page.reload();
  await expect(
    page.getByText("No predicted relationship", { exact: true }),
  ).toBeVisible();
  await page.goto(planUrl);
  if (info.project.name === "research-narrow")
    await page
      .getByRole("button", { name: "Experiments", exact: true })
      .click();
  await page
    .getByRole("link", { name: "Legacy study history", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Experiments", exact: true }),
  ).toBeVisible();
});
