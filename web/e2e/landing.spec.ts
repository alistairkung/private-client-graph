import { expect, test, type Page } from "@playwright/test";
import type { CanonicalState } from "../src/shared/contracts";
import { relationshipStatement } from "../src/features/review/presentation";
const publicCase = "/api/showcase/cases/case-01";
async function storyProgress(page: Page, progress: number) {
  await page.locator(".landing-story-track").evaluate((track, fraction) => {
    window.scrollTo({
      top:
        track.getBoundingClientRect().top +
        window.scrollY +
        (track.clientHeight - window.innerHeight) * fraction,
      behavior: "instant",
    });
  }, progress);
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      ),
  );
}
async function selectedQuoteVisible(page: Page) {
  await expect
    .poll(() =>
      page.locator(".landing-story-source-scroll").evaluate((pane) => {
        const quote = pane.querySelector("mark");
        if (!quote) return false;
        const bounds = pane.getBoundingClientRect();
        const mark = quote.getBoundingClientRect();
        return mark.top >= bounds.top - 1 && mark.bottom <= bounds.bottom + 1;
      }),
    )
    .toBe(true);
}
async function clearPhoneLabels(page: Page) {
  await expect
    .poll(() =>
      page.locator(".landing-story-drawing").evaluate((drawing) => {
        const captions = [
          ...drawing.querySelectorAll("[data-entity-id] span"),
        ].map((item) => item.getBoundingClientRect());
        const labels = [
          ...drawing.querySelectorAll("[data-relationship-index]"),
        ].map((item) => item.getBoundingClientRect());
        const overlaps = (a: DOMRect, b: DOMRect) =>
          Math.min(a.right, b.right) - Math.max(a.left, b.left) > 0.5 &&
          Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 0.5;
        // Fractional translations can report a CSS 44px box as 43.9999847px.
        // This allowance is smaller than one Chromium layout unit (1/64px).
        const minimumTargetSize = 44 - 0.001;
        return labels.flatMap((label, index) => {
          const undersized =
            label.height < minimumTargetSize || label.width < minimumTargetSize;
          const clipped = label.left < 0 || label.right > window.innerWidth;
          const captionOverlap = captions.some((caption) =>
            overlaps(label, caption),
          );
          const labelOverlap = labels
            .slice(index + 1)
            .some((other) => overlaps(label, other));
          return undersized || clipped || captionOverlap || labelOverlap
            ? [{
                index,
                width: label.width,
                height: label.height,
                undersized,
                clipped,
                captionOverlap,
                labelOverlap,
              }]
            : [];
        });
      }),
    )
    .toEqual([]);
}
async function clearRelationshipHint(page: Page) {
  await expect
    .poll(() => page.locator(".landing-story-relationship-hint").evaluate(element => {
      const box = element.getBoundingClientRect();
      const obstacles = document.querySelectorAll(
        ".landing-story-edge-label, .landing-story-entity span, .landing-story-entity svg, .landing-story-source-holder, .landing-story-graph-heading",
      );
      const overlaps = [...obstacles].filter(other => {
        const bounds = other.getBoundingClientRect();
        return (
          Math.min(box.right, bounds.right) - Math.max(box.left, bounds.left) > 0.5 &&
          Math.min(box.bottom, bounds.bottom) - Math.max(box.top, bounds.top) > 0.5
        );
      });
      return {
        overlaps: overlaps.map(other => other.getAttribute("class")),
        clipped: box.left < 0 || box.right > window.innerWidth,
        capturesInput: getComputedStyle(element).pointerEvents !== "none",
      };
    }))
    .toEqual({ overlaps: [], clipped: false, capturesInput: false });
}
async function openReview(page: Page) {
  await page
    .getByRole("link", { name: "Skip to relationship review", exact: true })
    .click();
  await expect(page.locator("#landing-story-review")).not.toHaveAttribute(
    "inert",
  );
  await expect
    .poll(() =>
      page
        .locator(".landing-story-source-holder")
        .evaluate((element) => Number(getComputedStyle(element).opacity)),
    )
    .toBe(1);
  await selectedQuoteVisible(page);
}

