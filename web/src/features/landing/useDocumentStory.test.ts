import { afterEach, describe, expect, it, vi } from "vitest";
import { measureDocumentOrigins } from "./useDocumentStory";
afterEach(() => vi.unstubAllGlobals());
describe("cached document-to-graph coordinates", () => {
  it("uses the first exact name fragment and removes the graph's current translation", () => {
    const note = document.createElement("article");
    note.innerHTML = '<span data-source-entity-id="alice">Alice</span>';
    const drawing = document.createElement("div");
    drawing.innerHTML =
      '<div data-entity-id="alice"></div><div data-entity-id="unmentioned"></div>';
    const holder = document.createElement("div");
    Object.defineProperty(holder, "offsetWidth", { value: 500 });
    vi.stubGlobal(
      "DOMMatrix",
      class {
        m41 = 60;
      },
    );
    vi.spyOn(note.firstElementChild!, "getClientRects").mockReturnValue([
      { left: 100, top: 120, width: 40, height: 20 },
    ] as unknown as DOMRectList);
    vi.spyOn(
      drawing.firstElementChild!,
      "getBoundingClientRect",
    ).mockReturnValue({ left: 300, top: 90 } as DOMRect);
    expect(
      measureDocumentOrigins(note, drawing, holder, false).get("alice"),
    ).toEqual([-350, 8]);
    expect(
      measureDocumentOrigins(note, drawing, holder, true).get("alice"),
    ).toEqual([-120, 8]);
    expect(
      measureDocumentOrigins(note, drawing, holder, false).has("unmentioned"),
    ).toBe(false);
  });
});
