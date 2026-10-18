import { expect, test } from "@playwright/test";

test.use({ video: { mode: "on", size: { width: 1512, height: 982 } } });

test("record construction and Evidence inspection", async ({ page }, info) => {
  test.skip(
    !process.env.PCG_RECORD_LANDING || info.project.name !== "desktop",
    "Opt-in landing recording, separate from the functional gates.",
  );
  await page.goto("/");
  const demo = page.getByRole("region", {
    name: "Explore the synthetic example",
  });
  await demo.locator(".landing-drawing").scrollIntoViewIfNeeded();
  await page
    .getByRole("button", { name: "Replay construction", exact: true })
    .click();
  await expect(demo).toHaveAttribute("data-playback", "complete");
  await page.waitForTimeout(1200);
  await page
    .getByRole("tab", { name: "Trace the Evidence", exact: true })
    .click();
  const claim = demo.getByRole("button", {
    name: "Alice Chen — parent of — Bob Chen",
    exact: true,
  });
  await expect(claim).toBeVisible();
  // Hold meaningful states long enough to read in the review recording.
  await page.waitForTimeout(1800);
  await claim.click();
  await expect(demo.locator("mark[data-evidence-id]")).toBeVisible();
  await page.waitForTimeout(1800);
  await demo
    .getByRole("button", {
      name: "Carol Wong — beneficiary of — Evergreen Family Trust",
      exact: true,
    })
    .click();
  await page.waitForTimeout(1800);
  await page.getByRole("contentinfo").scrollIntoViewIfNeeded();
  await page.waitForTimeout(1800);
  const video = page.video();
  await page.close();
  await video?.saveAs("artifacts/landing-walkthrough.webm");
});
