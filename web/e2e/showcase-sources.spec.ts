import { expect, test } from "@playwright/test";

test("multi-source curated review follows exact Evidence and demonstrates trustee replacement", async ({ page }, testInfo) => {
  await page.goto("/");
  const relationships = page.getByLabel("Find a relationship");
  const sources = page.getByRole("navigation", { name: "Sources" });

  await page.getByLabel("Choose a synthetic case").selectOption("case-04");
  await relationships.selectOption({ label: "Andrew Chan — Beneficiary of — Hillcrest Family Trust" });
  await expect(page.getByRole("button", { name: /Evidence 2/ })).toBeVisible();
  await page.getByRole("button", { name: /Evidence 2/ }).click();
  await expect(sources.getByRole("button", { name: /Source 2/ })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("mark")).toContainText("Andrew Chan");
  await page.getByRole("link", { name: "View in source" }).click();
  await expect(page.locator("mark")).toBeFocused();
  await page.screenshot({ path: testInfo.outputPath("case-04.png"), fullPage: true });

  await page.getByLabel("Choose a synthetic case").selectOption("case-05");
  await expect(relationships).not.toContainText("David Ng — Trustee");
  await expect(relationships).toContainText("Rachel Lim — Trustee of — Willow Family Trust");
  await relationships.selectOption({ label: "Rachel Lim — Trustee of — Willow Family Trust" });
  await expect(page.locator("mark")).toHaveText(
    "Rachel Lim is the sole trustee of the Willow Family Trust as at 15 September 2026.",
  );
  await expect(sources.getByRole("button", { name: /Source 2/ })).toHaveAttribute("aria-pressed", "true");
  await expect(sources.getByRole("button")).toHaveCount(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("case-05.png"), fullPage: true });
});

test("landing review stacks graph above attendance when its panel is narrow", async ({ page }, testInfo) => {
  for (const width of [390, 1024, 1280, 1600]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/#case-01");
    const graph = page.locator(".demonstration .graph-panel");
    const source = page.locator(".demonstration .source-panel");
    await expect(graph).toBeVisible();
    await expect(source).toBeVisible();
    const stage = await page.locator(".demonstration-stage").boundingBox();
    const graphBounds = await graph.boundingBox();
    const sourceBounds = await source.boundingBox();
    if (stage!.width <= 850) {
      expect(sourceBounds!.y).toBeGreaterThanOrEqual(graphBounds!.y + graphBounds!.height);
      expect(Math.abs(graphBounds!.x - sourceBounds!.x)).toBeLessThan(2);
      expect(Math.abs(graphBounds!.width - sourceBounds!.width)).toBeLessThan(2);
    } else {
      expect(sourceBounds!.x).toBeGreaterThan(graphBounds!.x);
      expect(Math.abs(graphBounds!.y - sourceBounds!.y)).toBeLessThan(2);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await graph.scrollIntoViewIfNeeded();
    await page.screenshot({ path: testInfo.outputPath(`landing-review-${width}.png`) });
  }
});
