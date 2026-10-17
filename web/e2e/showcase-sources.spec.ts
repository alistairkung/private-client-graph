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
