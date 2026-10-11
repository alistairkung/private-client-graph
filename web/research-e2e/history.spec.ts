import { test, expect } from "@playwright/test";

test("history through comparison, individual error and exact frozen Evidence", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("searchbox", { name: "Search experiments" })
    .fill("issue-");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(
    page.getByRole("link", { name: "issue-92-pilot", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("checkbox", {
      name: "Compare issue-91-demonstration",
      exact: true,
    })
    .check();
  await page
    .getByRole("checkbox", { name: "Compare issue-92-pilot", exact: true })
    .check();
  await page
    .getByRole("link", { name: "Compare selected experiments" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Comparison coverage" }),
  ).toBeVisible();
  await expect(page.getByText(/Configuration differs/)).toBeVisible();
  await page
    .getByRole("row")
    .filter({ hasText: "case_03_fixture" })
    .filter({ hasText: "Baseline" })
    .getByRole("link", { name: "Inspect right" })
    .click();
  await page
    .getByRole("link", { name: "Baseline Missing: 1", exact: true })
    .click();
  const missing = page.locator(".relationship-list a").first();
  await expect(missing).toContainText("Missing");
  await missing.click();
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
  await expect(
    page.getByRole("button", { name: /run|authorize|start|stop/i }),
  ).toHaveCount(0);
  await page
    .getByRole("combobox", { name: "Observation", exact: true })
    .selectOption("generative_full_source-1");
  await expect(
    page.getByText("Select a relationship in this result."),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Back to experiments", exact: true })
    .click();
  await expect(
    page.getByRole("searchbox", { name: "Search experiments", exact: true }),
  ).toHaveValue("issue-");
});

test("empty, incomplete and corrupt history remain explicit", async ({
  page,
}) => {
  await page.goto("/#q=not-a-real-experiment");
  await expect(
    page.getByRole("heading", { name: "No matching experiments" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Clear filters" }).click();
  await page
    .getByRole("link", { name: "incomplete-history", exact: true })
    .click();
  await expect(
    page.getByText(/Incomplete experiment\. Unattempted/),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Back to experiments", exact: true })
    .click();
  await page
    .getByRole("link", { name: "corrupt-history", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Artifact cannot be inspected" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /retry|run|start/i }),
  ).toHaveCount(0);
});

test("keyboard navigation, browser history and viewport reflow", async ({
  page,
}) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to workspace" }),
  ).toBeFocused();
  await page.getByRole("link", { name: "issue-92-pilot", exact: true }).click();
  await page.getByRole("link", { name: "Investigate", exact: true }).click();
  await expect(
    page.getByRole("navigation", { name: "Cases and extraction samples" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: "Relationship evaluation", exact: true }),
  ).toBeVisible();
});

test("narrow back controls restore keyboard focus to the parent context", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== "research-narrow",
    "Narrow navigation only",
  );
  await page.goto("/");
  await page.getByRole("link", { name: "issue-92-pilot", exact: true }).click();
  await page.getByRole("link", { name: "Investigate", exact: true }).click();
  await page.getByRole("link", { name: "Back to cases", exact: true }).click();
  await expect(page.locator("#cases summary")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("combobox", { name: "Samples with outcome" }),
  ).toBeFocused();
  await page
    .getByRole("link", { name: "Back to relationships", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Relationship investigation" }),
  ).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Back to cases", exact: true }),
  ).toBeFocused();
});

test("case outcome selection survives view changes", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "issue-92-pilot", exact: true }).click();
  await page.getByRole("link", { name: "Investigate", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Samples with outcome" })
    .selectOption("missing");
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await page.getByRole("link", { name: "Investigate", exact: true }).click();
  await expect(
    page.getByRole("combobox", { name: "Samples with outcome" }),
  ).toHaveValue("missing");
});

test("retained Issue 92 opens directly into the comparison bench and exact Evidence", async ({
  page,
}) => {
  await page.goto("/#q=issue-92");
  await page.getByRole("link", { name: "issue-92-pilot", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Input / cohort", exact: true })
    .selectOption("case_03_fixture");
  await expect(
    page.getByRole("link", { name: "Baseline matched: 6", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Treatment matched: 7", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Treatment repetition", exact: true })
    .selectOption("generative_full_source-3");
  await page
    .getByRole("link", { name: "Baseline missing: 1", exact: true })
    .click();
  await page.locator(".bench-inspection .relationship-list a").first().click();
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
    page.getByRole("combobox", { name: "Treatment repetition", exact: true }),
  ).toHaveValue("generative_full_source-3");
  await expect(
    page.getByRole("button", {
      name: /run|authorize|start|stop|add optional|bypass/i,
    }),
  ).toHaveCount(0);
});
