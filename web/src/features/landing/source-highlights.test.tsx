import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { sourceHighlights } from "./source-highlights";
import { SourceReview } from "./SourceReview";
import type { Evidence } from "../../shared/contracts";
const quote = (id: string, supporting_text: string): Evidence => ({
  id,
  document: "Synthetic",
  source_id: "s",
  supporting_text,
});
const source = { id: "s", title: "Source", text: "Start.\nabcde abcde\nEnd." };
const evidence = [
  quote("one", "abc"),
  quote("two", "bcd"),
  quote("three", "abc"),
];
const scrollTo = vi.fn();
let resizeSource: () => void;
let disconnectSource: ReturnType<typeof vi.fn>;
beforeEach(() => {
  disconnectSource = vi.fn();
  vi.stubGlobal(
    "ResizeObserver",
    class {
      constructor(callback: () => void) {
        resizeSource = callback;
      }
      observe = vi.fn();
      disconnect = disconnectSource;
    },
  );
  Object.defineProperty(HTMLElement.prototype, "scrollTo", {
    configurable: true,
    writable: true,
    value: vi.fn(),
  });
  vi.spyOn(HTMLElement.prototype, "scrollTo").mockImplementation(scrollTo);
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  scrollTo.mockReset();
});
describe("exact full-source Evidence", () => {
  it("preserves every character and all overlapping/repeated quote IDs without duplicate text", () => {
    const parts = sourceHighlights(source.text, evidence);
    expect(parts.map((part) => part.text).join("")).toBe(source.text);
    expect(
      parts
        .filter((part) => part.text === "bc")
        .map((part) => new Set(part.ids)),
    ).toEqual([
      new Set(["one", "two", "three"]),
      new Set(["one", "two", "three"]),
    ]);
  });
  it("handles empty or absent quotes without creating marks or dropping whitespace", () => {
    const parts = sourceHighlights(" \n\nText\t", [
      quote("empty", ""),
      quote("absent", "Other"),
    ]);
    expect(parts).toEqual([{ text: " \n\nText\t", start: 0, ids: [] }]);
  });
  it("finds overlapping occurrences of the same quote", () => {
    const parts = sourceHighlights("aaaa", [quote("pair", "aa")]);
    expect(parts.map((part) => part.text).join("")).toBe("aaaa");
    expect(parts.every((part) => part.ids.includes("pair"))).toBe(true);
  });
  it("waits for review opening, scrolls only the source, cancels on manual input and cleans up", () => {
    const pageScroll = vi.spyOn(window, "scrollTo");
    const { container, rerender, unmount } = render(
      <SourceReview
        source={source}
        evidence={evidence}
        relationship="First relationship"
        selectionVersion={0}
        reduced={false}
        active={false}
      />,
    );
    expect(scrollTo).not.toHaveBeenCalled();
    rerender(
      <SourceReview
        source={source}
        evidence={evidence}
        relationship="First relationship"
        selectionVersion={0}
        reduced={false}
        active
      />,
    );
    expect(scrollTo).toHaveBeenLastCalledWith(
      expect.objectContaining({ behavior: "smooth" }),
    );
    const pane = screen.getByRole("generic", {
      name: "Scroll full source document",
    });
    const before = document.activeElement;
    resizeSource();
    expect(scrollTo).toHaveBeenLastCalledWith(
      expect.objectContaining({ behavior: "smooth" }),
    );
    for (const type of ["wheel", "touchstart", "pointerdown"]) {
      fireEvent(pane, new Event(type));
      expect(scrollTo).toHaveBeenLastCalledWith(
        expect.objectContaining({ behavior: "instant" }),
      );
    }
    fireEvent.keyDown(pane, { key: "PageDown" });
    expect(scrollTo).toHaveBeenLastCalledWith(
      expect.objectContaining({ behavior: "instant" }),
    );
    const afterManualInput = scrollTo.mock.calls.length;
    resizeSource();
    expect(scrollTo).toHaveBeenCalledTimes(afterManualInput);
    expect(document.activeElement).toBe(before);
    expect(pageScroll).not.toHaveBeenCalled();
    expect(
      container.querySelector(".landing-story-source-text")?.textContent,
    ).toBe(source.text);
    unmount();
    expect(disconnectSource).toHaveBeenCalledOnce();
    const count = scrollTo.mock.calls.length;
    fireEvent(pane, new Event("wheel"));
    expect(scrollTo).toHaveBeenCalledTimes(count);
  });
  it("sweeps only explicitly selected Evidence and preserves exact text when motion is reduced", () => {
    const props = { source, evidence, relationship: "Relationship", active: true };
    const { container, rerender } = render(
      <SourceReview {...props} reduced={false} selectionVersion={0} />,
    );
    expect(container.querySelectorAll("mark").length).toBeGreaterThan(0);
    expect(container.querySelector("mark[data-reveal]")).toBeNull();
    rerender(<SourceReview {...props} reduced={false} selectionVersion={1} />);
    expect(container.querySelectorAll("mark[data-reveal]")).toHaveLength(
      container.querySelectorAll("mark").length,
    );
    expect(container.querySelector(".landing-story-source-text")?.textContent).toBe(source.text);
    rerender(<SourceReview {...props} reduced selectionVersion={2} />);
    expect(container.querySelector("mark[data-reveal]")).toBeNull();
    expect(container.querySelector(".landing-story-source-text")?.textContent).toBe(source.text);
    expect(container.querySelectorAll('[data-evidence-ids~="one"]').length)
      .toBeGreaterThan(0);
  });
  it("reselecting the same relationship follows its current Evidence mark on later source resize", () => {
    const props = { source, evidence, relationship: "Relationship", active: true, reduced: false };
    const { container, rerender } = render(
      <SourceReview {...props} selectionVersion={1} />,
    );
    const firstMark = container.querySelector("mark")!;
    vi.spyOn(firstMark, "getBoundingClientRect").mockReturnValue(new DOMRect(0, 100, 10, 10));
    rerender(<SourceReview {...props} selectionVersion={2} />);
    const currentMark = container.querySelector("mark")!;
    expect(currentMark).not.toBe(firstMark);
    vi.spyOn(currentMark, "getBoundingClientRect").mockReturnValue(new DOMRect(0, 400, 10, 10));
    resizeSource();
    expect(scrollTo).toHaveBeenLastCalledWith({ top: 365, behavior: "smooth" });
    expect(disconnectSource).toHaveBeenCalledOnce();
    expect(container.querySelector(".landing-story-source-text")?.textContent).toBe(source.text);
  });
  it("uses instant scrolling for reduced motion and excludes Evidence from another source", () => {
    const { container } = render(
      <SourceReview
        source={source}
        evidence={[
          ...evidence,
          { ...quote("other", "End"), source_id: "another" },
        ]}
        relationship="Relationship"
        selectionVersion={1}
        reduced
        active
      />,
    );
    expect(scrollTo).toHaveBeenLastCalledWith(
      expect.objectContaining({ behavior: "instant" }),
    );
    expect(container.querySelector('[data-evidence-ids~="other"]')).toBeNull();
    expect(screen.getByText(/Source: s/)).toHaveTextContent("one, two, three");
  });
});
