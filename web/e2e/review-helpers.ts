import type { Page } from "@playwright/test";

export async function selectSpouseRelationship(page: Page) {
  const relationship = page.getByRole("button", {
    name: "Alice Chen — Spouse of — David Chen",
    exact: true,
  });
  await page.getByLabel("Find a relationship").selectOption({ label: "Alice Chen — Spouse of — David Chen" });
  await relationship.getByText("Spouse of", { exact: true }).click();
  return relationship;
}
