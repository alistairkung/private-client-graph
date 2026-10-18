import { test, expect } from "@playwright/test";

test.use({ video: { mode: "on", size: { width: 1512, height: 982 } } });
test("record the synthetic practitioner walkthrough", async ({
  page,
}, info) => {
  test.skip(
    !process.env.PCG_RECORD_DEMO || info.project.name !== "desktop",
    "Opt-in evidence capture, not an additional parity gate.",
  );
  await page.goto("/auth/login?next=/app");
  await expect(
    page.getByRole("heading", { name: "Matters", exact: true }),
  ).toBeVisible();
  await page.getByRole("searchbox").fill("PC/2026/0142");
  await page.screenshot({
    path: "artifacts/desktop-ledger.png",
    fullPage: true,
  });
  await page.waitForTimeout(1000); // Hold each meaningful state for the short human-viewable recording.
  await page.getByRole("link", { name: /PC\/2026\/0142/ }).click();
  await expect(
    page.getByRole("heading", { name: "Evergreen Family Trust", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".react-flow__node")).toHaveCount(5);
  await page.waitForTimeout(1500);
  await page.locator('button.edge-label[data-edge-id="0"]').click();
  await page.locator(".evidence-item").first().click();
  await expect(page.locator(".source-text mark")).toBeVisible();
  await page.waitForTimeout(1500);
  await page.getByRole("button", { name: "Graph", exact: true }).click();
  await page.waitForTimeout(1500);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "artifacts/desktop-selected-graph.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Back to relationship", exact: true })
    .click();
  await page.waitForTimeout(1000);
  const video = page.video();
  await page.close();
  await video?.saveAs("artifacts/walkthrough.webm");
});
