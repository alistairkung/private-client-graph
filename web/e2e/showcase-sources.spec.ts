import { expect, test } from "@playwright/test";
import type { CanonicalState } from "../src/shared/contracts";

test("curated multi-source examples preserve corroboration, trustee replacement and direct links", async ({ page }, info) => {
  await page.goto("/app?example=case-04");
  await expect(page.getByLabel("Choose a synthetic case")).toHaveValue("case-04");
  await page.reload();
  await expect(page.getByLabel("Choose a synthetic case")).toHaveValue("case-04");
  await page.getByRole("button", { name: "Previous example", exact: true }).click();
  await expect(page.getByLabel("Choose a synthetic case")).toHaveValue("case-01");
  await expect(page.getByRole("button", { name: "Previous example", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Next example", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Choose a synthetic case")).toHaveValue("case-04");
  const case04 = await page.request.get("/api/showcase/cases/case-04");
  const state: CanonicalState = (await case04.json()).state;
  const beneficiary = state.relationships.findIndex(edge => edge.type === "beneficiary_of"
    && state.entities.find(entity => entity.id === edge.source)?.name === "Andrew Chan");
  expect(beneficiary).toBeGreaterThanOrEqual(0);
  expect(state.relationships[beneficiary].evidence_ids).toHaveLength(2);
  await page.getByRole("tab", { name: "List", exact: true }).click();
  await page.locator(`#relationship-${beneficiary}`).click();
  const sourceTabs = page.locator(".source-tabs button");
  await expect(sourceTabs).toHaveCount(2);
  await sourceTabs.nth(1).click();
  await expect(sourceTabs.nth(1)).toHaveAttribute("aria-pressed", "true");
  const expected = state.evidence.find(item => item.source_id === state.sources[1].id
    && state.relationships[beneficiary].evidence_ids.includes(item.id))!;
  await expect(page.locator(".source-text mark")).toHaveText(expected.supporting_text);
  await expect(page.locator(".source-text mark")).toHaveAttribute("data-evidence-id", expected.id);
  if (info.project.name === "desktop") {
    const inspector = await page.locator(".evidence-inspector").boundingBox();
    expect(inspector!.y + inspector!.height).toBeLessThanOrEqual(page.viewportSize()!.height + 1);
  }
  await page.screenshot({ path: info.outputPath("case-04.png"), fullPage: true });

  await page.getByLabel("Choose a synthetic case").selectOption("case-05");
  await expect(page).toHaveURL(/example=case-05$/);
  await expect(page.getByRole("button", { name: "Next example", exact: true })).toBeDisabled();
  await page.getByRole("tab", { name: "List", exact: true }).click();
  await expect(page.locator(".relationship-row").filter({ hasText: /David Ng.*trustee/i })).toHaveCount(0);
  const trustee = page.locator(".relationship-row").filter({ hasText: /Rachel Lim.*trustee.*Willow Family Trust/i });
  await expect(trustee).toHaveCount(1);
  await trustee.click();
  await expect(page.locator(".source-text mark")).toHaveText(
    "Rachel Lim is the sole trustee of the Willow Family Trust as at 15 September 2026.",
  );
  await expect(sourceTabs.nth(1)).toHaveAttribute("aria-pressed", "true");
  await expect(sourceTabs).toHaveCount(2);
  await expect(page.getByRole("button", { name: "Confirm proposal", exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath("case-05.png"), fullPage: true });
});