test("documents become one real graph, every relationship highlights its exact full-source Evidence", async ({
  page,
}, info) => {
  const requests: string[] = [];
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (path.startsWith("/api/")) requests.push(request.method() + " " + path);
  });
  await page.goto("/");
  await expect(page.locator("h1")).toContainText("Build the structure.");
  await expect(
    page.getByRole("heading", { name: "It begins with your documents" }),
  ).toBeVisible();
  const response = await page.request.get(publicCase);
  expect(response.ok()).toBe(true);
  const { state } = (await response.json()) as { state: CanonicalState };
  await storyProgress(page, 0);
  await expect(page.locator("[data-document-kind]")).toHaveCount(4);
  for (const format of await page
    .locator(".landing-story-format-list > span")
    .all()) {
    const box = await format.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  }
  await page.screenshot({
    path: `artifacts/landing-documents-${info.project.name}.png`,
    animations: "allow",
  });
  await openReview(page);
  const demo = page.getByRole("region", {
    name: "Explore the synthetic example",
  });
  await expect(demo.locator(".landing-story-edge-layer > path")).toHaveCount(
    state.relationships.length,
  );
  await expect(demo.locator(".landing-story-source-text")).toHaveText(
    state.sources[0].text,
    { useInnerText: false },
  );
  expect(await demo.locator(".landing-story-source-text").textContent()).toBe(
    state.sources[0].text,
  );
  const geometry = await demo.evaluate((region) => {
    const failures: string[] = [];
    for (const path of region.querySelectorAll<SVGPathElement>(
      ".landing-story-edge-layer > path",
    )) {
      const length = path.getTotalLength();
      const matrix = path.getScreenCTM()!;
      if (length < 10) failures.push("collapsed connector");
      for (const [id, distance] of [
        [path.dataset.source, 0],
        [path.dataset.target, length],
      ] as const) {
        const glyph = region.querySelector<SVGSVGElement>(
          `[data-entity-id="${id}"] svg`,
        );
        if (!glyph) {
          failures.push("missing " + id);
          continue;
        }
        const point = path.getPointAtLength(distance);
        const x = point.x * matrix.a + point.y * matrix.c + matrix.e;
        const y = point.x * matrix.b + point.y * matrix.d + matrix.f;
        const box = glyph.getBoundingClientRect();
        const directedTarget =
          distance === length && path.hasAttribute("marker-end");
        if (directedTarget) {
          const shape =
            glyph.querySelector<SVGGeometryElement>("circle, path")!;
          const local = new DOMPoint(x, y).matrixTransform(
            shape.getScreenCTM()!.inverse(),
          );
          if (shape.isPointInFill(local) || shape.isPointInStroke(local))
            failures.push("covered arrow " + id);
          // The tip must remain close to the shape, rather than floating away.
          const center = new DOMPoint(24, 24).matrixTransform(
            glyph.getScreenCTM()!,
          );
          const vx = x - center.x;
          const vy = y - center.y;
          const radius = Math.hypot(vx, vy);
          const inward = new DOMPoint(
            x - (vx / radius) * 6,
            y - (vy / radius) * 6,
          ).matrixTransform(shape.getScreenCTM()!.inverse());
          if (!shape.isPointInFill(inward))
            failures.push("detached arrow " + id);
        } else if (
          x < box.left - 3 ||
          x > box.right + 3 ||
          y < box.top - 3 ||
          y > box.bottom + 3
        )
          failures.push("detached " + id);
      }
    }
    return failures;
  });
  expect(geometry).toEqual([]);
  for (const relationship of state.relationships) {
    const claim = demo.getByRole("button", {
      name: relationshipStatement(state, relationship, (key) => key),
      exact: true,
    });
    const outer = await page.evaluate(() => window.scrollY);
    await claim.click();
    await expect(claim).toHaveAttribute("aria-pressed", "true");
    await expect(claim).toBeFocused();
    expect(await page.evaluate(() => window.scrollY)).toBe(outer);
    for (const id of relationship.evidence_ids) {
      const evidence = state.evidence.find((item) => item.id === id)!;
      const marks = demo.locator(`mark[data-evidence-ids~="${id}"]`);
      expect(await marks.count()).toBeGreaterThan(0);
      for (const mark of await marks.all())
        await expect(mark).toHaveText(evidence.supporting_text);
      await expect(demo.locator(".landing-story-source-meta")).toContainText(
        evidence.source_id!,
      );
    }
    await selectedQuoteVisible(page);
  }
  if (page.viewportSize()!.width <= 700) await clearPhoneLabels(page);
  const paths = demo.locator(".landing-story-edge-layer > path");
  for (let index = 0; index < state.relationships.length; index++) {
    const type = state.relationships[index].type;
    const path = paths.nth(index);
    if (["parent_of", "spouse_of", "sibling_of"].includes(type))
      await expect(path).toHaveAttribute("stroke-dasharray", "5 5");
    else await expect(path).not.toHaveAttribute("stroke-dasharray");
    if (["spouse_of", "sibling_of"].includes(type))
      await expect(path).not.toHaveAttribute("marker-end");
    else await expect(path).toHaveAttribute("marker-end", /url\(#/);
  }
  await page.screenshot({
    path: `artifacts/landing-review-${info.project.name}.png`,
    animations: "allow",
  });
  expect(requests.length).toBeGreaterThan(0);
  expect(requests.every((request) => request === "GET " + publicCase)).toBe(
    true,
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("scroll scrubs document fronts, measured name movement and masked drawing; reverse keeps selection", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator(".landing-story")).toHaveAttribute(
    "data-story-mode",
    "scroll",
  );
  for (const [progress, kind] of [
    [0, "attendance"],
    [0.12, "email"],
    [0.19, "timesheet"],
    [0.27, "legal"],
  ] as const) {
    await storyProgress(page, progress);
    await expect
      .poll(() =>
        page
          .locator(`[data-document-kind="${kind}"]`)
          .evaluate((element) => getComputedStyle(element).zIndex),
      )
      .toBe("5");
    const contentsFit = await page
      .locator(`[data-document-kind="${kind}"]`)
      .evaluate((element) => element.scrollHeight <= element.clientHeight);
    expect(contentsFit, `${kind} content stays inside its paper`).toBe(true);
  }
  await storyProgress(page, 0.44);
  const travelling = await page
    .locator(".landing-story-entity-content")
    .evaluateAll((nodes) =>
      nodes.some((node) => {
        const matrix = new DOMMatrix(getComputedStyle(node).transform);
        return Math.abs(matrix.m41) + Math.abs(matrix.m42) > 5;
      }),
    );
  expect(travelling).toBe(true);
  await storyProgress(page, 0.69);
  const partial = await page
    .locator(".landing-story-edge-layer mask path")
    .evaluateAll((nodes) =>
      nodes.some((node) => {
        const dash = parseFloat(getComputedStyle(node).strokeDasharray);
        return dash > 0 && dash < 1;
      }),
    );
  expect(partial).toBe(true);
  await expect(page.getByText("Try this relationship", { exact: true })).toHaveCount(0);
  await storyProgress(page, 1);
  await expect(page.getByText("Try this relationship", { exact: true })).toBeVisible();
  await openReview(page);
  const claim = page.getByRole("button", {
    name: "Carol Wong — beneficiary of — Evergreen Family Trust",
    exact: true,
  });
  await claim.click();
  await expect(page.locator(".landing-story-edge-label[data-inviting]")).toHaveCount(0);
  const evidence = await page
    .locator(".landing-story-source-meta")
    .textContent();
  await storyProgress(page, 0.1);
  await storyProgress(page, 1);
  await expect(page.getByText("Try this relationship", { exact: true })).toHaveCount(0);
  await expect(claim).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".landing-story-source-meta")).toHaveText(
    evidence!,
  );
});

