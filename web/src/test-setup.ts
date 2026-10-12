import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";
afterEach(() => {
  cleanup();
  window.history.replaceState(null, "", "/");
  vi.restoreAllMocks();
});
HTMLElement.prototype.scrollIntoView = vi.fn();
HTMLElement.prototype.scrollBy = vi.fn();

// jsdom lacks the native dialog API; focus isolation is tested in Playwright.
HTMLDialogElement.prototype.showModal = function () {
  this.setAttribute("open", "");
};
HTMLDialogElement.prototype.close = function () {
  this.removeAttribute("open");
};
