import { expect, test, type Locator } from "@playwright/test";
import { writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import type { CanonicalState, Evidence } from "../src/shared/contracts";

test.use({ video: { mode: "on", size: { width: 1512, height: 982 } } });

const evergreen = "/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369";
const familyPdf = fileURLToPath(
  new URL("../../tests/fixtures/synthetic-proposal.pdf", import.meta.url),
);
const trustPdf = fileURLToPath(
  new URL("../../tests/fixtures/multiple-role-proposal.pdf", import.meta.url),
);

async function expectPassageVisible(mark: Locator) {
  await expect
    .poll(() =>
      mark.evaluate((target) => {
        const reader = target
          .closest(".source-scroll")!
          .getBoundingClientRect();
        const rect = target.getBoundingClientRect();
        return rect.top >= reader.top - 1 && rect.bottom <= reader.bottom + 1;
      }),
    )
    .toBe(true);
}

test("relationship selection smoothly reveals exact Evidence without moving the outer workspace", async ({
  page,
}, info) => {
  await page.goto("/auth/login?next=" + encodeURIComponent(evergreen));
  await page.getByRole("tab", { name: "Graph", exact: true }).click();
  await expect(page.locator(".react-flow__node")).toHaveCount(5);
  const outerScroll = await page.evaluate(() => window.scrollY);
  const camera = await page
    .locator(".react-flow__viewport")
    .getAttribute("style");
  const reader = page.locator(".source-scroll");
  const frames = reader.evaluate(
    (element) =>
      new Promise<number[]>((resolve) => {
        const samples: number[] = [];
        const start = performance.now();
        function sample() {
          samples.push(element.scrollTop);
          if (performance.now() - start > 850) resolve(samples);
          else requestAnimationFrame(sample);
        }
        requestAnimationFrame(sample);
      }),
  );
  const relationship = page.locator('button.edge-label[data-edge-id="0"]');
  await relationship.click();
  const samples = await frames;
  expect(
    new Set(samples.map((value) => Math.round(value))).size,
  ).toBeGreaterThan(3);
  expect(samples.at(-1)!).toBeGreaterThan(100);
  const mark = page.locator(".source-text mark");
  await expect(mark).toContainText(
    "Alice Chen and David Chen are the parents of Bob Chen",
  );
  await expectPassageVisible(mark);
  if (info.project.name === "desktop") await expect(relationship).toBeFocused();
  else await expect(mark).toBeFocused();
  expect(await page.evaluate(() => window.scrollY)).toBe(outerScroll);
  await expect(page.locator(".react-flow__viewport")).toHaveAttribute(
    "style",
    camera!,
  );

  await page.emulateMedia({ reducedMotion: "reduce" });
  if (info.project.name === "phone")
    await page
      .getByRole("button", { name: "Back to relationship", exact: true })
      .click();
  await page.locator('button.edge-label[data-edge-id="4"]').click();
  await expect(mark).toContainText("Carol Wong");
  await expectPassageVisible(mark);
  await page.screenshot({
    path: `artifacts/${info.project.name}-source-reveal.png`,
    fullPage: true,
  });
});

test.describe("multiple source continuity", () => {
  test("five sources retain exact attribution, reveal the active tab and support repeated source changes", async ({
    page,
  }, info) => {
    await page.goto("/auth/login?next=/app/matter-proposals/new");
    await page
      .locator('input[name="external_reference"]')
      .fill(`NEXT/SOURCES/${info.project.name}/${crypto.randomUUID()}`);
    await page
      .locator('input[name="matter_title"]')
      .fill("Fictional multi-source review");
    await page
      .locator('input[type="file"]')
      .setInputFiles([trustPdf, trustPdf, trustPdf, trustPdf, familyPdf]);
    const duplicateTitle =
      "Fictional family and trust review — supplementary instructions and attendance record";
    for (let index = 0; index < 5; index++)
      await page
        .locator(`input[name="source_title_${index}"]`)
        .fill(
          index === 0 || index === 4
            ? duplicateTitle
            : `Fictional trust instruction ${index + 1}`,
        );
    await page.getByRole("checkbox").check();
    await page
      .getByRole("button", { name: "Upload and analyse", exact: true })
      .click();
    await expect(page).toHaveURL(/\/app\/matter-proposals\/[a-f0-9-]+$/);
    const result = await page.request.get(page.url().replace("/app/", "/api/"));
    const { state }: { state: CanonicalState } = await result.json();
    expect(state.sources).toHaveLength(5);
    const tabs = page.locator(".source-tabs > button");
    await expect(tabs).toHaveCount(5);
    await page.getByRole("tab", { name: "List", exact: true }).click();
    const familyIndex = state.relationships.findIndex(
      (edge) => edge.type === "parent_of",
    );
    await page.locator(`#relationship-${familyIndex}`).click();
    const mark = page.locator(".source-text mark");
    await expect(mark).toHaveText(
      "Alice Example is the parent of Ben Example.",
    );
    await expect(tabs.nth(4)).toHaveAttribute("aria-pressed", "true");
    await expect(
      tabs.nth(4).getByText("Supporting Evidence", { exact: true }),
    ).toBeVisible();
    await expect(
      tabs.nth(0).getByText("Supporting Evidence", { exact: true }),
    ).toHaveCount(0);
    await expect
      .poll(() =>
        tabs.nth(4).evaluate((tab) => {
          const strip = tab.parentElement!.getBoundingClientRect();
          const box = tab.getBoundingClientRect();
          return box.left >= strip.left - 1 && box.right <= strip.right + 1;
        }),
      )
      .toBe(true);
    await expectPassageVisible(mark);

    // An unrelated document remains available without inventing Evidence for it.
    await tabs.nth(0).click();
    await expect(tabs.nth(0)).toHaveAttribute("aria-pressed", "true");
    await expect(mark).toHaveCount(0);
    if (info.project.name === "phone")
      await page
        .getByRole("button", { name: "Back to relationship", exact: true })
        .click();
    const trustIndex = state.relationships.findIndex(
      (edge) => edge.type === "beneficiary_of",
    );
    await page.locator(`#relationship-${trustIndex}`).click();
    const trustEvidence = state.relationships[trustIndex].evidence_ids.map(
      (id) => state.evidence.find((item) => item.id === id)!,
    );
    expect(trustEvidence).toHaveLength(4);
    for (const index of [3, 1, 2, 3]) {
      const expected = trustEvidence.find(
        (item) => item.source_id === state.sources[index].id,
      )!;
      await tabs.nth(index).click();
      await expect(tabs.nth(index)).toHaveAttribute("aria-pressed", "true");
      await expect(mark).toHaveAttribute("data-evidence-id", expected.id);
      await expect(mark).toHaveText(expected.supporting_text);
    }
    const expected: Evidence = trustEvidence.find(
      (item) => item.source_id === state.sources[3].id,
    )!;
    await expectPassageVisible(mark);
    await expect(page.locator(".source-footer")).toContainText(expected.id);
    if (info.project.name === "desktop") {
      const selectedEvidence = page.locator(".evidence-item.active");
      await expect(selectedEvidence.locator(".evidence-meta")).toContainText(
        expected.id,
      );
      await expect(selectedEvidence.locator(".evidence-source")).toHaveText(
        state.sources[3].title,
      );
      await expect(selectedEvidence.locator(".evidence-source")).toBeInViewport(
        { ratio: 1 },
      );
    }
    await expect(
      tabs.nth(3).getByText("Supporting Evidence", { exact: true }),
    ).toBeVisible();
    await expect(
      tabs.nth(4).getByText("Supporting Evidence", { exact: true }),
    ).toHaveCount(0);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    if (info.project.name === "desktop")
      await page.getByRole("tab", { name: "Graph", exact: true }).click();
    if (info.project.name === "desktop") {
      await expect(
        page.getByRole("tab", { name: "Graph", exact: true }),
      ).toHaveAttribute("aria-selected", "true");
      await expect(page.locator("#graph-view-panel")).toHaveCSS("opacity", "1");
      await expect(page.locator(".react-flow__node")).toHaveCount(4);
    }
    await page.screenshot({
      path: `artifacts/${info.project.name}-multiple-sources.png`,
      fullPage: true,
    });
    await writeFile(
      info.outputPath("preview.json"),
      JSON.stringify({ url: page.url() }),
    );
    if (process.env.PCG_RECORD_DEMO && info.project.name === "desktop") {
      const video = page.video();
      await page.close();
      await video?.saveAs("artifacts/source-navigation.webm");
    }
  });
});
