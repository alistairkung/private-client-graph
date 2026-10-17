import { readFile } from "node:fs/promises";
import { expect, test } from "@playwright/test";

for (const locale of ["en", "zh-CN"] as const) {
  test(`published research is discoverable and uses one exact artifact in ${locale}`, async ({ page, context }, testInfo) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.addInitScript(value => localStorage.setItem("pcg-locale", value), locale);
    const publication = await context.request.get("/api/research-results");
    expect(publication.ok()).toBe(true);
    const bytes = await publication.body();
    const snapshot = JSON.parse(bytes.toString());
    await page.goto("/");
    const summary = page.locator("#research-summary");
    await expect(summary).toContainText("94.87%");
    await expect(summary).toContainText("100.00%");
    await expect(summary.locator("dd span")).toHaveCount(2);
    await expect(summary).toContainText(locale === "en" ? "post-hoc and exploratory" : "事后开展的探索性比较");
    await expect(summary).toContainText(locale === "en" ? "No real client data was used" : "未使用真实客户数据");
    await expect(summary).toContainText(locale === "en" ? "do not establish production accuracy or reliability" : "不代表系统在实际生产环境中的准确率或可靠性");
    expect(await summary.evaluate(section => {
      const approach = document.querySelector("#approach")!;
      const demo = document.querySelector("#case-01")!;
      return !!(approach.compareDocumentPosition(section) & Node.DOCUMENT_POSITION_FOLLOWING)
        && !!(section.compareDocumentPosition(demo) & Node.DOCUMENT_POSITION_FOLLOWING);
    })).toBe(true);
    await summary.scrollIntoViewIfNeeded();
    await page.screenshot({ path: testInfo.outputPath(`landing-research-${locale}.png`), fullPage: true });

    const requests: string[] = [];
    page.on("request", request => {
      if (request.url().includes("/api/")) requests.push(`${request.method()} ${new URL(request.url()).pathname}`);
    });
    await summary.getByRole("link").click();
    await expect(page).toHaveURL(/\/research-results$/);
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator("main")).toContainText("94.87%");
    await expect(page.locator("main")).toContainText("100.00%");
    await expect(page.locator("main")).toContainText(snapshot.snapshot_id);
    await expect(page.locator("main")).toContainText(snapshot.integrity.digest);
    const downloadEvent = page.waitForEvent("download");
    await page.getByRole("link", { name: locale === "en" ? "Download results" : "下载研究结果", exact: true }).first().click();
    const download = await downloadEvent;
    expect(await readFile((await download.path())!)).toEqual(bytes);
    expect(requests.every(request => [
      "GET /api/research-results", "GET /api/research-results/download",
    ].includes(request))).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`research-results-${locale}.png`), fullPage: true });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.reload();
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
  });
}

test("an unavailable publication never substitutes figures or private data", async ({ page }) => {
  await page.route("**/api/research-results", route => route.fulfill({
    status: 503, contentType: "application/json", body: JSON.stringify({ error: { message: "Publication unavailable" } }),
  }));
  await page.goto("/");
  const summary = page.locator("#research-summary");
  await expect(summary.getByRole("status")).toContainText("unavailable");
  await expect(summary.locator("dd")).toHaveCount(0);
  await page.goto("/research-results/");
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.locator("main")).not.toContainText("94.87%");
  await expect(page.locator("main")).not.toContainText("100.00%");
});
