import { expect, test } from "@playwright/test";

for (const locale of ["en", "zh-CN"] as const) {
  test(`landing and research share navigation layout and language in ${locale}`, async ({ page }, testInfo) => {
    await page.addInitScript(value => localStorage.setItem("pcg-locale", value), locale);
    let landing: unknown;
    for (const path of ["/", "/research-results", "/research-results/"]) {
      await page.goto(path);
      const header = page.locator(".public-header");
      await expect(header).toBeVisible();
      await page.evaluate(() => document.fonts.ready);
      await expect(header.getByRole("link", { name: "Private Client Graph" })).toHaveAttribute("href", "/");
      await expect(header.locator("select")).toHaveValue(locale);
      const shape = await header.evaluate(element => {
        const box = element.getBoundingClientRect();
        const brand = element.querySelector(".public-header-brand")!;
        const select = element.querySelector("select")!;
        const styles = getComputedStyle(element);
        const selectStyles = getComputedStyle(select);
        return {
          x: box.x, width: box.width, height: box.height,
          font: styles.fontFamily, color: styles.color,
          brandSize: getComputedStyle(brand).fontSize,
          iconWidth: brand.querySelector("svg")!.getBoundingClientRect().width,
          selectBorder: selectStyles.borderWidth,
          selectPadding: selectStyles.padding,
          selectSize: selectStyles.fontSize,
        };
      });
      if (path === "/") landing = shape;
      else expect(shape).toEqual(landing);
      const current = header.locator('a[aria-current="page"]');
      await expect(current).toHaveCount(path === "/" ? 0 : 1);
      await header.locator("select").focus();
      await expect(header.locator("select")).toBeFocused();
      expect(await header.locator("select").evaluate(element => getComputedStyle(element).outlineStyle)).not.toBe("none");
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
    await page.screenshot({ path: testInfo.outputPath(`shared-header-${locale}.png`) });
  });
}

test("shared navigation remains usable at 280px", async ({ page }) => {
  await page.setViewportSize({ width: 280, height: 800 });
  await page.goto("/research-results");
  const header = page.locator(".public-header");
  await header.locator("select").selectOption("zh-CN");
  await expect(header.getByRole("link", { name: "打开实务原型" })).toBeVisible();
  expect(await header.evaluate(element => {
    const width = window.innerWidth;
    return [...element.querySelectorAll("a, select")].every(control => {
      const rect = control.getBoundingClientRect();
      return rect.left >= 0 && rect.right <= width && rect.height >= 44;
    });
  })).toBe(true);
});
