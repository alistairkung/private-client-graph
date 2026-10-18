import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const evergreen = "/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369";
const pdf = fileURLToPath(
  new URL("../../tests/fixtures/synthetic-proposal.pdf", import.meta.url),
);

test("click, drag and keyboard view changes retain the review context", async ({
  page,
}, info) => {
  await page.goto("/auth/login?next=" + encodeURIComponent(evergreen));
  const graph = page.getByRole("tab", { name: "Graph", exact: true });
  const list = page.getByRole("tab", { name: "List", exact: true });
  await graph.click();
  await expect(page.locator(".react-flow__node")).toHaveCount(5);
  await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  const viewport = page.locator(".react-flow__viewport");
  const camera = await viewport.getAttribute("style");
  const first = await graph.boundingBox();
  const second = await list.boundingBox();
  expect(first).not.toBeNull();
  expect(second).not.toBeNull();
  await page.mouse.move(
    first!.x + first!.width / 2,
    first!.y + first!.height / 2,
  );
  await page.mouse.down();
  await page.mouse.move(
    second!.x + second!.width / 2,
    second!.y + second!.height / 2,
    { steps: 8 },
  );
  await page.mouse.up();
  await expect(list).toHaveAttribute("aria-selected", "true");
  await page
    .getByRole("searchbox", { name: "Find relationship" })
    .fill("Carol");
  await expect(page.locator(".relationship-row:visible")).toHaveCount(1);
  await list.press("Home");
  await expect(graph).toHaveAttribute("aria-selected", "true");
  await expect(viewport).toHaveAttribute("style", camera!);
  const outerScroll = await page.evaluate(() => window.scrollY);
  await page.locator('button.edge-label[data-edge-id="0"]').click();
  await expect(page.locator(".relationship-statement")).toContainText(
    "Alice Chen",
  );
  expect(await page.evaluate(() => window.scrollY)).toBe(outerScroll);
  if (info.project.name === "phone")
    await page
      .getByRole("button", { name: "Back to relationship", exact: true })
      .click();
  await graph.press("End");
  await expect(list).toHaveAttribute("aria-selected", "true");
  await expect(
    page.getByRole("searchbox", { name: "Find relationship" }),
  ).toHaveValue("Carol");
  await graph.click();
  await list.click();
  await graph.click();
  await expect(graph).toHaveAttribute("aria-selected", "true");
  await expect(viewport).toHaveAttribute("style", camera!);
  const query = page.getByRole("searchbox", { name: "Find relationship" });
  await graph.press("End");
  await query.fill("");
  await page.locator("#relationship-0").click();
  if (info.project.name === "desktop")
    await page
      .getByRole("button", { name: "Inspect in source", exact: true })
      .click();
  await expect(page.locator(".source-text mark")).toBeFocused();
  await expect(page.locator(".source-relationship-context")).toContainText(
    "Alice Chen",
  );
  if (info.project.name === "desktop") {
    const inspector = await page.locator(".evidence-inspector").boundingBox();
    expect(inspector!.y + inspector!.height).toBeLessThanOrEqual(
      page.viewportSize()!.height + 1,
    );
  }
  await page.screenshot({
    path: `artifacts/${info.project.name}-interaction.png`,
    fullPage: true,
  });
});

