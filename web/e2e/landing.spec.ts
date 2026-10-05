import { expect, test } from "@playwright/test";

test("landing navigation reaches an explicit, contained demonstration", async ({ page }) => {
  const analyses: string[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().includes("/api/showcase")) {
      analyses.push(request.url());
    }
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const source = page.getByLabel("Source document");
  await expect(source).toBeVisible();
  await expect(page.getByLabel("Relationship graph")).toHaveCount(0);
  expect(analyses).toEqual([]);
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to Case 01" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#case-01")).toBeFocused();
  await expect(source).toContainText(await page.locator(".folio-source blockquote").innerText());
  await page.getByRole("button", { name: "Load sample analysis" }).click();
  const graph = page.getByLabel("Relationship graph");
  await expect(graph).toBeVisible();
  expect(analyses).toHaveLength(1);
  const frame = await page.locator(".demonstration-frame").boundingBox();
  for (const panel of [graph, source]) {
    const bounds = await panel.boundingBox();
    expect(bounds!.x).toBeGreaterThanOrEqual(frame!.x);
    expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(frame!.x + frame!.width);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );
});

for (const reducedMotion of ["no-preference", "reduce"] as const) {
  test(`Case 01 navigation respects ${reducedMotion} motion preference`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion });
    await page.goto("/");
    await expect(page.locator("html")).toHaveCSS(
      "scroll-behavior", reducedMotion === "reduce" ? "auto" : "smooth",
    );
    await expect(page.getByLabel("Source document")).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    await page.getByRole("link", { name: "Explore Case 01", exact: true }).last().click();
    await expect(page).toHaveURL(/#case-01$/);
    await expect.poll(() => page.locator("#case-01").evaluate((section) => {
      const target = section.getBoundingClientRect().top + window.scrollY
        - parseFloat(getComputedStyle(section).scrollMarginTop);
      const maximum = document.documentElement.scrollHeight - window.innerHeight;
      return Math.abs(window.scrollY - Math.min(target, maximum));
    })).toBeLessThan(2);
  });
}
