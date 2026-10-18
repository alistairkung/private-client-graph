import { expect, test, type Locator } from "@playwright/test";
import type { CanonicalState } from "../src/shared/contracts";

const evergreen = "/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369";

async function rectangle(locator: Locator) {
  const bounds = await locator.boundingBox();
  expect(bounds).not.toBeNull();
  return bounds!;
}

test("Evergreen graph preserves family structure and every selectable relationship", async ({
  page,
}, info) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/auth/login?next=" + encodeURIComponent(evergreen));
  await expect(page.locator("h1")).toHaveText("Evergreen Family Trust");
  const response = await page.request.get(evergreen.replace("/app/", "/api/"));
  const record = (await response.json()) as { state: CanonicalState };
  const state = record.state;
  if (info.project.name === "phone") {
    await page.getByRole("tab", { name: "Graph", exact: true }).click();
  }

  const nodes = page.locator(".react-flow__node");
  const labels = page.locator("button.edge-label");
  await expect(nodes).toHaveCount(state.entities.length);
  await expect(labels).toHaveCount(state.relationships.length);
  await page.getByRole("button", { name: "Fit graph", exact: true }).click();
  const canvas = await rectangle(page.locator(".graph-container"));

  const obscured = await page
    .locator(".graph-container")
    .evaluate((container) => {
      const labels = Array.from(
        container.querySelectorAll<HTMLElement>(".edge-label"),
      );
      const collisions: string[] = [];
      for (const edge of container.querySelectorAll(".react-flow__edge")) {
        const path = edge.querySelector<SVGPathElement>(
          ".react-flow__edge-path",
        );
        if (!path) continue;
        const transform = path.getScreenCTM()!;
        const length = path.getTotalLength();
        for (const label of labels) {
          if (label.dataset.edgeId === edge.getAttribute("data-id")) continue;
          const box = label.getBoundingClientRect();
          for (let step = 0; step <= 300; step++) {
            const p = path.getPointAtLength((length * step) / 300);
            const x = p.x * transform.a + p.y * transform.c + transform.e;
            const y = p.x * transform.b + p.y * transform.d + transform.f;
            if (
              x > box.left + 1 &&
              x < box.right - 1 &&
              y > box.top + 1 &&
              y < box.bottom - 1
            ) {
              collisions.push(
                `${edge.getAttribute("data-id")} under label ${label.dataset.edgeId}`,
              );
              break;
            }
          }
        }
      }
      return collisions;
    });
  expect(obscured).toEqual([]);

  // Fit includes label and Trust-caption extents, rather than only React Flow nodes.
  const drawingParts = page.locator(
    ".entity-node, .entity-node strong, button.edge-label",
  );
  await expect(async () => {
    for (const part of await drawingParts.all()) {
      const box = await rectangle(part);
      expect(box.x).toBeGreaterThanOrEqual(canvas.x - 1);
      expect(box.y).toBeGreaterThanOrEqual(canvas.y - 1);
      expect(box.x + box.width).toBeLessThanOrEqual(
        canvas.x + canvas.width + 1,
      );
      expect(box.y + box.height).toBeLessThanOrEqual(
        canvas.y + canvas.height + 1,
      );
    }
  }).toPass();

  const person = (name: string) =>
    page.locator(".react-flow__node").filter({ hasText: name });
  const alice = await rectangle(person("Alice Chen"));
  const david = await rectangle(person("David Chen"));
  const bob = await rectangle(person("Bob Chen"));
  const trust = await rectangle(page.locator(".trust-entity"));
  expect(Math.abs(alice.y - david.y)).toBeLessThan(1);
  expect(trust.y).toBeGreaterThan(alice.y + alice.height);
  expect(bob.y).toBeGreaterThan(trust.y + trust.height);

  if (info.project.name === "desktop") {
    expect(trust.width).toBeGreaterThan(100);
    const obstacles = await page
      .locator(".entity-node, .entity-node strong")
      .evaluateAll((elements) =>
        elements.map((element) => {
          const { x, y, width, height } = element.getBoundingClientRect();
          return { x, y, width, height };
        }),
      );
    const previous: typeof obstacles = [];
    for (const label of await labels.all()) {
      const box = await rectangle(label);
      for (const other of [...obstacles, ...previous]) {
        const intersectionWidth =
          Math.min(box.x + box.width, other.x + other.width) -
          Math.max(box.x, other.x);
        const intersectionHeight =
          Math.min(box.y + box.height, other.y + other.height) -
          Math.max(box.y, other.y);
        expect(intersectionWidth > 1 && intersectionHeight > 1).toBe(false);
      }
      previous.push(box);
    }
    // Selection and language changes must not reset the practitioner's chosen camera.
    await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  }
  const viewport = page.locator(".react-flow__viewport");
  const camera = await viewport.getAttribute("style");
  const edge = state.relationships[0];
  const name = (id: string) =>
    state.entities.find((entity) => entity.id === id)!.name;
  const label = page.locator('button.edge-label[data-edge-id="0"]');
  await expect(label).toHaveAccessibleName(new RegExp(name(edge.source)));
  await expect(label).toHaveAccessibleName(new RegExp(name(edge.target)));
  await label.focus();
  await label.press("Enter");
  await expect(label).toHaveAttribute("aria-pressed", "true");
  await expect(viewport).toHaveAttribute("style", camera!);
  const evidence = state.evidence.find(
    (item) => item.id === edge.evidence_ids[0],
  )!;
  await expect(page.locator(".evidence-item").first().locator("q")).toHaveText(
    evidence.supporting_text,
  );

  if (info.project.name === "desktop") {
    await page
      .getByRole("combobox", { name: "Language", exact: true })
      .selectOption("zh-CN");
    await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
    await expect(viewport).toHaveAttribute("style", camera!);
    await page
      .getByRole("combobox")
      .filter({ visible: true })
      .first()
      .selectOption("en");
  }
  if (info.project.name === "desktop")
    await page.locator(".evidence-item").first().click();
  await expect(page.locator(".source-text mark")).toHaveText(
    evidence.supporting_text,
  );
  await page
    .getByRole("button", { name: "Back to relationship", exact: true })
    .click();
  await expect(label).toBeFocused();
  await page.getByRole("button", { name: "Fit graph", exact: true }).click();
  await page.screenshot({
    path: `artifacts/${info.project.name}-corrected-graph.png`,
    fullPage: true,
  });
});
