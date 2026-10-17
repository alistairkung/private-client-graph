import { test, expect } from "@playwright/test";

test("persistent Experiment: changed and repeated Runs retain frozen Evidence and independent draft", async ({
  page,
}, info) => {
  await page.goto("/");
  await page
    .getByLabel("Experiment name", { exact: true })
    .fill("Does alias resolution improve identity consistency?");
  await page
    .getByLabel("Hypothesis (optional)")
    .fill("Aliases should resolve without losing Evidence.");
  await page
    .getByRole("button", { name: "Create experiment", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Next run", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("5 benchmark inputs selected")).toBeVisible();
  await page.getByRole("button", { name: "Choose cases" }).click();
  await page.getByRole("button", { name: "Clear selection" }).click();
  await page.getByRole("checkbox", { name: /case_03_fixture/ }).check();
  await page.getByRole("button", { name: "Apply cases" }).click();
  let created = 0;
  async function run() {
    await page.getByRole("button", { name: "Run", exact: true }).click();
    await expect(
      page.getByRole("dialog", { name: "Review next Run" }),
    ).toBeVisible();
    const review = page.getByRole("dialog", { name: "Review next Run" });
    await expect(
      review.getByRole("button", { name: "Freeze Run", exact: true }),
    ).toBeInViewport();
    await review
      .getByRole("button", { name: "Freeze Run", exact: true })
      .focus();
    await page.keyboard.press("Tab");
    await expect(
      review.getByRole("button", { name: "Close review" }),
    ).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("button", { name: "Run", exact: true }),
    ).toBeFocused();
    await page.getByRole("button", { name: "Run", exact: true }).click();
    if (info.project.name !== "research-compact")
      await review.screenshot({
        path: `../.impeccable/review/flow-review-${info.project.name}.png`,
      });
    await page
      .getByRole("button", { name: "Freeze Run", exact: true })
      .dblclick();
    const frozen = page.getByRole("dialog", {
      name: /Ready to start Run \d+/,
      exact: true,
    });
    await expect(frozen).toBeVisible();
    created++;
    await expect(frozen).toHaveAccessibleName(`Ready to start Run ${created}`);
    if (created > 1)
      await expect(
        page.locator(".run-inspection > .section-heading h2"),
      ).toHaveText("Run 1 · No resolver");
    if (created === 2 && info.project.name !== "research-compact") {
      await frozen.screenshot({
        path: `../.impeccable/review/flow-frozen-${info.project.name}.png`,
      });
      await page.screenshot({
        path: `../.impeccable/review/flow-distinct-${info.project.name}.png`,
        fullPage: true,
      });
    }
    await page.keyboard.press("Escape");
    await page
      .getByRole("button", { name: "Review frozen Run", exact: true })
      .click();
    await expect(frozen).toBeVisible();
    await expect(
      frozen.getByRole("button", { name: "Start Run", exact: true }),
    ).toBeInViewport();
    await page.getByRole("button", { name: "Start Run", exact: true }).click();
    await expect(
      page.getByRole("heading", {
        name: /Run \d+ · Execution · complete/,
        exact: true,
      }),
    ).toBeVisible();
  }
  await run();
  const firstUrl = page.url();
  const firstId = new URLSearchParams(firstUrl.split("#")[1]).get("run");
  const experiment = new URLSearchParams(firstUrl.split("#")[1]).get(
    "workspace",
  );
  const original = await (
    await page.request.get(
      `/api/research/v2/experiments/${experiment}/runs/${firstId}`,
    )
  ).json();
  await page
    .getByRole("button", { name: "Add alias resolution", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await page
    .getByRole("button", { name: "Add generative resolver", exact: true })
    .click();
  await run();
  await run();
  await expect(page.locator(".chart-point")).toHaveCount(3);
  const history = await (
    await page.request.get(`/api/research/v2/experiments/${experiment}/runs`)
  ).json();
  expect(history).toHaveLength(3);
  expect(history[0].plan).toEqual(original.plan);
  expect(history[0].observations).toEqual(original.observations);
  await page.locator(".chart-point").first().click();
  await expect(
    page.getByRole("heading", { name: "Run 1 · No resolver", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Selected Run evaluation" }),
  ).toBeFocused();
  await expect(
    page.getByRole("heading", { name: "Run 1 · No resolver", exact: true }),
  ).toBeInViewport();
  await expect(page.locator(".run-inspection")).toHaveCount(1);
  await expect(page.locator(".chart-inspection details")).toHaveCount(0);
  const resolverNode = page.getByRole("button", { name: /Resolve aliases/ });
  if ((await resolverNode.getAttribute("aria-expanded")) === "false")
    await resolverNode.click();
  await expect(
    page.getByRole("region", { name: "Resolve aliases settings" }),
  ).toBeVisible();
  await expect(page.getByLabel("Relationship outcome")).not.toBeVisible();
  await page.getByText("Observations & Evidence", { exact: true }).click();
  await page.getByLabel("Relationship outcome").selectOption("missing");
  await page
    .locator(".observation-bench .relationship-list button")
    .first()
    .click();
  if (info.project.name === "research-narrow") {
    const evidence = page.getByRole("region", {
      name: "Selected relationship Evidence",
    });
    await expect(evidence).toBeFocused();
    await expect(evidence).toBeInViewport();
    await page.getByRole("link", { name: "Back to relationships" }).click();
    await expect(
      page.locator(".observation-bench .relationship-list button").first(),
    ).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(evidence).toBeFocused();
  }
  await expect(
    page.getByText("No predicted relationship", { exact: true }),
  ).toBeVisible();
  const expected = await page
    .locator(".evidence-group blockquote")
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
  ).toHaveText(expected);
  await page.getByRole("button", { name: "Use as next draft" }).click();
  await expect(
    page.getByRole("button", { name: "Add alias resolution", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Run", exact: true }),
  ).toBeEnabled();
  await page.reload();
  await expect(page.locator(".chart-point")).toHaveCount(3);
  await expect(
    page.getByRole("button", { name: "Add alias resolution", exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "F1 vs Cost" }).click();
  await expect(page.locator(".chart-point")).toHaveCount(3);
  await page.getByRole("tab", { name: "F1 by Run" }).click();
  await page.getByText("Cost and comparison", { exact: true }).click();
  await page.getByLabel("Compare with Run").selectOption(history[1].id);
  await expect(page.getByText(/Comparable benchmark scope/)).toBeVisible();
  await page.getByText("Cost and comparison", { exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Run", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText("Checking draft…", { exact: true })).toHaveCount(
    0,
  );
  await expect(
    page.getByRole("navigation", {
      name: "Experiments",
      exact: true,
      includeHidden: true,
    }),
  ).toBeAttached();
  await page.evaluate(() => window.scrollTo(0, 0));
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  if (info.project.name !== "research-compact")
    await page.screenshot({
      path: `../.impeccable/review/flow-${info.project.name}.png`,
      fullPage: true,
      animations: "disabled",
    });
});

test("sidebar preserves wide preference and traps focus in narrow drawer", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await page.getByRole("button", { name: "Collapse experiments" }).click();
  await expect(page.locator("#experiment-sidebar")).not.toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  const trigger = page.getByRole("button", {
    name: "Experiments",
    exact: true,
  });
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "Experiments", exact: true });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("link", { name: "Legacy study history" }).focus();
  await page.keyboard.press("Tab");
  expect(
    await dialog.evaluate((element) =>
      element.contains(document.activeElement),
    ),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
  await trigger.click();
  await dialog.getByRole("link", { name: "Legacy study history" }).click();
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(
    page.getByRole("button", { name: "Expand experiments" }),
  ).toHaveAttribute("aria-expanded", "false");
});

test("compact insertion preserves rail height and keeps its option visible", async ({
  page,
}, info) => {
  await page.goto("/");
  await page
    .getByLabel("Experiment name", { exact: true })
    .fill("Compact insertion review");
  await page
    .getByRole("button", { name: "Create experiment", exact: true })
    .click();
  await page.getByRole("button", { name: "Run", exact: true }).waitFor();
  const rail = page.locator(".pipeline-rail");
  const before = await rail.boundingBox();
  await page
    .getByRole("button", { name: "Add alias resolution", exact: true })
    .click();
  const menu = page.locator(".resolver-menu");
  await expect(menu).toBeVisible();
  expect((await rail.boundingBox())!.height).toBeLessThanOrEqual(
    Math.max(before!.height, 210),
  );
  await expect(menu.getByRole("button")).toHaveCount(1);
  const popup = (await menu.boundingBox())!;
  const frame = (await page.locator(".pipeline-viewport").boundingBox())!;
  expect(popup.x).toBeGreaterThanOrEqual(frame.x);
  expect(popup.x + popup.width).toBeLessThanOrEqual(frame.x + frame.width);
  if (info.project.name !== "research-compact")
    await page.locator(".pipeline-viewport").screenshot({
      path: `../.impeccable/review/flow-insert-${info.project.name}.png`,
    });
  await page.keyboard.press("Escape");
  await expect(menu).toHaveCount(0);
});

test("opens the frozen Run review when polling arrives before its freeze response", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByLabel("Experiment name", { exact: true })
    .fill("Freeze response ordering");
  await page
    .getByRole("button", { name: "Create experiment", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Next run", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Choose cases" }).click();
  await page.getByRole("button", { name: "Clear selection" }).click();
  await page.getByRole("checkbox", { name: /case_01_fixture/ }).check();
  await page.getByRole("button", { name: "Apply cases" }).click();
  await page.getByRole("button", { name: "Run", exact: true }).click();
  await expect(
    page.getByRole("dialog", { name: "Review next Run" }),
  ).toBeVisible();

  await page.route("**/api/research/v2/experiments/*/runs", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    const response = await route.fetch();
    // Publish the Run, then let ordinary polling mount it before acknowledging freeze.
    await expect(
      page.getByRole("heading", {
        name: "Run 1 · Execution · frozen",
        exact: true,
      }),
    ).toBeVisible();
    await route.fulfill({ response });
  });
  // The route deliberately waits for a polling/render cycle. Start the dialog
  // assertion after that response, so its timeout measures the UI transition.
  const freezeResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      /\/api\/research\/v2\/experiments\/[^/]+\/runs$/.test(response.url()),
  );
  await page.getByRole("button", { name: "Freeze Run", exact: true }).click();
  await freezeResponse;

  const review = page.getByRole("dialog", {
    name: "Ready to start Run 1",
    exact: true,
  });
  await expect(review).toBeVisible();
  await expect(
    review.getByRole("heading", {
      name: "Ready to start Run 1",
      exact: true,
    }),
  ).toBeFocused();
  await expect(
    review.getByRole("button", { name: "Start Run", exact: true }),
  ).toBeEnabled();
});
