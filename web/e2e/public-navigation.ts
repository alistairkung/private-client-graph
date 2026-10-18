import type { Page } from "@playwright/test";

export async function openPublicMenu(page: Page) {
  const menu = page.locator(".showcase-header").getByRole("button", { name: /^(Menu|菜单)$/ });
  if (await menu.isVisible() && await menu.getAttribute("aria-expanded") === "false") await menu.click();
}

export async function selectPublicLanguage(page: Page, locale: "en" | "zh-CN") {
  await openPublicMenu(page);
  await page.locator(".showcase-header").getByRole("button", {
    name: locale === "en" ? "EN" : "简体中文", exact: true,
  }).click();
}
