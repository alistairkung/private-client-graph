import { selectPublicLanguage } from "./public-navigation";
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
    const researchLink = page.locator(".landing-research").getByRole("link");
    await expect(researchLink).toHaveAttribute("href", "/research-results");
    await expect(page.locator(".landing-research")).toContainText(locale === "en" ? "research" : "研究");
    const requests: string[] = [];
    page.on("request", request => {
      if (request.url().includes("/api/")) requests.push(`${request.method()} ${new URL(request.url()).pathname}`);
    });
    await researchLink.click();
    await expect(page).toHaveURL(/\/research-results$/);
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator("main")).toContainText("94.87%");
    await expect(page.locator("main")).toContainText("100.00%");
    await expect(page.locator("main")).toContainText(snapshot.snapshot_id);
    await expect(page.locator("main")).toContainText(snapshot.integrity.digest);
    await page.locator(".research-recorded-metrics > summary").click();
    for (const section of ["comparison", "usage"]) {
      const scroller = page.locator(`#${section} .research-table-scroll`);
      if (page.viewportSize()!.width < 600) {
        expect(await scroller.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(true);
      }
      expect(await scroller.evaluate(element => element.getBoundingClientRect().right <= window.innerWidth)).toBe(true);
    }
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
  const selectedHeading = page.locator(".research-case-detail h3");
  await expect(selectedHeading).toBeFocused();
  await expect(selectedHeading).toBeInViewport();
  const corrections = page.getByRole("button", { name: /Bea → Beatrice Ng/ });
  await expect(corrections).toHaveCount(2);
  for (let index = 0; index < 2; index++) {
    await corrections.nth(index).click();
    await expect(page.locator(".source-panel mark")).toBeVisible();
    await expect(page.locator(".research-source-inspection")).toContainText("Selected relationship · B");
    const quote = await page.locator(".source-panel mark").innerText();
    const source = await page.getByLabel("Original Source", { exact: true }).inputValue();
    await selectPublicLanguage(page, "zh-CN");
    await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
    await expect(page.locator(".source-panel mark")).toHaveText(quote);
    expect(await page.locator(".research-source-inspection select").first().inputValue()).toBe(source);
    await expect(page.locator(".research-case-index button[aria-pressed=true]")).toContainText("heldout_03");
    await expect(page.locator(".research-pair button[aria-pressed=true]")).toHaveCount(1);
    await expect(page.locator(".research-source-inspection")).not.toContainText("Selected relationship");
    if (index === 0) await page.screenshot({ path: testInfo.outputPath("research-correction-zh-CN.png"), fullPage: true });
    await selectPublicLanguage(page, "en");
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
  await selectPublicLanguage(page, "zh-CN");
  await expect(call).toHaveAttribute("open", "");
  await expect(call).toContainText(resolver.calls[0].attempt_id);
  await expect(call).toContainText("未定价");
  await page.screenshot({ path: testInfo.outputPath("research-calls-zh-CN.png"), fullPage: true });
});

