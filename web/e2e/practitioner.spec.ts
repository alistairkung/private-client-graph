import { expect, test } from "@playwright/test";

test("empty practitioner shell supports direct entry, refresh, and showcase navigation", async ({ page }, testInfo) => {
  const apiRequests: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/api/")) apiRequests.push(request.url());
  });
  await page.goto("/app");
  await page.reload();
  await expect(page).toHaveTitle("Matters · Private Client Graph");
  await expect(page.getByRole("heading", { name: "Matters", exact: true })).toBeVisible();
  await expect(page.getByText("No Matters available", { exact: true })).toBeVisible();
  await expect(page.getByText("This read-only application does not currently contain any Matters.")).toBeVisible();
  await expect(page.getByRole("navigation").getByRole("link")).toHaveCount(1);
  await expect(page.getByRole("link", { name: "Matters", exact: true })).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("button")).toHaveCount(0);
  expect(apiRequests).toEqual([]);
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.fonts.check('500 32px "Newsreader"'))).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Private Client Graph" })).toBeFocused();
  await page.screenshot({ path: testInfo.outputPath("matters.png"), fullPage: true });
  await page.getByRole("link", { name: "Public showcase" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByLabel("Source document")).toContainText("Attendance Note – Meeting with Alice Chen");
  await expect(page.getByRole("button", { name: "Load sample analysis" })).toBeVisible();
  await page.getByRole("link", { name: "Practitioner application" }).click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByText("No Matters available", { exact: true })).toBeVisible();
});
