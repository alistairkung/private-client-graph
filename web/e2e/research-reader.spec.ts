import { expect, test } from "@playwright/test";

for (const reducedMotion of ["reduce", "no-preference"] as const) {
  test(`research disclosures and case navigation remain interruptible with ${reducedMotion}`, async ({ page }, testInfo) => {
    await page.emulateMedia({ reducedMotion });
    await page.goto("/research-results");
    const metrics = page.getByRole("button", { name: "Recorded metric table", exact: true });
    await metrics.focus();
    await metrics.press("Space");
    await expect(metrics).toHaveAttribute("aria-expanded", "true");
    const panelId = await metrics.getAttribute("aria-controls");
    const panel = page.locator(`[id="${panelId}"]`);
    await expect(panel.getByRole("table")).toBeVisible();
    await metrics.press("Enter");
    await metrics.press("Enter");
    await metrics.press("Enter");
    await expect(metrics).toHaveAttribute("aria-expanded", "false");
    await expect(panel.getByRole("table")).toHaveCount(0);
    await metrics.press("Space");
    await expect(panel.getByRole("table")).toBeVisible();
    await expect(metrics).toBeFocused();
    await page.locator(".research-recorded-metrics").screenshot({ path: testInfo.outputPath(`accordion-${reducedMotion}.png`) });
    await metrics.press("Enter");
    await expect(panel).toHaveJSProperty("offsetHeight", 0);

    const cases = page.locator("#cases");
    const picker = cases.getByRole("combobox", { name: "Benchmark case", exact: true });
    await picker.scrollIntoViewIfNeeded();
    await picker.focus();
    const previousScroll = await page.evaluate(() => window.scrollY);
    await picker.selectOption("heldout_03");
    await expect(picker).toBeFocused();
    expect(await page.evaluate(() => window.scrollY)).toBe(previousScroll);
    const corrections = cases.getByRole("button", { name: /Bea → Beatrice Ng/ });
    await corrections.first().click();
    await expect(cases.getByRole("article")).toHaveCount(0);
    const sourceJump = cases.getByRole("button", { name: "View in original Source", exact: true });
    await sourceJump.click();
    const source = cases.getByRole("region", { name: "Original Source", exact: true });
    await expect(source).toBeFocused();
    await expect(source.locator("mark")).toHaveText("Bea is the settlor of the Larch Family Trust.");
    await source.getByRole("button", { name: "Back to selected relationship", exact: true }).click();
    await expect(sourceJump).toBeFocused();
    await expect(cases.getByRole("article")).toHaveCount(0);
    await cases.locator(".research-source-inspection").scrollIntoViewIfNeeded();
    expect(await cases.evaluate(element => {
      const pickerBottom = element.querySelector(".research-case-picker")!.getBoundingClientRect().bottom;
      return [...element.querySelectorAll(".research-quotes button")].every(button => {
        const bounds = button.getBoundingClientRect();
        return bounds.top >= pickerBottom && bounds.bottom <= innerHeight;
      });
    })).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`case-reader-${reducedMotion}.png`) });
    await cases.getByLabel("Recorded outcome filter").selectOption("errors");
    await expect(cases.locator(".research-source-inspection")).not.toContainText("Selected relationship");
    await expect(cases.getByRole("region", { name: "Run B relationships" })).toContainText("No recorded relationship errors.");
    const runs = cases.getByRole("group", { name: "Relationship Run", exact: true });
    await runs.getByRole("button", { name: "Run A′", exact: true }).click();
    const replay = cases.getByRole("region", { name: "Run A′ relationships" });
    await replay.getByRole("button").first().click();
    await expect(cases.locator(".research-source-inspection")).toContainText("Selected relationship · A′");
    await cases.getByLabel("Baseline Run").selectOption("A");
    await expect(cases.getByRole("region", { name: "Run A relationships" })).toBeVisible();
    await expect(cases.locator(".research-source-inspection")).not.toContainText("Selected relationship");
    await picker.selectOption("heldout_10");
    await expect(cases.locator(".research-case-detail")).toContainText("Unchanged relationship results across A, A′ and B.");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}