for (const locale of ["en", "zh-CN"] as const) {
  test(`editorial pipeline and recorded graph evidence remain read-only in ${locale}`, async ({ page }, testInfo) => {
    await page.addInitScript(value => localStorage.setItem("pcg-locale", value), locale);
    await page.emulateMedia({ reducedMotion: "reduce" });
    const requests: string[] = [];
    page.on("request", request => { if (request.url().includes("/api/")) requests.push(`${request.method()} ${new URL(request.url()).pathname}`); });
    await page.goto("/research-results");
    await expect(page.locator("main > .research-section")).toHaveCount(8);
    const sectionIds = ["question", "architecture", "methodology", "comparison", "failure-analysis", "findings", "limitations", "reproducibility"];
    expect(await page.locator("main > .research-section").evaluateAll(elements => elements.map(element => element.id))).toEqual(sectionIds);
    if (page.viewportSize()!.width >= 701) {
      const index = page.getByRole("navigation", { name: locale === "en" ? "Benchmark cases" : "基准案例" });
      expect(await index.evaluate(element => element.clientHeight)).toBeLessThanOrEqual(512);
      expect(await index.evaluate(element => element.scrollHeight > element.clientHeight)).toBe(true);
      expect(await index.getByRole("button").evaluateAll(buttons => buttons.every(button => button.scrollHeight <= button.clientHeight + 1))).toBe(true);
      await index.getByRole("button").last().scrollIntoViewIfNeeded();
      await expect(index.getByRole("button").last()).toBeVisible();
      await index.evaluate(element => { element.scrollTop = 0; });
    }
    const architecture = page.locator("#architecture");
    await architecture.getByRole("combobox", { name: locale === "en" ? "Inspect Run" : "查看运行", exact: true }).selectOption("B");
    const resolver = architecture.getByRole("button", { name: locale === "en" ? /Resolve aliases/ : /解析别名/ });
    await resolver.click();
    await expect(resolver).toHaveAttribute("aria-expanded", "true");
    await expect(architecture.getByRole("region", { name: locale === "en" ? "Resolve aliases settings" : "解析别名设置" })).toContainText(locale === "en" ? "Frozen configuration · Read-only" : "冻结配置 · 只读");
    const study = page.locator(".research-graph-study");
    await study.getByLabel(locale === "en" ? "Find a relationship" : "查找关系").selectOption("0");
    const canvasContainsNodes = () => study.locator(".graph-canvas").evaluate(canvas => {
      const frame = canvas.getBoundingClientRect();
      return Array.from(canvas.querySelectorAll(".react-flow__node")).every(node => {
        const box = node.getBoundingClientRect();
        return box.left >= frame.left && box.right <= frame.right && box.top >= frame.top && box.bottom <= frame.bottom;
      });
    });
    await expect.poll(canvasContainsNodes).toBe(true);
    const inspector = study.locator(".evidence-inspector");
    await expect(inspector).toContainText("Bea · parent_of · Isaac Ng");
    await inspector.getByRole("button", { name: locale === "en" ? "View predicted in Source" : "在来源中查看预测证据", exact: true }).click();
    const quote = await inspector.locator("mark").first().innerText();
    await page.locator("#failure-analysis").screenshot({ path: testInfo.outputPath(`editorial-original-${locale}.png`) });
    await expect(inspector.locator("article")).toBeFocused();
    await study.getByRole("button", { name: locale === "en" ? "Resolved relationships · B" : "解析后关系 · B", exact: true }).click();
    await study.getByLabel(locale === "en" ? "Find a relationship" : "查找关系").selectOption("0");
    await expect.poll(canvasContainsNodes).toBe(true);
    await expect(inspector).toContainText("Beatrice Ng · parent_of · Isaac Ng");
    await inspector.getByRole("button", { name: locale === "en" ? "View predicted in Source" : "在来源中查看预测证据", exact: true }).click();
    await expect(inspector.locator("mark").first()).toHaveText(quote);
    await page.locator("#failure-analysis").scrollIntoViewIfNeeded();
    await page.screenshot({ path: testInfo.outputPath(`editorial-results-${locale}.png`), fullPage: true });
    await page.locator("#failure-analysis").screenshot({ path: testInfo.outputPath(`editorial-graph-${locale}.png`) });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect(requests.every(request => request === "GET /api/research-results")).toBe(true);
  });
}

