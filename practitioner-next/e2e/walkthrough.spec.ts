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
  const graph = page.getByRole("tab", { name: "Graph", exact: true });
  const list = page.getByRole("tab", { name: "List", exact: true });
  const from = await graph.boundingBox();
  const to = await list.boundingBox();
  if (!from || !to) throw new Error("View switch is not visible");
  await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2);
  await page.mouse.down();
  await page.mouse.move(to.x + to.width / 2, to.y + to.height / 2, {
    steps: 16,
  });
  await page.mouse.up();
  await expect(list).toHaveAttribute("aria-selected", "true");
  await page
    .getByRole("searchbox", { name: "Find relationship" })
    .fill("Carol");
  await page.waitForTimeout(1000);
  await graph.click();
  await page.waitForTimeout(800);
  await page.locator('button.edge-label[data-edge-id="0"]').click();
  await page.waitForTimeout(800);
  await expect(page.locator(".source-text mark")).toBeVisible();
  await page.waitForTimeout(1500);
  await page.getByRole("tab", { name: "Graph", exact: true }).click();
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
