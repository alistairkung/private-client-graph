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

test("paired corrections preserve the exact selected Source and Evidence across language changes", async ({ page }, testInfo) => {
  await page.goto("/research-results");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Research results");
  await expect(page.getByRole("article", { name: "Source document" })).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Benchmark cases" }).getByRole("button")).toHaveCount(10);
  await page.getByRole("button", { name: "Inspect the two corrections", exact: true }).click();
  const corrections = page.getByRole("button", { name: /Bea → Beatrice Ng/ });
  await expect(corrections).toHaveCount(2);
  for (let index = 0; index < 2; index++) {
    await corrections.nth(index).click();
    await expect(page.locator(".source-panel mark")).toBeVisible();
    await expect(page.locator(".research-source-inspection")).toContainText("Selected relationship · B");
    const quote = await page.locator(".source-panel mark").innerText();
    const source = await page.getByLabel("Original Source", { exact: true }).inputValue();
    await page.getByRole("button", { name: "简体中文", exact: true }).click();
    await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
    await expect(page.locator(".source-panel mark")).toHaveText(quote);
    expect(await page.locator(".research-source-inspection select").first().inputValue()).toBe(source);
    await expect(page.locator(".research-case-index button[aria-pressed=true]")).toContainText("heldout_03");
    await expect(page.locator(".research-pair button[aria-pressed=true]")).toHaveCount(1);
    await expect(page.locator(".research-source-inspection")).not.toContainText("Selected relationship");
    if (index === 0) await page.screenshot({ path: testInfo.outputPath("research-correction-zh-CN.png"), fullPage: true });
    await page.getByRole("button", { name: "EN", exact: true }).click();
    await expect(page.locator(".source-panel mark")).toHaveText(quote);
  }
  await page.getByLabel("Recorded outcome filter").selectOption("errors");
  await expect(page.getByRole("region", { name: "Run B relationships" })).toContainText("No recorded relationship errors.");
  await expect(page.getByRole("region", { name: "Run A′ relationships" }).getByRole("button")).toHaveCount(4);
  await page.getByLabel("Baseline Run").selectOption("A");
  await expect(page.getByRole("region", { name: "Run A relationships" }).getByRole("button")).toHaveCount(4);
  await page.getByRole("navigation", { name: "Benchmark cases" }).getByRole("button").first().click();
  await expect(page.locator(".research-case-detail")).toContainText("Unchanged relationship results across A, A′ and B.");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("provider inspection shows replay zero calls and retained metadata only", async ({ page }, testInfo) => {
  const response = await page.request.get("/api/research-results");
  const snapshot = await response.json();
  const resolver = snapshot.runs.find((run: { label: string }) => run.label === "B");
  await page.goto("/research-results");
  const usage = page.locator("#usage");
  await usage.getByText("Run A′: 0 provider calls", { exact: true }).click();
  await expect(usage).toContainText("Zero provider calls. This control used deterministic replay.");
  await usage.getByText(`Run B: ${resolver.usage.attempts} provider calls`, { exact: true }).click();
  const treatment = usage.locator(":scope > details").filter({
    has: page.getByText(resolver.run_id, { exact: true }),
  });
  const call = treatment.locator(".research-call-list details").first();
  await call.locator("summary").click();
  await expect(call).toContainText(resolver.calls[0].attempt_id);
  await expect(call).toContainText("Input tokens");
  await expect(call).toContainText("Output tokens");
  await expect(call).toContainText("Cached tokens");
  await expect(call).toContainText("Unpriced");
  await expect(call).not.toContainText("Authorization");
  await expect(call).not.toContainText("system_prompt");
  await page.screenshot({ path: testInfo.outputPath("research-calls-en.png"), fullPage: true });
  await page.getByRole("button", { name: "简体中文", exact: true }).click();
  await expect(call).toHaveAttribute("open", "");
  await expect(call).toContainText(resolver.calls[0].attempt_id);
  await expect(call).toContainText("未定价");
  await page.screenshot({ path: testInfo.outputPath("research-calls-zh-CN.png"), fullPage: true });
});
