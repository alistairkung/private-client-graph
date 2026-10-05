import { expect, test } from "@playwright/test";
import { selectSpouseRelationship } from "./review-helpers";

test("live attempt exhausts the shared allowance while sample and Matter review stay usable", async ({ page }) => {
  await page.goto("/");
  const live = page.getByRole("button", { name: "Run live analysis" });
  await expect(live).toBeEnabled();
  await live.click();
  await expect(page.getByText("Live analysis · Newly extracted")).toBeVisible();
  await expect(live).toBeDisabled();
  await expect(page.locator("time")).toBeVisible();
  await selectSpouseRelationship(page);
  await expect(page.locator("mark")).toHaveText("Alice Chen confirmed that she and David Chen are spouses.");

  // New navigation at a phone width discovers exhaustion before any POST.
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await expect(live).toBeDisabled();
  await expect(page.locator("time")).toBeVisible();
  await page.getByRole("button", { name: "Load sample analysis" }).click();
  await expect(page.getByText("Sample analysis · Demonstration fixture")).toBeVisible();
  await page.getByRole("link", { name: "Practitioner application" }).click();
  await page.getByRole("link", { name: /Evergreen Family Trust/ }).click();
  await selectSpouseRelationship(page);
  await expect(page.locator("mark")).toHaveText("Alice Chen confirmed that she and David Chen are spouses.");
});
