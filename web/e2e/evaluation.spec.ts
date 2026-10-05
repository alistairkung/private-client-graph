import { expect, test } from "@playwright/test";

test("evaluation is keyboard reachable with accessible unpublished results and a readable research sequence", async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const evaluationLink = page.getByRole("navigation", { name: "Public navigation" })
    .getByRole("link", { name: "Evaluation", exact: true });
  await expect(evaluationLink).toBeVisible();
  await evaluationLink.focus();
  await evaluationLink.press("Enter");
  const chapter = page.getByRole("region", { name: "How well does it recover the relationships?" });
  await expect(chapter).toBeFocused();
  await expect(page).toHaveURL(/#evaluation$/);
  await expect(chapter.getByRole("heading", { level: 2 })).toBeInViewport();
  const register = chapter.getByRole("table", { name: "Evaluation results" });
  for (const metric of ["Relationship precision", "Relationship recall", "F1", "Provenance accuracy", "Evaluation-set size"]) {
    const row = register.getByRole("row").filter({ has: page.getByRole("rowheader", { name: metric, exact: true }) });
    await expect(row.getByRole("cell", { name: "Not yet published", exact: true })).toBeVisible();
  }
  const stages = [
    page.getByRole("heading", { name: "A proposed graph still needs professional judgment." }),
    chapter.getByRole("heading", { name: "How the benchmark works" }),
    register,
    chapter.getByRole("heading", { name: "Context for a future publication" }),
  ];
  const positions = await Promise.all(stages.map((stage) => stage.boundingBox()));
  for (let index = 1; index < positions.length; index += 1) {
    expect(positions[index]!.y).toBeGreaterThan(positions[index - 1]!.y);
  }
  if (testInfo.project.name === "narrow") {
    const row = register.getByRole("row").filter({ has: page.getByRole("rowheader", { name: "Relationship precision", exact: true }) });
    const label = (await row.getByRole("rowheader").boundingBox())!;
    const result = (await row.getByRole("cell", { name: "Not yet published", exact: true }).boundingBox())!;
    const explanation = (await row.getByRole("cell").last().boundingBox())!;
    expect(result.y).toBeGreaterThanOrEqual(label.y + label.height);
    expect(explanation.y).toBeGreaterThanOrEqual(result.y + result.height);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await chapter.screenshot({ path: testInfo.outputPath("evaluation.png") });
});
