import type { Page } from "@playwright/test";

export async function selectPublicLanguage(page: Page, locale: "en" | "zh-CN") {
  await page.locator(".public-header select").selectOption(locale);
}
