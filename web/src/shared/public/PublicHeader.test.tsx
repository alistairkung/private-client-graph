import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { LocaleProvider } from "../locale";
import { PublicHeader } from "./PublicHeader";

afterEach(() => vi.unstubAllGlobals());

test("shared public navigation identifies the research page and links to the landing and prototype", () => {
  render(<PublicHeader currentPage="research" />);
  expect(screen.getByRole("link", { name: "Private Client Graph" })).toHaveAttribute("href", "/");
  expect(screen.getByRole("link", { name: "Open practitioner prototype" })).toHaveAttribute("href", "/app");
  expect(screen.getByRole("link", { name: "Research" })).toHaveAttribute("href", "/research-results");
  expect(screen.getByRole("link", { name: "Research" })).toHaveAttribute("aria-current", "page");
});

test("language selection translates shared navigation and persists the preference without moving focus", () => {
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
  });
  render(<LocaleProvider><PublicHeader /></LocaleProvider>);
  const language = screen.getByRole("combobox", { name: "Language" });
  language.focus();
  fireEvent.change(language, { target: { value: "zh-CN" } });
  expect(screen.getByRole("navigation", { name: "主导航" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "打开实务原型" })).toHaveAttribute("href", "/app");
  expect(screen.getByRole("link", { name: "研究" })).not.toHaveAttribute("aria-current");
  expect(screen.getByRole("combobox", { name: "语言" })).toHaveFocus();
  expect(values.get("pcg-locale")).toBe("zh-CN");
});
