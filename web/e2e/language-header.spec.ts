import { openPublicMenu, selectPublicLanguage } from "./public-navigation";
import { expect, test } from "@playwright/test";

for (const path of ["/demo", "/app"]) {
  test(`language is a quiet right-aligned utility on ${path}`, async ({ page }, testInfo) => {
    await page.goto(path);
    const header = page.locator(".ledger-header-inner");
    const utilities = header.locator(".app-header-utilities");
    const language = utilities.getByRole("combobox", { name: "Language", exact: true });
    await expect(language).toHaveValue("en");
    await expect(header.getByRole("button", { name: "EN", exact: true })).toHaveCount(0);
    const bounds = await header.boundingBox();
    const utilityBounds = await utilities.boundingBox();
    expect(Math.abs(bounds!.x + bounds!.width - utilityBounds!.x - utilityBounds!.width)).toBeLessThan(2);
    const controlBounds = await language.boundingBox();
    expect(controlBounds!.height).toBeGreaterThanOrEqual(44);
    await language.focus();
    await expect(language).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(language).not.toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await expect(language).toBeFocused();
    // macOS native popup keystrokes are verified in the real browser; use the
    // native select seam for deterministic headless option selection.
    await language.selectOption("zh-CN");
    await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
    await expect(utilities.locator(".language-dropdown-display")).toHaveText("简中");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.locator("h1").click();
    await page.screenshot({ path: testInfo.outputPath(`${path.slice(1)}-header-zh-CN.png`) });
    await page.reload();
    await expect(utilities.locator("select")).toHaveValue("zh-CN");
    await utilities.locator("select").selectOption("en");
    await page.locator("h1").click();
    await page.screenshot({ path: testInfo.outputPath(`${path.slice(1)}-header-en.png`) });
  });
}

test("public language controls remain available in the header navigation", async ({ page }) => {
  await page.goto("/");
  const header = page.locator(".showcase-header");
  await openPublicMenu(page);
  await expect(header.getByRole("button", { name: "EN", exact: true })).toBeVisible();
  await expect(header.getByRole("button", { name: "简体中文", exact: true })).toBeVisible();
  await expect(header.getByRole("combobox")).toHaveCount(0);
});

for (const locale of ["en", "zh-CN"]) {
  test(`demo sign-in is a quiet footer link in ${locale}`, async ({ page }, testInfo) => {
    await page.goto("/demo/matters/hillcrest");
    await page.getByRole("combobox", { name: "Language", exact: true }).selectOption(locale);
    await expect(page.locator("header a[href='/app']")).toHaveCount(0);
    const signIn = page.locator("footer").getByRole("link", {
      name: locale === "en" ? "Practitioner sign-in" : "专业用户登录", exact: true,
    });
    await signIn.scrollIntoViewIfNeeded();
    await expect(signIn).toBeVisible();
    await expect(signIn).toHaveAttribute("href", "/app");
    await page.screenshot({ path: testInfo.outputPath(`demo-footer-${locale}.png`) });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}

for (const path of ["/", "/research-results"]) {
  test(`public navigation collapses to a keyboard-operable dropdown on ${path}`, async ({ page }, testInfo) => {
    await page.goto(path);
    await page.evaluate(() => document.fonts.ready);
    const header = page.locator(".showcase-header");
    const navigation = header.getByRole("navigation");
    const menu = header.getByRole("button", { name: "Menu", exact: true });
    for (const width of [1024, 640, 390, 320]) {
      await page.setViewportSize({ width, height: 900 });
      await expect(menu).toBeVisible();
      const brand = header.getByRole("link", { name: "Private Client Graph", exact: true });
      const brandBox = (await brand.boundingBox())!;
      const menuBox = (await menu.boundingBox())!;
      expect(Math.abs(brandBox.y + brandBox.height / 2 - menuBox.y - menuBox.height / 2)).toBeLessThan(2);
      expect(brandBox.x + brandBox.width).toBeLessThanOrEqual(menuBox.x);
      expect((await header.boundingBox())!.height).toBeLessThanOrEqual(90);
      const iconSize = await menu.locator("svg").evaluate(element => element.getBoundingClientRect().width);
      const labelSize = await menu.evaluate(element => parseFloat(getComputedStyle(element).fontSize));
      expect(iconSize / labelSize).toBeCloseTo(1.4, 1);
      await expect(navigation).toBeHidden();
      await expect(header.getByRole("button", { name: "EN", exact: true })).toBeHidden();
      await page.screenshot({ path: testInfo.outputPath(`public-header-en-${width}.png`) });
      await menu.click();
      await expect(menu).toHaveAttribute("aria-expanded", "true");
      await expect(navigation.getByRole("link")).toHaveCount(4);
      for (const link of await navigation.getByRole("link").all()) await expect(link).toBeVisible();
      expect(await navigation.getByRole("link").first().evaluate(element => getComputedStyle(element).fontSize)).toBe(`${labelSize}px`);
      expect(await header.getByRole("button", { name: "EN", exact: true }).evaluate(element => getComputedStyle(element).fontSize)).toBe(`${labelSize}px`);
      await page.keyboard.press("Tab");
      await expect(navigation.getByRole("link").first()).toBeFocused();
      await page.keyboard.press("Escape");
      await expect(menu).toBeFocused();
      await expect(navigation).toBeHidden();
      await menu.click();
      await page.screenshot({ path: testInfo.outputPath(`public-menu-en-${width}.png`) });
      await header.getByRole("button", { name: "简体中文", exact: true }).click();
      await expect(navigation).toBeHidden();
      const chineseMenu = header.getByRole("button", { name: "菜单", exact: true });
      await page.screenshot({ path: testInfo.outputPath(`public-header-zh-CN-${width}.png`) });
      await chineseMenu.click();
      await expect(navigation.getByRole("link", { name: "研究结果", exact: true })).toBeVisible();
      await page.screenshot({ path: testInfo.outputPath(`public-menu-zh-CN-${width}.png`) });
      await page.mouse.click(4, 300);
      await expect(navigation).toBeHidden();
      await selectPublicLanguage(page, "en");
    }
    await page.setViewportSize({ width: 1440, height: 1100 });
    await expect(menu).toBeHidden();
    await expect(navigation.getByRole("link", { name: "Research results", exact: true })).toBeVisible();
    await page.setViewportSize({ width: 884, height: 900 });
    await menu.click();
    await navigation.getByRole("link", { name: "The approach", exact: true }).click();
    await expect(page).toHaveURL(/\/#approach$/);
    await expect(page.locator("#approach")).toBeInViewport();
    await expect(page.locator(".showcase-header nav")).toBeHidden();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}