test("paper flick lifts before its layer handoff, settles and reverses without delaying review", async ({
  page,
}) => {
  await page.goto("/");
  const email = page.locator('[data-document-kind="email"]');
  const pose = () => email.evaluate(element => {
    const style = getComputedStyle(element);
    const matrix = new DOMMatrix(style.transform);
    return {
      x: matrix.m41,
      y: matrix.m42,
      rotation: Math.atan2(matrix.m12, matrix.m11) * 180 / Math.PI,
      front: style.zIndex === "5",
    };
  });
  await storyProgress(page, 0.065);
  await expect.poll(async () => {
    const value = await pose();
    return value.x > 80 && value.y < -26 && !value.front;
  }).toBe(true);
  const formatBottom = await page.locator(".landing-story-format-list")
    .evaluate(element => element.getBoundingClientRect().bottom);
  expect((await email.boundingBox())!.y).toBeGreaterThan(formatBottom + 4);
  await storyProgress(page, 0.12);
  await expect.poll(async () => {
    const value = await pose();
    return value.front && Math.abs(value.x) < 1 && Math.abs(value.rotation) < 0.2;
  }).toBe(true);
  await storyProgress(page, 0.065);
  await expect.poll(async () => {
    const value = await pose();
    return value.y < -26 && !value.front;
  }).toBe(true);
  await openReview(page);
  await expect(email).toHaveCSS("opacity", "0");
  await expect(page.locator("#landing-story-review")).not.toHaveAttribute("inert");
});

