import { expect, test } from "@playwright/test";

test("persisted Matter ledger supports selection, refresh, and showcase navigation", async ({ page }, testInfo) => {
  const apiRequests: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/api/")) apiRequests.push(request.url());
  });
  await page.goto("/app");
  await page.reload();
  await expect(page).toHaveTitle("Matters · Private Client Graph");
  await expect(page.getByRole("heading", { name: "Matters", exact: true })).toBeVisible();
  const matter = page.getByRole("button", { name: "PC/2026/0142 Evergreen Family Trust" });
  await expect(matter).toBeVisible();
  await matter.click();
  await expect(matter).toHaveAttribute("aria-pressed", "true");
  await expect(page).toHaveURL(/\/app$/);
  await matter.press("Space");
  await expect(matter).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByRole("navigation").getByRole("link")).toHaveCount(1);
  await expect(page.getByRole("link", { name: "Matters", exact: true })).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("button")).toHaveCount(1);
  expect(apiRequests.length).toBeGreaterThan(0);
  expect(apiRequests.every(url => new URL(url).pathname === "/api/matters")).toBe(true);
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.fonts.check('500 32px "Newsreader"'))).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole("link", { name: "Private Client Graph" }).focus();
  await expect(page.getByRole("link", { name: "Private Client Graph" })).toBeFocused();
  await page.screenshot({ path: testInfo.outputPath("matters.png"), fullPage: true });
  await page.getByRole("link", { name: "Public showcase" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByLabel("Source document")).toContainText("Attendance Note – Meeting with Alice Chen");
  await expect(page.getByRole("button", { name: "Load sample analysis" })).toBeVisible();
  await page.getByRole("link", { name: "Practitioner application" }).click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(matter).toBeVisible();
});
