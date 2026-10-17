import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const sourcePdf = fileURLToPath(new URL("../../tests/fixtures/synthetic-proposal.pdf", import.meta.url));
const matterPath = "/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369";

// These tests stop at the existing deterministic application/provider boundary.
test("locale changes retain showcase case, selected relationship and exact Evidence", async ({ page }, testInfo) => {
  await page.goto("/#case-01");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  const caseChoice = page.locator(".showcase-case-choice");
  await caseChoice.selectOption("case-04");
  const relationshipChoice = page.locator(".graph-selector select");
  await relationshipChoice.selectOption("0");
  const quote = await page.locator("mark").innerText();
  const originalSource = await page.locator(".source-panel").innerText();
  const beforePath = page.url();
  await page.getByRole("button", { name: "简体中文", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
  expect(page.url()).toBe(beforePath);
  await expect(caseChoice).toHaveValue("case-04");
  await expect(relationshipChoice).toHaveValue("0");
  await expect(page.locator("mark")).toHaveText(quote);
  // The authoritative text is retained, even while its surrounding controls translate.
  expect(await page.locator(".source-panel").innerText()).toContain(quote);
  expect(originalSource).toContain(quote);
  await page.screenshot({ path: testInfo.outputPath("showcase-zh-CN.png"), fullPage: true });
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
});

test("practitioner locale switch preserves intake fields and selected PDF", async ({ page }) => {
  await page.goto("/app/matter-proposals/new");
  const reference = page.locator('input[name="external_reference"]');
  const title = page.locator('input[name="matter_title"]');
  await reference.fill(`Locale/${randomUUID()}`);
  const referenceValue = await reference.inputValue();
  await title.fill("Fictional locale check");
  const pdf = page.locator('input[type="file"]');
  await pdf.setInputFiles(sourcePdf);
  await page.locator('input[name="source_title_0"]').fill("Original Source title");
  await page.getByRole("button", { name: "简体中文", exact: true }).click();
  await expect(reference).toHaveValue(referenceValue);
  await expect(title).toHaveValue("Fictional locale check");
  await expect(page.locator('input[name="source_title_0"]')).toHaveValue("Original Source title");
  expect(await pdf.evaluate((input: HTMLInputElement) => input.files?.[0]?.name)).toBe("synthetic-proposal.pdf");
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(reference).toHaveValue(referenceValue);
  expect(await pdf.evaluate((input: HTMLInputElement) => input.files?.length)).toBe(1);
});

test("translated accepted Matter preserves canonical data and selected quotation", async ({ page, context }, testInfo) => {
  await page.goto(matterPath);
  const before = await (await context.request.get(matterPath.replace("/app/", "/api/"))).json();
  await page.locator(".graph-selector select").selectOption("0");
  const quote = await page.locator("mark").innerText();
  await page.getByRole("button", { name: "简体中文", exact: true }).click();
  await expect(page.locator(".graph-selector select")).toHaveValue("0");
  await expect(page.locator("mark")).toHaveText(quote);
  await expect(page.getByRole("heading", { name: "Evergreen Family Trust", exact: true })).toBeVisible();
  const after = await (await context.request.get(matterPath.replace("/app/", "/api/"))).json();
  expect(after).toEqual(before);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("practitioner-zh-CN.png"), fullPage: true });
});
