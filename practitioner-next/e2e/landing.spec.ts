import { expect, test } from "@playwright/test";
import type { CanonicalState } from "../src/shared/contracts";
import { relationshipStatement } from "../src/review/presentation";

const publicCase = "/api/showcase/cases/case-01";

test("public example traces every canonical claim to exact Evidence without analysis or sign-in", async ({
  page,
}, info) => {
  const requests: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/api/"))
      requests.push(request.method() + " " + new URL(request.url()).pathname);
  });
  await page.goto("/");
  await expect(page.locator("h1")).toContainText("Every relationship.");
  const response = await page.request.get(publicCase);
  expect(response.ok()).toBe(true);
  const { state } = (await response.json()) as { state: CanonicalState };
  const demo = page.getByRole("region", {
    name: "Explore the synthetic example",
  });
  await expect(demo).toBeVisible();
  await expect(demo.locator(".landing-connectors > path")).toHaveCount(
    state.relationships.length,
  );
  await expect(async () => {
    const broken = await demo.evaluate((region) => {
      const failures: string[] = [];
      for (const path of region.querySelectorAll<SVGPathElement>(
        ".landing-connectors > path",
      )) {
        const length = path.getTotalLength();
        if (length < 10) failures.push("collapsed connector");
        const matrix = path.getScreenCTM()!;
        for (const [id, distance] of [
          [path.dataset.source, 0],
          [path.dataset.target, length],
        ] as const) {
          const glyph = region.querySelector(`[data-entity-id="${id}"] svg`);
          if (!glyph) {
            failures.push("missing endpoint " + id);
            continue;
          }
          const point = path.getPointAtLength(distance);
          const x = point.x * matrix.a + point.y * matrix.c + matrix.e;
          const y = point.x * matrix.b + point.y * matrix.d + matrix.f;
          const box = glyph.getBoundingClientRect();
          if (
            x < box.left - 3 ||
            x > box.right + 3 ||
            y < box.top - 3 ||
            y > box.bottom + 3
          )
            failures.push("detached endpoint " + id);
        }
      }
      return failures;
    });
    expect(broken).toEqual([]);
  }).toPass();
  for (const relationship of state.relationships) {
    const button = demo.getByRole("button", {
      name: relationshipStatement(state, relationship, (key) => key),
      exact: true,
    });
    await button.click();
    await expect(button).toHaveAttribute("aria-pressed", "true");
    const evidence = state.evidence.find(
      (item) => item.id === relationship.evidence_ids[0],
    )!;
    const quote = demo.locator(`mark[data-evidence-id="${evidence.id}"]`);
    await expect(quote).toHaveText(evidence.supporting_text);
    await expect(quote).toBeVisible();
    expect(
      state.sources.find((source) => source.id === evidence.source_id)?.text,
    ).toContain(await quote.innerText());
  }
  const strokes = await demo
    .locator(".landing-connectors > path")
    .evaluateAll((paths) =>
      paths.map((element) => {
        const path = element as SVGPathElement;
        const style = getComputedStyle(path);
        const length = path.getTotalLength();
        const normalized = Number(path.getAttribute("pathLength")) || length;
        return {
          dash: (style.strokeDasharray.match(/[\d.]+/g) ?? []).map(
            (value) => (Number(value) * length) / normalized,
          ),
          opacity: Number(style.strokeOpacity) * Number(style.opacity),
          stroke: style.stroke,
        };
      }),
    );
  state.relationships.forEach((relationship, index) => {
    const stroke = strokes[index];
    expect(stroke.stroke).not.toBe("none");
    expect(stroke.opacity).toBeGreaterThanOrEqual(0.8);
    const family = ["parent_of", "spouse_of", "sibling_of"].includes(
      relationship.type,
    );
    if (family) {
      expect(stroke.dash.length).toBeGreaterThanOrEqual(2);
      for (const segment of stroke.dash) {
        expect(segment).toBeGreaterThan(1);
        expect(segment).toBeLessThan(20);
      }
    } else expect(stroke.dash).toEqual([]);
  });
  expect(requests.length).toBeGreaterThan(0);
  expect(requests.every((request) => request === "GET " + publicCase)).toBe(
    true,
  );
  await expect(page.locator(".atlas")).toHaveCount(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  for (const control of await page
    .locator(
      ".landing-masthead a, .landing-masthead select, .landing-claims button",
    )
    .filter({ visible: true })
    .all()) {
    const box = await control.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(
      page.viewportSize()!.width + 1,
    );
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `artifacts/landing-${info.project.name}.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("keyboard claim selection survives narrative scrolling and reduced motion", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const demo = page.getByRole("region", {
    name: "Explore the synthetic example",
  });
  const claim = demo.getByRole("button", {
    name: "Carol Wong — beneficiary of — Evergreen Family Trust",
    exact: true,
  });
  await claim.focus();
  await claim.press("Enter");
  await expect(claim).toHaveAttribute("aria-pressed", "true");
  const quote = demo.locator("mark[data-evidence-id]");
  const original = await quote.innerText();
  await page.getByRole("contentinfo").scrollIntoViewIfNeeded();
  await expect(claim).toHaveAttribute("aria-pressed", "true");
  await expect(quote).toHaveText(original);
  await claim.scrollIntoViewIfNeeded();
  await claim.focus();
  await expect(claim).toBeFocused();
  const focus = await claim.evaluate((element) => ({
    style: getComputedStyle(element).outlineStyle,
    width: parseFloat(getComputedStyle(element).outlineWidth),
  }));
  expect(focus.style).not.toBe("none");
  expect(focus.width).toBeGreaterThanOrEqual(2);
});

test("public example failure can retry the unchanged backend without a fabricated fallback", async ({
  page,
}) => {
  // Isolated UI failure; retry resumes the real existing showcase API.
  await page.route("**" + publicCase, (route) =>
    route.fulfill({ status: 503, json: { error: "unavailable" } }),
  );
  await page.goto("/");
  const retry = page.getByRole("button", { name: "Try again", exact: true });
  await expect(retry).toBeVisible();
  await expect(page.locator("mark[data-evidence-id]")).toHaveCount(0);
  await page.unroute("**" + publicCase);
  await retry.click();
  await expect(
    page.getByRole("button", {
      name: "Alice Chen — parent of — Bob Chen",
      exact: true,
    }),
  ).toBeVisible();
});

test("landing routes reach the existing public destinations and practitioner sign-in", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator('a[href$="/demo"]').first()).toHaveAttribute(
    "href",
    "https://localhost:8443/demo",
  );
  await expect(
    page.locator('a[href$="/research-results"]').first(),
  ).toHaveAttribute("href", "https://localhost:8443/research-results");
  await page.locator('a[href="/app"]').first().click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(
    page.getByRole("link", { name: "Sign in", exact: true }).first(),
  ).toBeVisible();
  await expect(page.locator(".atlas")).toBeVisible();
});

test("language changes preserve the selected canonical relationship and source words", async ({
  page,
}) => {
  await page.goto("/");
  const claim = page.getByRole("button", {
    name: "Carol Wong — beneficiary of — Evergreen Family Trust",
    exact: true,
  });
  await claim.click();
  const quote = page.locator("mark[data-evidence-id]");
  const exact = await quote.innerText();
  const evidenceId = await quote.getAttribute("data-evidence-id");
  await page
    .getByRole("combobox", { name: "Language", exact: true })
    .selectOption("zh-CN");
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
  await expect(quote).toHaveText(exact);
  await expect(quote).toHaveAttribute("data-evidence-id", evidenceId!);
  await expect(
    page.locator('.landing-claims button[aria-pressed="true"]'),
  ).toContainText("Carol Wong");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
});
