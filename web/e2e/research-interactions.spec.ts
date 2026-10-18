import { expect, test } from "@playwright/test";

for (const reduced of [false, true]) {
  test(`research selection preserves immediate content, focus and spatial continuity with reduced motion ${reduced}`, async ({ page }, testInfo) => {
    await page.emulateMedia({ reducedMotion: reduced ? "reduce" : "no-preference" });
    await page.addInitScript(() => localStorage.setItem("pcg-locale", "en"));
    const requests: string[] = [];
    page.on("request", request => {
      if (request.url().includes("/api/")) requests.push(`${request.method()} ${new URL(request.url()).pathname}`);
    });
    await page.goto("/research-results");
    const configuration = page.locator("#architecture").getByRole("group", { name: "Inspect Run" });
    const replay = configuration.getByRole("button", { name: /A′/ });
    const resolver = configuration.getByRole("button", { name: /B/ });
    async function observeSelection(action: () => Promise<unknown>, name: string) {
      if (process.env.PCG_RESEARCH_EVIDENCE !== "1") return action();
      const observation = configuration.evaluate(async group => {
        const frames = [];
        const start = performance.now();
        for (let frame = 0; frame < 40; frame++) {
          await new Promise(requestAnimationFrame);
          const button = group.querySelector('[aria-pressed="true"]')!;
          const surface = button.querySelector(".research-run-surface")!;
          frames.push({
            ms: performance.now() - start,
            selected: button.textContent?.trim(),
            surfaceLeft: surface.getBoundingClientRect().left,
            targetLeft: button.getBoundingClientRect().left,
            resolverVisible: !!group.closest("#architecture")!.querySelector(".resolver-slot.present"),
          });
        }
        return frames;
      });
      await action();
      await testInfo.attach(name, { body: JSON.stringify(await observation, null, 2), contentType: "application/json" });
    }
    await replay.focus();
    await observeSelection(() => replay.press("Space"), "run-selection-frames");
    await expect(replay).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator("#architecture").getByRole("button", { name: /Resolve aliases/ })).toHaveCount(0);
    await replay.press("Tab");
    await expect(resolver).toBeFocused();
    await resolver.press("Enter");
    await expect(resolver).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator("#architecture").getByRole("button", { name: /Resolve aliases/ })).toBeVisible();
    // Rapid reversal must never queue content changes behind the moving indicator.
    await observeSelection(async () => {
      await replay.click();
      await resolver.click();
      await replay.click();
    }, "run-reversal-frames");
    await expect(replay).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator("#architecture").getByRole("button", { name: /Resolve aliases/ })).toHaveCount(0);
    const chart = page.locator("#comparison .run-chart");
    const baseline = chart.getByRole("button", { name: "A · Fresh baseline, F1 0.949, complete, 10/10 scored", exact: true });
    const treatment = chart.getByRole("button", { name: "B · With resolver, F1 1.000, complete, 10/10 scored", exact: true });
    const positions = await chart.locator(".chart-point").evaluateAll(points => points.map(point => ({ left: (point as HTMLElement).style.left, top: (point as HTMLElement).style.top })));
    await baseline.click();
    await treatment.click();
    await expect(treatment).toHaveAttribute("aria-pressed", "true");
    await expect(chart.locator(".chart-inspection")).toContainText("841389cef51957ce8523ea41c03d2baa");
    expect(await chart.locator(".chart-point").evaluateAll(points => points.map(point => ({ left: (point as HTMLElement).style.left, top: (point as HTMLElement).style.top })))).toEqual(positions);
    await expect(chart.locator(".chart-selection-ring")).toHaveCount(1);
    const tab = chart.getByRole("tab", { name: "F1 by Run", exact: true });
    await tab.focus();
    await tab.press("ArrowRight");
    await expect(chart.getByRole("tab", { name: "F1 vs Cost", exact: true })).toBeFocused();
    await expect(chart.locator(".chart-point")).toHaveCount(1);
    expect(requests.every(request => request === "GET /api/research-results")).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}

test("Chinese usage totals remain keyboard-scrollable to the final column at 280px", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 280, height: 844 });
  await page.addInitScript(() => localStorage.setItem("pcg-locale", "zh-CN"));
  await page.goto("/research-results");
  const usage = page.getByRole("region", { name: "运行用量汇总", exact: true });
  const finalHeader = usage.getByRole("columnheader", { name: "已记录费用", exact: true });
  const finalCell = usage.getByRole("row", { name: /^B / }).getByRole("cell").last();
  await usage.focus();
  await expect(usage).toBeFocused();
  expect(await usage.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(true);
  await expect.poll(async () => {
    await usage.press("ArrowRight");
    return usage.evaluate(element => element.scrollLeft + element.clientWidth >= element.scrollWidth - 1);
  }, { timeout: 15000, intervals: [50] }).toBe(true);
  await expect(usage).toBeFocused();
  for (const cell of [finalHeader, finalCell]) {
    await expect(cell).toBeVisible();
    const bounds = await cell.boundingBox();
    const region = await usage.boundingBox();
    expect(bounds).not.toBeNull();
    expect(region).not.toBeNull();
    expect(bounds!.x).toBeGreaterThanOrEqual(region!.x - 1);
    expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(region!.x + region!.width + 1);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.locator("#usage").screenshot({ path: testInfo.outputPath("narrow-zh-usage-end.png") });
  if (process.env.PCG_RESEARCH_EVIDENCE === "1") {
    await page.locator("#usage").screenshot({ path: "../docs/artifacts/research-refresh/narrow-zh-usage-end.png" });
  }
});
