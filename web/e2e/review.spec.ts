import { expect, test } from "@playwright/test";
import { selectSpouseRelationship } from "./review-helpers";

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
  await expect(page.getByLabel("Graph legend")).toContainText("Parent → child");
  await expect(page.getByLabel("Graph legend")).toContainText("Spouse / sibling");
  await expect(page.getByLabel("Graph legend")).toContainText("Trust role · no flow implied");
  await expect(page.locator(".react-flow__background")).toHaveCount(0);
  const canvas = await page.getByLabel("Relationship graph").boundingBox();
  // Wide panels fit the full structure; narrow panels retain readable scale and pan.
  if (canvas!.width > 450) for (const node of await page.locator(".react-flow__node").all()) {
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
  const beneficiary = page.getByRole("button", {
    name: "Bob Chen — Beneficiary of — Evergreen Family Trust",
    exact: true,
  });
  const beneficiaryLabel = await beneficiary.boundingBox();
  const bob = await page.locator(".react-flow__node", { hasText: "Bob Chen" }).boundingBox();
  const trust = await page.locator(".react-flow__node", { hasText: "Evergreen Family Trust" }).boundingBox();
  const alice = await page.locator(".react-flow__node", { hasText: "Alice Chen" }).boundingBox();
  const david = await page.locator(".react-flow__node", { hasText: "David Chen" }).boundingBox();
  expect(alice!.y + alice!.height).toBeLessThan(trust!.y);
  expect(bob!.y).toBeGreaterThan(trust!.y + trust!.height);
  expect(david!.x + david!.width).toBeLessThan(alice!.x);
  const overlaps = (first: typeof beneficiaryLabel, second: typeof bob) => first!.x < second!.x + second!.width
    && first!.x + first!.width > second!.x && first!.y < second!.y + second!.height
    && first!.y + first!.height > second!.y;
  expect(overlaps(beneficiaryLabel, bob)).toBe(false);
  expect(overlaps(beneficiaryLabel, trust)).toBe(false);
  await expect(beneficiary).toHaveClass(/relationship-trust-role/);
  await expect(page.locator(".react-flow__edge.relationship-trust-role .react-flow__edge-path").first()).not.toHaveAttribute("marker-end");
  await page.getByLabel("Find a relationship").selectOption({ label: "Bob Chen — Beneficiary of — Evergreen Family Trust" });
  await beneficiary.getByText("Beneficiary", { exact: true }).click();
  await expect(beneficiary).toHaveClass(/selected/);
  await expect(page.locator("mark")).toHaveText(
    "Alice Chen confirmed that Bob Chen is a beneficiary of the Evergreen Family Trust.",
  );
  const edge = await selectSpouseRelationship(page);
  await expect(edge).toHaveClass(/selected/);
  await expect(edge).toHaveClass(/relationship-family/);
  await expect(page.locator(".react-flow__edge.relationship-family .react-flow__edge-path").first()).toHaveCSS("stroke-dasharray", "6px, 4px");
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
  const parentId = await parentEdge.getAttribute("data-edge-id");
  await expect(page.locator(`.react-flow__edge[data-id="${parentId}"] .react-flow__edge-path`)).toHaveAttribute("marker-end", /url/);
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
