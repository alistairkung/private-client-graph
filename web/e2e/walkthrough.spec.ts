import { expect, test } from "@playwright/test";

const relationships = [
  "Alice Chen — Settlor of — Evergreen Family Trust",
  "Alice Chen — Spouse of — David Chen",
  "Alice Chen — Parent of — Bob Chen",
  "David Chen — Parent of — Bob Chen",
  "Bob Chen — Beneficiary of — Evergreen Family Trust",
  "Carol Wong — Beneficiary of — Evergreen Family Trust",
];

test("sample attention preserves graph geometry, exact source and visitor control", async ({ page }, testInfo) => {
  await page.goto("/");
  const source = await page.getByLabel("Source document").textContent();
  await page.getByRole("button", { name: "Load sample analysis" }).click();
  const passages = page.locator(".sample-passage");
  await expect(passages).toHaveCount(6);
  await expect(page.locator(".relationship-label")).toHaveCount(6);
  await expect(page.locator(".react-flow__node")).toHaveCount(5);

  if (testInfo.project.name === "desktop") {
    await expect(page.locator(".sample-review")).toHaveCSS("position", "sticky");
    await expect(page.getByRole("button", { name: relationships[0], exact: true })).toHaveAttribute("aria-pressed", "true");
    await page.getByLabel("Relationship graph").hover();
    await page.mouse.wheel(0, 80);
    await expect(page.getByText(/Guided sample walkthrough\. Choose/)).toBeVisible();
    const viewport = await page.locator(".react-flow__viewport").getAttribute("style");
    const positions = await page.locator(".react-flow__node").evaluateAll((nodes) => nodes.map((node) => node.getAttribute("style")));
    for (let index = 0; index < relationships.length; index++) {
      const scroll = await passages.nth(index).evaluate((element) => {
        window.scrollTo(0, scrollY + element.getBoundingClientRect().top - innerHeight * 0.45 + 1);
        return scrollY;
      });
      await expect(page.getByRole("button", { name: relationships[index], exact: true })).toHaveAttribute("aria-pressed", "true");
      await expect(page.locator("mark")).toHaveText((await passages.nth(index).locator("blockquote").textContent())!);
      await expect(page.locator("mark")).toBeInViewport();
      expect(await page.evaluate(() => scrollY)).toBe(scroll);
      await expect(page.locator(".react-flow__viewport")).toHaveAttribute("style", viewport!);
      expect(await page.locator(".react-flow__node").evaluateAll((nodes) => nodes.map((node) => node.getAttribute("style")))).toEqual(positions);
      if (index === 1 || index === 5) await page.screenshot({ path: testInfo.outputPath(`guided-${index}.png`) });
    }
    const spouse = page.getByRole("button", { name: relationships[1], exact: true });
    await spouse.click();
    await passages.first().scrollIntoViewIfNeeded();
    await expect(spouse).toHaveAttribute("aria-pressed", "true");
    await page.getByRole("link", { name: "Skip to interactive demonstration" }).click();
    await expect(page.locator("#interactive-demonstration")).toBeFocused();
    await expect(spouse).toHaveAttribute("aria-pressed", "true");
  } else {
    await expect(page.locator(".sample-review")).toHaveCSS("position", "static");
    await passages.first().scrollIntoViewIfNeeded();
    await page.screenshot({ path: testInfo.outputPath("sequential-story.png") });
    await passages.last().scrollIntoViewIfNeeded();
    await expect(page.getByRole("button", { name: relationships[0], exact: true })).toHaveAttribute("aria-pressed", "true");
    await page.getByRole("button", { name: relationships[5], exact: true }).click();
    await page.screenshot({ path: testInfo.outputPath("mobile-review.png") });
  }
  expect(await page.getByLabel("Source document").textContent()).toBe(source);
  await page.getByRole("link", { name: "Read passage in source" }).click();
  const scrollRegion = page.getByRole("region", { name: "Scrollable source" });
  await expect(scrollRegion).toBeFocused();
  await scrollRegion.press("Tab");
  await expect(scrollRegion).not.toBeFocused();
  // Tabbing to the closing links may reach the page bottom; leave room to test chaining.
  await page.evaluate(() => window.scrollBy(0, -300));
  await scrollRegion.evaluate((element) => { element.scrollTop = element.scrollHeight; });
  await scrollRegion.hover();
  await expect.poll(() => scrollRegion.evaluate((element) =>
    element.scrollHeight - element.clientHeight - element.scrollTop,
  )).toBeLessThanOrEqual(1);
  const scroll = await page.evaluate(() => scrollY);
  expect(await page.evaluate(() => document.documentElement.scrollHeight - innerHeight - scrollY)).toBeGreaterThan(180);
  // Chromium can consume the first wheel event at the inner scroll boundary.
  // Continued wheel input must escape to the page; a scroll trap still fails.
  await expect.poll(async () => {
    await page.mouse.wheel(0, 180);
    return page.evaluate(() => scrollY);
  }).toBeGreaterThan(scroll);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  if (testInfo.project.name === "desktop") {
    await page.setViewportSize({ width: 1200, height: 850 });
    await expect(page.locator(".sample-review")).toHaveCSS("position", "sticky");
    expect((await page.locator(".sample-review").boundingBox())!.height).toBeLessThan(850 - 48);
    await page.screenshot({ path: testInfo.outputPath("compact-desktop.png") });
  }
});

test("skip offers keyboard access to explicit sample loading before analysis exists", async ({ page }) => {
  const requests: string[] = [];
  page.on("request", (request) => { if (request.method() === "POST") requests.push(request.url()); });
  await page.goto("/");
  const skip = page.getByRole("link", { name: "Skip to interactive demonstration" });
  await skip.focus();
  await skip.press("Enter");
  await expect(page.locator("#interactive-demonstration")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Load sample analysis" })).toBeFocused();
  expect(requests).toEqual([]);
  await page.keyboard.press("Enter");
  await expect(page.getByText(/You control the review/)).toBeVisible();
  await page.locator(".sample-passage").last().scrollIntoViewIfNeeded();
  await expect(page.getByRole("button", { name: relationships[0], exact: true })).toHaveAttribute("aria-pressed", "true");
});
