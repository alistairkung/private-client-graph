import { expect, test } from "@playwright/test";

test("sample journey uses real API and graph construction, then highlights exact evidence", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await expect(page.getByLabel("Source document")).toContainText(
    "Attendance Note – Meeting with Alice Chen",
  );
  await expect(page.getByText("SYNTHETIC CASE", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Run live analysis" })).toBeDisabled();
  await page.getByRole("button", { name: "Load sample analysis" }).click();
  await expect(
    page.getByText("Sample analysis · Demonstration fixture"),
  ).toBeVisible();
  await expect(page.getByRole("img", { name: "Triangular Trust node" })).toBeVisible();
  const canvas = await page.getByLabel("Relationship graph").boundingBox();
  for (const node of await page.locator(".react-flow__node").all()) {
    await expect
      .poll(async () => {
        const box = await node.boundingBox();
        return (
          box!.x >= canvas!.x &&
          box!.x + box!.width <= canvas!.x + canvas!.width
        );
      })
      .toBe(true);
  }
  const edge = page.getByRole("button", {
    name: "Alice Chen — Spouse of — David Chen",
    exact: true,
  });
  await edge.getByText("Spouse of", { exact: true }).click();
  await expect(edge).toHaveClass(/selected/);
  const highlight = page.locator("mark");
  await expect(highlight).toHaveCount(1);
  await expect(highlight).toHaveText(
    "Alice Chen confirmed that she and David Chen are spouses.",
  );
  await expect(highlight).toBeInViewport();
  await expect(
    page.getByRole("button", { name: /Evidence 1/ }),
  ).toHaveAttribute("aria-pressed", "true");
  if (testInfo.project.name === "narrow") {
    const graph = await page.locator(".graph-panel").boundingBox();
    const source = await page.locator(".source-panel").boundingBox();
    expect(source!.y).toBeGreaterThanOrEqual(graph!.y + graph!.height);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }
  const parentEdge = page.getByRole("button", {
    name: "Alice Chen — Parent of — Bob Chen",
    exact: true,
  });
  await parentEdge.focus();
  await parentEdge.press("Enter");
  await expect(parentEdge).toHaveClass(/selected/);
  await expect(highlight).toHaveText(
    "Alice Chen confirmed that Alice Chen and David Chen are the parents of Bob Chen.",
  );
  await expect(edge).not.toHaveClass(/selected/);
  await expect(highlight).toBeInViewport();
  await page.locator(".document-scroll").evaluate((el) => {
    el.scrollTop = 0;
  });
  const otherParent = page.getByRole("button", {
    name: "David Chen — Parent of — Bob Chen",
    exact: true,
  });
  await otherParent.focus();
  await otherParent.press("Enter");
  await expect(otherParent).toHaveClass(/selected/);
  await expect(highlight).toBeInViewport();
  await page.screenshot({
    path: testInfo.outputPath("review.png"),
    fullPage: true,
  });
});
