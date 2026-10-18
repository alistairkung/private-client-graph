import { expect, test, type Page } from "@playwright/test";
import { fileURLToPath } from "node:url";

const pdf = fileURLToPath(
  new URL("../../tests/fixtures/synthetic-proposal.pdf", import.meta.url),
);

type ContrastTarget = {
  selector: string;
  label: string;
  part?: "placeholder" | "outline" | "border" | "stroke";
  minimum?: number;
};
async function checkContrast(page: Page, targets: ContrastTarget[]) {
  // Buttons transition between disabled and enabled colors after form input.
  await expect(async () => {
    const results = await page.evaluate((targets) => {
      type Color = [number, number, number, number];
      function parse(value: string): Color {
        const parts = value.match(/[\d.]+/g)?.map(Number);
        if (!parts || parts.length < 3)
          throw new Error("Unsupported computed color: " + value);
        return [parts[0], parts[1], parts[2], parts[3] ?? 1];
      }
      function composite(front: Color, back: Color): Color {
        return [
          front[0] * front[3] + back[0] * (1 - front[3]),
          front[1] * front[3] + back[1] * (1 - front[3]),
          front[2] * front[3] + back[2] * (1 - front[3]),
          1,
        ];
      }
      function background(element: Element | null): Color {
        if (!element) return [255, 255, 255, 1];
        return composite(
          parse(getComputedStyle(element).backgroundColor),
          background(element.parentElement),
        );
      }
      function luminance(color: Color) {
        return color
          .slice(0, 3)
          .map((value) => {
            const channel = value / 255;
            return channel <= 0.04045
              ? channel / 12.92
              : ((channel + 0.055) / 1.055) ** 2.4;
          })
          .reduce(
            (total, value, index) =>
              total + value * [0.2126, 0.7152, 0.0722][index],
            0,
          );
      }
      return targets.map((target) => {
        const element = document.querySelector(target.selector);
        if (!element) throw new Error("Missing contrast target: " + target.label);
        const style = getComputedStyle(
          element,
          target.part === "placeholder" ? "::placeholder" : null,
        );
        const foreground =
          target.part === "outline"
            ? style.outlineColor
            : target.part === "border"
              ? style.borderTopColor
              : target.part === "stroke"
                ? style.stroke
                : style.color;
        const surface = background(element);
        const a = luminance(composite(parse(foreground), surface));
        const b = luminance(surface);
        return {
          label: target.label,
          foreground,
          transitioning: element.getAnimations().some(
            (animation) => animation instanceof CSSTransition,
          ),
          ratio: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05),
          minimum: target.minimum ?? 4.5,
        };
      });
    }, targets);
    for (const result of results) {
      expect(result.transitioning, `${result.label} CSS transition`).toBe(false);
      expect(
        result.ratio,
        `${result.label} (${result.foreground}) contrast`,
      ).toBeGreaterThanOrEqual(result.minimum);
    }
  }).toPass({ timeout: 10_000 });
}

test("Forest & Chalk keeps navigation, forms and account surfaces readable", async ({
  page,
}, info) => {
  await page.goto("/auth/login?next=/app");
  await expect(
    page.getByRole("heading", { name: "Matters", exact: true }),
  ).toBeVisible();
  await expect(page.locator("main")).toHaveCSS("opacity", "1");
  await checkContrast(page, [
    { selector: "h1", label: "page heading" },
    { selector: ".record-identity > span", label: "Matter title" },
    {
      selector: ".search-field input",
      label: "search placeholder",
      part: "placeholder",
    },
    { selector: "a.button.primary", label: "primary action" },
  ]);
  if (info.project.name === "phone")
    await page.getByRole("button", { name: "Menu", exact: true }).click();
  await checkContrast(page, [
    { selector: ".brand", label: "rail brand" },
    { selector: ".rail nav a[aria-current=page]", label: "active navigation" },
    { selector: ".rail .language select", label: "language control" },
    { selector: ".rail .icon-button", label: "account icon", minimum: 3 },
  ]);
  const matters = page.locator(".rail nav a[aria-current=page]");
  await matters.focus();
  await matters.press("Tab");
  const next = page.locator('.rail nav a[href="/app/matter-proposals/new"]');
  await expect(next).toBeFocused();
  await expect(next).toHaveCSS("outline-width", "2px");
  await checkContrast(page, [
    {
      selector: '.rail nav a[href="/app/matter-proposals/new"]',
      label: "rail focus ring",
      part: "outline",
      minimum: 3,
    },
  ]);
  await page.getByRole("button", { name: "Account menu", exact: true }).click();
  await expect(page.locator(".account-panel")).toHaveCSS("opacity", "1");
  await checkContrast(page, [
    { selector: ".account-panel h2", label: "account heading" },
    { selector: ".account-panel > a", label: "account link" },
    { selector: ".account-panel > button", label: "account sign out" },
  ]);
  await page.keyboard.press("Escape");
  await next.click();
  await expect(page.locator("main")).toHaveCSS("opacity", "1");
  await page
    .locator('input[name="external_reference"]')
    .fill("SYNTHETIC/PALETTE");
  await page
    .locator('input[name="matter_title"]')
    .fill("Fictional palette check");
  await page.locator('input[type="file"]').setInputFiles(pdf);
  await page.getByRole("checkbox").check();
  await expect(
    page.getByRole("button", { name: "Upload and analyse", exact: true }),
  ).toBeEnabled();
  await checkContrast(page, [
    { selector: ".field-help", label: "field guidance" },
    { selector: ".source-help", label: "source assistance" },
    { selector: ".consent", label: "synthetic consent" },
    { selector: ".intake-form .button.primary", label: "submit action" },
    {
      selector: 'input[name="external_reference"]',
      label: "input boundary",
      part: "border",
      minimum: 3,
    },
  ]);
});

test("forest diagram claims and amber Evidence retain readable contrast", async ({
  page,
}) => {
  await page.goto(
    "/auth/login?next=/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369",
  );
  await page.getByRole("tab", { name: "Graph", exact: true }).click();
  await expect(page.locator(".react-flow__node")).toHaveCount(5);
  await checkContrast(page, [
    { selector: ".entity-node strong", label: "entity name" },
    {
      selector: 'button.edge-label[data-edge-id="0"]',
      label: "relationship label",
    },
    {
      selector: '.react-flow__edge[data-id="1"] .react-flow__edge-path',
      label: "Trust connector",
      part: "stroke",
      minimum: 3,
    },
    {
      selector: '.react-flow__edge[data-id="0"] .react-flow__edge-path',
      label: "family connector",
      part: "stroke",
      minimum: 3,
    },
    {
      selector: ".edge-label-leader",
      label: "label leader",
      part: "stroke",
      minimum: 3,
    },
  ]);
  await page.locator('button.edge-label[data-edge-id="0"]').click();
  await expect(page.locator(".source-text mark")).toBeVisible();
  await checkContrast(page, [
    { selector: ".source-text mark", label: "exact Evidence text" },
    {
      selector: 'button.edge-label[data-edge-id="0"]',
      label: "selected relationship",
    },
  ]);
});