for (const locale of ["en", "zh-CN"] as const) {
  test(`genuine Workbench figures inspect published Runs without operational access in ${locale}`, async ({ page }, testInfo) => {
    await page.addInitScript(value => localStorage.setItem("pcg-locale", value), locale);
    await page.emulateMedia({ reducedMotion: "reduce" });
    const requests: string[] = [];
    page.on("request", request => { if (request.url().includes("/api/")) requests.push(`${request.method()} ${new URL(request.url()).pathname}`); });
    await page.goto("/research-results");
    if (page.viewportSize()!.width >= 701) {
      expect(await page.locator(".research-disclosure").evaluate(element => element.getBoundingClientRect().width)).toBeLessThanOrEqual(900);
    }
    const architecture = page.locator("#architecture");
    const configuration = architecture.getByRole("combobox", { name: locale === "en" ? "Inspect Run" : "查看运行", exact: true });
    await configuration.selectOption("A_prime");
    await expect(architecture.getByRole("button", { name: /Resolve aliases|解析别名/ })).toHaveCount(0);
    await configuration.selectOption("B");
    const stage = architecture.getByRole("button", { name: /Resolve aliases|解析别名/ });
    await stage.click();
    await expect(stage).toHaveAttribute("aria-expanded", "true");
    await expect(architecture.getByRole("button", { name: /Add|Bypass|Authorize|Execute|添加|跳过|授权|执行/ })).toHaveCount(0);
    await expect(page.locator("iframe")).toHaveCount(0);
    await stage.click();
    await architecture.locator(".pipeline-viewport").evaluate(element => { element.scrollLeft = 0; });
    await expect(architecture.locator(".pipeline-node").first()).toHaveCSS("width", "240px");
    await expect(architecture.locator(".node-header").first()).toHaveCSS("height", "140px");
    await expect(architecture.locator(".pipeline-navigation button").first()).toHaveCSS("background-color", "rgb(23, 62, 56)");
    await page.mouse.move(0, 0);
    await page.evaluate(() => document.fonts.ready);
    await architecture.locator(".pipeline-workspace").screenshot({ path: testInfo.outputPath(`shared-pipeline-component-public-${locale}.png`) });
    await architecture.screenshot({ path: testInfo.outputPath(`shared-pipeline-public-${locale}.png`) });
    const chart = page.locator("#comparison .run-chart");
    await expect(chart.locator(".chart-point")).toHaveCount(3);
    await chart.screenshot({ path: testInfo.outputPath(`shared-chart-component-public-${locale}.png`) });
    const treatment = chart.getByRole("button", { name: locale === "en" ? "Run 3, F1 1.000, complete, 10/10 scored" : "运行 3，F1 1.000，完整，已评分 10/10", exact: true });
    await treatment.click();
    await expect(treatment).toHaveAttribute("aria-pressed", "true");
    await expect(chart.locator(".chart-inspection")).toContainText("841389cef51957ce8523ea41c03d2baa");
    const inputs = chart.getByRole("combobox", { name: locale === "en" ? "Input mode" : "输入模式", exact: true });
    await inputs.selectOption("fresh");
    await expect(chart.locator(".chart-point")).toHaveCount(1);
    await inputs.selectOption("all");
    await chart.getByRole("tab", { name: locale === "en" ? "F1 vs Cost" : "F1 与成本", exact: true }).click();
    await expect(chart.locator(".chart-point")).toHaveCount(1);
    await expect(chart.locator(".chart-point")).toHaveAttribute("aria-label", locale === "en" ? "Run 2, F1 0.949, complete, 10/10 scored" : "运行 2，F1 0.949，完整，已评分 10/10");
    await expect(chart.getByText(locale === "en" ? "Unpriced provider attempts; excluded from cost chart." : "提供商调用尝试未定价；不纳入成本图表。", { exact: true })).toHaveCount(2);
    await chart.getByRole("tab", { name: locale === "en" ? "F1 by Run" : "各次运行的 F1", exact: true }).click();
    await expect(chart.getByRole("tab", { name: locale === "en" ? "F1 by Run" : "各次运行的 F1", exact: true })).toHaveCSS("color", "rgb(23, 62, 56)");
    await expect(treatment).toHaveAttribute("aria-pressed", "true");
    await page.mouse.move(0, 0);
    await page.locator("#comparison").screenshot({ path: testInfo.outputPath(`shared-chart-public-${locale}.png`) });
    for (const frame of page.frames()) await frame.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: testInfo.outputPath(`shared-results-${locale}.png`), fullPage: true });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect(requests.every(request => request === "GET /api/research-results")).toBe(true);
  });
}