test("keyboard skip and live reduced motion expose an in-flow review while preserving selection", async ({
  page,
}) => {
  await page.goto("/");
  const skip = page.getByRole("link", { name: "Skip to relationship review" });
  await skip.focus();
  await skip.press("Enter");
  await expect(page.locator("#landing-story-review")).toBeFocused();
  await expect(page.getByText("Try this relationship", { exact: true })).toBeVisible();
  await expect(page.locator(".landing-story-edge-label[data-inviting]")).toHaveCount(1);
  await expect(page.locator(".landing-story-edge-label[data-inviting]"))
    .toHaveAccessibleDescription("Try this relationship");
  const claim = page.getByRole("button", {
    name: "Carol Wong — beneficiary of — Evergreen Family Trust",
    exact: true,
  });
  await claim.focus();
  await claim.press("Enter");
  await expect(page.locator(".landing-story-edge-label[data-inviting]")).toHaveCount(0);
  await expect(page.getByText("Try this relationship", { exact: true })).toHaveCount(0);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(page.locator(".landing-story")).toHaveAttribute(
    "data-story-mode",
    "static",
  );
  await expect(page.locator(".landing-story-stage")).toHaveCSS(
    "position",
    "relative",
  );
  await expect(claim).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".landing-story-edge-label[data-inviting]")).toHaveCount(0);
  await expect(page.locator("[data-document-kind]")).toHaveCount(4);
  for (const doc of await page.locator("[data-document-kind]").all()) {
    await expect(doc).toHaveCSS("position", "relative");
    expect(
      await doc.evaluate(
        (element) => element.scrollHeight <= element.clientHeight,
      ),
    ).toBe(true);
  }
  await claim.focus();
  await expect(claim).toBeFocused();
  expect(
    await claim.evaluate((element) =>
      parseFloat(getComputedStyle(element).outlineWidth),
    ),
  ).toBeGreaterThanOrEqual(2);
});

