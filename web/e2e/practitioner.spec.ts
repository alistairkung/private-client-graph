import { expect, test } from "@playwright/test";

const matterPath = "/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369";

test("persisted Matter opens from ledger and highlights exact Evidence after direct entry and refresh", async ({ page }, testInfo) => {
  const apiRequests: string[] = [];
  page.on("request", request => {
    const path = new URL(request.url()).pathname;
    if (path.startsWith("/api/")) apiRequests.push(path);
  });
  await page.goto("/app");
  await expect(page).toHaveTitle("Matters · Private Client Graph");
  const matter = page.getByRole("link", { name: "PC/2026/0142 Evergreen Family Trust" });
  await expect(matter).toHaveAttribute("href", matterPath);
  await matter.focus();
  await matter.press("Enter");
  await expect(page).toHaveURL(matterPath);
  await expect(page.getByRole("heading", { name: "Evergreen Family Trust", exact: true })).toBeVisible();
  await expect(page.getByText("Matter reference: PC/2026/0142")).toBeVisible();
  await page.goto(matterPath);
  await page.reload();
  await expect(page).toHaveTitle("Evergreen Family Trust · Private Client Graph");
  await expect(page.getByRole("img", { name: "Triangular Trust node" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Matters", exact: true })).toHaveAttribute("aria-current", "page");
  const edge = page.getByRole("button", { name: "Alice Chen — Spouse of — David Chen", exact: true });
  await edge.getByText("Spouse of", { exact: true }).click();
  await expect(edge).toHaveClass(/selected/);
  const highlight = page.locator("mark");
  await expect(highlight).toHaveText("Alice Chen confirmed that she and David Chen are spouses.");
  await expect(highlight).toBeInViewport();
  await expect(page.getByRole("button", { name: /Evidence 1/ })).toHaveAttribute("aria-pressed", "true");
  const parent = page.getByRole("button", { name: "Alice Chen — Parent of — Bob Chen", exact: true });
  await parent.focus();
  await parent.press("Enter");
  await expect(parent).toHaveClass(/selected/);
  await expect(edge).not.toHaveClass(/selected/);
  await expect(highlight).toHaveText("Alice Chen confirmed that Alice Chen and David Chen are the parents of Bob Chen.");
  await expect(highlight).toBeInViewport();
  expect(apiRequests).toContain(matterPath.replace("/app/", "/api/"));
  expect(apiRequests.every(path => path.startsWith("/api/matters"))).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("matter-workspace.png"), fullPage: true });
  await page.getByRole("link", { name: "Back to Matters" }).click();
  await expect(matter).toBeVisible();
  await page.getByRole("link", { name: "Public showcase" }).click();
  await expect(page.getByRole("button", { name: "Load sample analysis" })).toBeVisible();
  await page.getByRole("link", { name: "Practitioner application" }).click();
  await expect(matter).toBeVisible();
});

test("unknown Matter direct route stays in the practitioner shell", async ({ page }) => {
  await page.goto("/app/matters/00000000-0000-0000-0000-000000000000");
  await expect(page.getByRole("alert")).toContainText("Matter not found");
  await page.getByRole("link", { name: "Back to Matters" }).click();
  await expect(page.getByRole("heading", { name: "Matters", exact: true })).toBeVisible();
});
