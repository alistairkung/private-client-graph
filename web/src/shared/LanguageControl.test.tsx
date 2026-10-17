import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { LanguageControl } from "./LanguageControl";
import { LocaleProvider } from "./locale";

beforeEach(() => {
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    clear: () => values.clear(),
  });
});

it("offers native language options in the compact app control without losing form state", () => {
  window.localStorage.clear();
  render(<LocaleProvider><LanguageControl compact /><input defaultValue="Review in progress" /></LocaleProvider>);
  const language = screen.getByRole("combobox", { name: "Language" });
  expect(screen.getByRole("option", { name: "English" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "简体中文" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "EN" })).not.toBeInTheDocument();
  fireEvent.change(language, { target: { value: "zh-CN" } });
  expect(language).toHaveValue("zh-CN");
  expect(screen.getByRole("textbox")).toHaveValue("Review in progress");
  expect(document.documentElement.lang).toBe("zh-CN");
  expect(window.localStorage.getItem("pcg-locale")).toBe("zh-CN");
});

it("retains the landing page's explicit language buttons by default", () => {
  window.localStorage.clear();
  render(<LocaleProvider><LanguageControl /></LocaleProvider>);
  expect(screen.getByRole("button", { name: "EN" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("button", { name: "简体中文" })).toBeInTheDocument();
  expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
});