test("initial reduced motion shows all documents and keeps graph/source readable after resize", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator(".landing-story")).toHaveAttribute(
    "data-story-mode",
    "static",
  );
  await expect(page.getByText("Try this relationship", { exact: true })).toBeVisible();
  await expect(page.locator(".landing-story-relationship-hint")).toHaveCSS("transform", "none");
  await expect(page.locator(".landing-story-graph-heading")).toHaveCSS("opacity", "1");
  const source = page.locator(".landing-story-source-text");
  const text = await source.textContent();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".landing-story-source-holder")).toHaveCSS(
    "position",
    "relative",
  );
  expect(await source.textContent()).toBe(text);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("the forest story flows directly into the decision section; light returns with research content", async ({
  page,
}, info) => {
  await page.goto("/");
  await expect(page.locator(".landing-story")).toBeVisible();
  const boundary = await page.evaluate(() => {
    const story = document.querySelector(".landing-example-shell")!;
    const decision = document.querySelector(".landing-acceptance")!;
    const research = document.querySelector(".landing-research")!;
    return {
      gap:
        decision.getBoundingClientRect().top -
        story.getBoundingClientRect().bottom,
      story: getComputedStyle(story).backgroundColor,
      decision: getComputedStyle(decision).backgroundColor,
      research: getComputedStyle(research).backgroundColor,
      next: story.nextElementSibling === decision,
      researchContent: research.textContent!.trim().length,
    };
  });
  expect(boundary.gap).toBe(0);
  expect(boundary.next).toBe(true);
  expect(boundary.story).toBe(boundary.decision);
  expect(boundary.research).not.toBe(boundary.decision);
  expect(boundary.researchContent).toBeGreaterThan(100);
  await page.locator(".landing-acceptance").evaluate((element) =>
    window.scrollTo({
      top: element.getBoundingClientRect().top + window.scrollY - 150,
      behavior: "instant",
    }),
  );
  await page.screenshot({
    path: `artifacts/landing-boundary-${info.project.name}.png`,
    animations: "allow",
  });
});

test("phone graph captions and all six relationship targets remain separate at narrow widths", async ({
  page,
}, info) => {
  test.skip(
    info.project.name !== "phone",
    "Phone layout checks run in the phone project.",
  );
  await page.goto("/");
  for (const width of [320, 390, 700]) {
    await page.setViewportSize({ width, height: 844 });
    await openReview(page);
    await clearPhoneLabels(page);
    // Linux CI renders these parent labels 54px wide; reserve 60px as a font-metric regression.
    const widerLabels = await page.addStyleTag({ content: `
      .landing-story [data-relationship-index="0"],
      .landing-story [data-relationship-index="5"] { min-width: 60px; }
    ` });
    await clearPhoneLabels(page);
    // A real CSS translation exposes DOMRect precision differences between runners.
    await page.locator(".landing-story-drawing").evaluate(element => {
      (element as HTMLElement).style.transform = "translateY(0.3px)";
    });
    await clearPhoneLabels(page);
    await page.locator(".landing-story-drawing").evaluate(element => {
      (element as HTMLElement).style.removeProperty("transform");
    });
    await widerLabels.evaluate(element => element.parentNode?.removeChild(element));
    await clearPhoneLabels(page);
    await page.screenshot({ path: info.outputPath(`landing-labels-${width}.png`) });
  }
});

for (const height of [667, 760]) {
  for (const width of [390, 320]) {
    test(`compact phone ${width}x${height} uses the readable static review without label collisions`, async ({
      page,
    }, info) => {
      test.skip(info.project.name !== "phone", "Compact phone regression.");
      await page.setViewportSize({ width, height });
      await page.goto("/");
      await expect(page.locator(".landing-story")).toHaveAttribute(
        "data-story-mode",
        "static",
      );
      await expect(page.locator(".landing-story-stage")).toHaveCSS(
        "position",
        "relative",
      );
      await openReview(page);
      await clearPhoneLabels(page);
    });
  }
}
test("phone fallback includes 800px and preserves the animated 844px story", async ({
  page,
}, info) => {
  test.skip(
    info.project.name !== "phone",
    "Phone fallback boundary regression.",
  );
  await page.setViewportSize({ width: 390, height: 800 });
  await page.goto("/");
  await expect(page.locator(".landing-story")).toHaveAttribute(
    "data-story-mode",
    "static",
  );
  await openReview(page);
  await clearPhoneLabels(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".landing-story")).toHaveAttribute(
    "data-story-mode",
    "scroll",
  );
  await openReview(page);
  await clearPhoneLabels(page);
});

