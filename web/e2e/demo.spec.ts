import { expect, test } from "@playwright/test";

test("public demo journey is isolated, read-only, and reopens a fixed completed example", async ({ page }, testInfo) => {
  const forbidden: string[] = [];
  page.on("request", request => {
    const path = new URL(request.url()).pathname;
    if (request.method() !== "GET" || /^\/(api\/(matters|matter-proposals|session)|auth)(\/|$)/.test(path) || path.endsWith("/analysis")) {
      forbidden.push(`${request.method()} ${path}`);
    }
  });
  await page.goto("/");
  await page.getByRole("link", { name: "Demo application", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Demo Matters", exact: true })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("demo-matter-list.png"), fullPage: true });
  await page.getByRole("link", { name: "DEMO/2026/004 Hillcrest Family Trust" }).last().click();
  await expect(page.getByRole("heading", { name: "Hillcrest Family Trust", exact: true })).toBeVisible();
  await expect(page.getByLabel("Find a relationship")).toBeVisible();
  await page.getByLabel("Find a relationship").selectOption({ index: 1 });
  await expect(page.locator("mark")).toBeVisible();
  const quote = await page.locator("mark").textContent();
  expect(quote).toBeTruthy();
  await page.getByRole("link", { name: "Back to Matters", exact: true }).click();
  await page.getByRole("link", { name: "Create Matter preview", exact: true }).click();
  for (const name of ["External Matter reference", "Matter title", "Authoritative Source title"]) {
    await expect(page.getByLabel(name, { exact: true })).toBeDisabled();
    await expect(page.getByLabel(name, { exact: true })).toHaveValue("");
  }
  await expect(page.locator('input[type="file"]')).toBeDisabled();
  await expect(page.locator('input[type="file"]')).toHaveAttribute("multiple", "");
  await expect(page.getByRole("checkbox")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Upload and analyse unavailable" })).toBeDisabled();
  await page.screenshot({ path: testInfo.outputPath("demo-blank-intake.png"), fullPage: true });
  await page.getByRole("link", { name: "View example proposal" }).click();
  await page.getByLabel("Find a relationship").selectOption({ index: 1 });
  await expect(page.locator("mark")).toHaveText(quote!);
  await expect(page.getByText(/Evidence from Source/)).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("demo-proposal-evidence.png"), fullPage: true });
  await page.getByRole("link", { name: "Preview confirmation", exact: true }).click();
  await expect(page.getByText("This is a preview only. No Matter will be created or changed.", { exact: true })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("demo-confirmation-preview.png"), fullPage: true });
  await page.getByRole("link", { name: "View completed example" }).click();
  await page.getByLabel("Find a relationship").selectOption({ index: 1 });
  await expect(page.locator("mark")).toHaveText(quote!);
  await page.reload();
  await page.getByLabel("Find a relationship").selectOption({ index: 1 });
  await expect(page.locator("mark")).toHaveText(quote!);
  await page.screenshot({ path: testInfo.outputPath("demo-completed-example.png"), fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(forbidden).toEqual([]);
  expect(await page.evaluate(() => Object.keys(localStorage).filter(key => !key.includes("locale")))).toEqual([]);
  expect(await page.evaluate(() => Object.keys(sessionStorage))).toEqual([]);
});

test("public demo deep links refresh and missing examples return to the demo list", async ({ page }) => {
  for (const path of ["/demo", "/demo/matter-proposals/new", "/demo/matter-proposals/hillcrest", "/demo/confirmation/hillcrest", "/demo/matters/hillcrest", "/demo/matters/evergreen"]) {
    await page.goto(path);
    await page.reload();
    await expect(page.getByRole("complementary", { name: "Read-only demo" })).toBeVisible();
  }
  await page.goto("/demo/matters/unknown");
  await expect(page.getByRole("heading", { name: "Demo page not found" })).toBeVisible();
  await page.getByRole("link", { name: "Back to Matters" }).click();
  await expect(page).toHaveURL(/\/demo$/);
});
