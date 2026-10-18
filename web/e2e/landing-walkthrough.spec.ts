import { expect, test } from "@playwright/test";
test.use({ video: { mode: "on", size: { width: 1512, height: 982 } } });
test.skip(!process.env.PCG_RECORD_DEMO, "Run explicitly to refresh review recordings.");

test("record documents becoming a graph and exact Evidence inspection", async ({
  page,
}, info) => {
  test.skip(
    !process.env.PCG_RECORD_LANDING || info.project.name !== "desktop",
    "Opt-in recording, separate from functional gates.",
  );
  await page.goto("/");
  await expect(page.locator(".landing-story")).toBeVisible();
  for (const fraction of [0, 0.12, 0.19, 0.27, 0.44, 0.69, 1]) {
    await page.locator(".landing-story-track").evaluate(
      (track, progress) =>
        window.scrollTo({
          top:
            track.getBoundingClientRect().top +
            window.scrollY +
            (track.clientHeight - window.innerHeight) * progress,
          behavior: "smooth",
        }),
      fraction,
    );
    // Reading holds belong to the opt-in video, never the product animation.
    await page.waitForTimeout(1100);
  }
  for (const name of [
    "Alice Chen — parent of — Bob Chen",
    "Carol Wong — beneficiary of — Evergreen Family Trust",
  ]) {
    await page.getByRole("button", { name, exact: true }).click();
    await page.waitForTimeout(1800);
  }
  await page.locator(".landing-acceptance").scrollIntoViewIfNeeded();
  await page.waitForTimeout(1500);
  const video = page.video();
  await page.close();
  await video?.saveAs("artifacts/landing-walkthrough.webm");
});