test("public read failure retries the real backend without a fabricated fallback", async ({
  page,
}) => {
  await page.route("**" + publicCase, (route) =>
    route.fulfill({ status: 503, json: { error: "unavailable" } }),
  );
  await page.goto("/");
  const retry = page.getByRole("button", { name: "Try again", exact: true });
  await expect(retry).toBeVisible();
  await expect(page.locator(".landing-story")).toHaveCount(0);
  await page.unroute("**" + publicCase);
  await retry.click();
  await openReview(page);
  await expect(
    page.getByRole("button", {
      name: "Alice Chen — parent of — Bob Chen",
      exact: true,
    }),
  ).toBeVisible();
});

test("language changes keep exact source and canonical selection; public and practitioner routes remain", async ({
  page,
}) => {
  await page.goto("/");
  await openReview(page);
  await page
    .getByRole("button", {
      name: "Carol Wong — beneficiary of — Evergreen Family Trust",
      exact: true,
    })
    .click();
  const source = await page.locator(".landing-story-source-text").textContent();
  await page
    .getByRole("combobox", { name: "Language", exact: true })
    .selectOption("zh-CN");
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
  expect(await page.locator(".landing-story-source-text").textContent()).toBe(
    source,
  );
  await expect(
    page.locator('.landing-story-edge-label[aria-pressed="true"]'),
  ).toContainText("受益人");
  await expect(page.locator('a[href="/app"]').first()).toHaveAttribute(
    "href",
    "/app",
  );
  await expect(
    page.locator('a[href$="/research-results"]').first(),
  ).toHaveAttribute("href", "/research-results");
  await page.locator('a[href="/app"]').first().click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.locator(".atlas")).toBeVisible();
});

test("contextual hint clears graph labels, captions and Evidence in both languages and dismisses on selection", async ({ page }, info) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/");
  await openReview(page);
  const selection = page.locator('.landing-story-edge-label[aria-pressed="true"]');
  const initial = await selection.getAttribute("data-relationship-index");
  const source = await page.locator(".landing-story-source-text").textContent();
  const widths = info.project.name === "phone" ? [320, 390, 700] : [701, 900, 1512];
  for (const reducedMotion of ["no-preference", "reduce"] as const) {
    await page.locator(".public-header select").selectOption("en");
    await page.emulateMedia({ reducedMotion });
    await page.goto("/");
    await openReview(page);
    for (const width of widths) {
      await page.setViewportSize({ width, height: info.project.name === "phone" ? 844 : 982 });
      for (const locale of ["en", "zh-CN"]) {
        await page.locator(".public-header select").selectOption(locale);
        if (reducedMotion === "no-preference") await storyProgress(page, 1);
        const hint = page.locator(".landing-story-relationship-hint");
        await expect(hint).toHaveCSS("opacity", "1");
        await expect(hint).toHaveText(locale === "en" ? "Try this relationship" : "试着选择这项关系");
        await expect(selection).toHaveAttribute("data-relationship-index", initial!);
        await expect(page.locator(".landing-story-edge-label[data-inviting]")).toHaveAttribute("aria-pressed", "false");
        await clearRelationshipHint(page);
        if (width <= 700) await clearPhoneLabels(page);
        if (reducedMotion === "reduce") await expect(hint).toHaveCSS("transform", "none");
        await page.locator(".landing-story-graph-holder").screenshot({ path: info.outputPath(`hint-${width}-${locale}-${reducedMotion}.png`) });
      }
    }
  }
  expect(await page.locator(".landing-story-source-text").textContent()).toBe(source);
  const target = page.locator(".landing-story-edge-label[data-inviting]");
  if (info.project.name === "phone") await target.tap();
  else {
    await target.focus();
    await target.press("Space");
  }
  await expect(page.locator(".landing-story-relationship-hint")).toHaveCount(0);
  await page.locator(".public-header select").selectOption("en");
  await expect(page.locator(".landing-story-relationship-hint")).toHaveCount(0);
  expect(errors).toEqual([]);
});
