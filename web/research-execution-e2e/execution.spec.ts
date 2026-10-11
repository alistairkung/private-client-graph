import { test, expect } from "@playwright/test";

test("configure, freeze, run replay and inspect exact Evidence", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("link", { name: "New experiment", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Review execution" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Review frozen plan" }).click();
  await expect(
    page.getByRole("heading", { name: "Frozen experiment" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "frozen", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Run replay", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "complete", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "complete", exact: true }),
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
  await page.goto("/#new=1");
  await page
    .getByRole("combobox", { name: "Execution mode", exact: true })
    .selectOption("recorded");
  await page
    .getByRole("spinbutton", { name: "Resolver repetitions", exact: true })
    .fill("2");
  await page.getByRole("button", { name: "Review frozen plan" }).click();
  await page
    .getByRole("button", { name: "Run recorded demonstration", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "stopped", exact: true }),
  ).toBeVisible();
  const frozenUrl = page.url();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "stopped", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Review continuation" }).click();
  await expect(page.getByText(/1 recorded attempts remain/)).toBeVisible();
  await page
    .getByRole("button", { name: "Continue offline execution" })
    .click();
  await expect(
    page.getByRole("heading", { name: "complete", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Edit configuration" }).click();
  await expect(
    page.getByRole("spinbutton", { name: "Resolver repetitions", exact: true }),
  ).toHaveValue("2");
  await expect(
    page.getByRole("button", { name: "Review frozen plan" }),
  ).toBeVisible();
  await page.goto(frozenUrl);
  await expect(
    page.getByRole("heading", { name: "complete", exact: true }),
  ).toBeVisible();
});

test("configuration reflows and is operable by keyboard", async ({
  page,
}, info) => {
  await page.goto("/#new=1");
  await expect(
    page.getByRole("heading", { name: "New experiment", exact: true }),
  ).toBeVisible();
  const mode = page.getByRole("combobox", {
    name: "Execution mode",
    exact: true,
  });
  await mode.selectOption("recorded");
  const input = page.getByRole("checkbox", { name: /case_03_fixture/ });
  await input.focus();
  await page.keyboard.press("Space");
  await expect(input).not.toBeChecked();
  await page.keyboard.press("Space");
  await expect(input).toBeChecked();
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
  });
});