test("reduced-motion control and client navigation preserve camera and search", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/auth/login?next=" + encodeURIComponent(evergreen));
  await page.getByRole("tab", { name: "Graph", exact: true }).click();
  await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  const camera = await page
    .locator(".react-flow__viewport")
    .getAttribute("style");
  await page.getByRole("tab", { name: "List", exact: true }).click();
  await page
    .getByRole("searchbox", { name: "Find relationship" })
    .fill("Alice");
  const documentStart = await page.evaluate(() => performance.timeOrigin);
  await page
    .getByRole("link", { name: /Back to Matters$|^Matters$/ })
    .filter({ visible: true })
    .last()
    .click();
  await expect(page.locator("h1")).toHaveText("Matters");
  await page.getByRole("searchbox").fill("PC/2026/0142");
  await page.getByRole("link", { name: /PC\/2026\/0142/ }).click();
  expect(await page.evaluate(() => performance.timeOrigin)).toBe(documentStart);
  await expect(
    page.getByRole("tab", { name: "List", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(
    page.getByRole("searchbox", { name: "Find relationship" }),
  ).toHaveValue("Alice");
  await page.getByRole("tab", { name: "Graph", exact: true }).click();
  await expect(page.locator(".react-flow__viewport")).toHaveAttribute(
    "style",
    camera!,
  );
});

test("intake retains its fictional entries and selected PDF during app navigation", async ({
  page,
}) => {
  await page.goto("/auth/login?next=/app");
  await page.getByRole("searchbox").fill("PC/2026/0142");
  await page
    .getByRole("link", { name: "New proposal", exact: true })
    .filter({ visible: true })
    .last()
    .click();
  await page
    .locator('input[name="external_reference"]')
    .fill("SYNTHETIC/DRAFT");
  await page
    .locator('input[name="matter_title"]')
    .fill("Fictional retained draft");
  await page.locator('input[type="file"]').setInputFiles(pdf);
  await page
    .locator('input[name="source_title_0"]')
    .fill("Fictional retained source");
  const documentStart = await page.evaluate(() => performance.timeOrigin);
  await page.getByRole("link", { name: /Back to Matters$/ }).click();
  await expect(page.getByRole("searchbox")).toHaveValue("PC/2026/0142");
  await page
    .getByRole("link", { name: "New proposal", exact: true })
    .filter({ visible: true })
    .last()
    .click();
  expect(await page.evaluate(() => performance.timeOrigin)).toBe(documentStart);
  await expect(page.locator('input[name="external_reference"]')).toHaveValue(
    "SYNTHETIC/DRAFT",
  );
  await expect(page.locator('input[name="matter_title"]')).toHaveValue(
    "Fictional retained draft",
  );
  await expect(page.locator('input[name="source_title_0"]')).toHaveValue(
    "Fictional retained source",
  );
  await expect(page.locator(".source-uploads")).toContainText(
    "synthetic-proposal.pdf",
  );
});

test("submission keeps the active form open and retains an unknown outcome across navigation", async ({
  page,
}) => {
  let release = () => {};
  const responseGate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/matter-proposals", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    await responseGate;
    await route.fulfill({
      status: 503,
      json: {
        error: {
          code: "outcome_unknown",
          message: "diagnostic must not render",
          retryable: false,
          outcome_unknown: true,
        },
      },
    });
  });
  await page.goto("/auth/login?next=/app/matter-proposals/new");
  await page
    .locator('input[name="external_reference"]')
    .fill("SYNTHETIC/UNKNOWN");
  await page
    .locator('input[name="matter_title"]')
    .fill("Fictional interrupted submission");
  await page.locator('input[type="file"]').setInputFiles(pdf);
  await page.getByRole("checkbox").check();
  await page
    .getByRole("button", { name: "Upload and analyse", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Uploading and analysing…", exact: true }),
  ).toBeDisabled();
  await page.getByRole("link", { name: /Back to Matters$/ }).click();
  await expect(page).toHaveURL(/\/app\/matter-proposals\/new$/);
  release();
  await expect(page.getByRole("alert")).toContainText("outcome is unknown");
  await page.getByRole("link", { name: /Back to Matters$/ }).click();
  await page
    .getByRole("link", { name: "New proposal", exact: true })
    .filter({ visible: true })
    .last()
    .click();
  await expect(page.locator('input[name="matter_title"]')).toHaveValue(
    "Fictional interrupted submission",
  );
  await expect(page.locator(".source-uploads")).toContainText(
    "synthetic-proposal.pdf",
  );
  await expect(page.getByRole("alert")).toContainText("outcome is unknown");
  await expect(
    page.getByRole("button", {
      name: "Check reference and retry",
      exact: true,
    }),
  ).toBeDisabled();
  await expect(page.getByText("diagnostic must not render")).toHaveCount(0);
});
