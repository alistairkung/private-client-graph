import { describe, expect, it, vi, beforeEach } from "vitest";
const mocks = vi.hoisted(() => ({ animate: vi.fn() }));
import { revealSource } from "./source-reveal";
vi.mock("motion", () => ({ animate: mocks.animate }));
let update: (value: number) => void;
const stop = vi.fn();
beforeEach(() => {
  vi.clearAllMocks();
  mocks.animate.mockImplementation(
    (
      _from: number,
      _to: number,
      options: { onUpdate: (value: number) => void },
    ) => {
      update = options.onUpdate;
      return { stop };
    },
  );
});
function fixture() {
  const reader = document.createElement("div"),
    target = document.createElement("mark");
  target.tabIndex = -1;
  reader.append(target);
  document.body.append(reader);
  Object.defineProperties(reader, {
    clientHeight: { value: 300 },
    scrollHeight: { value: 2000 },
  });
  reader.getBoundingClientRect = () => new DOMRect(0, 100, 300, 300);
  target.getBoundingClientRect = () => new DOMRect(0, 900, 200, 20);
  return { reader, target };
}
describe("interruptible source reveal", () => {
  it("animates only reader position and preserves origin focus for automatic desktop selection", () => {
    const { reader, target } = fixture();
    const cancel = revealSource(reader, target, false, false);
    expect(mocks.animate).toHaveBeenCalledWith(
      0,
      740,
      expect.objectContaining({ duration: 0.28 }),
    );
    update(240);
    expect(reader.scrollTop).toBe(240);
    expect(target).not.toHaveFocus();
    expect(window.scrollY).toBe(0);
    cancel();
    update(700);
    expect(reader.scrollTop).toBe(240);
  });
  it.each(["wheel", "touchstart", "pointerdown", "keydown"])(
    "lets %s input cancel movement",
    (type) => {
      const { reader, target } = fixture();
      const cancel = revealSource(reader, target, false, false);
      update(80);
      reader.dispatchEvent(
        type === "keydown"
          ? new KeyboardEvent(type, { key: "PageDown" })
          : new Event(type),
      );
      update(740);
      expect(reader.scrollTop).toBe(80);
      expect(stop).toHaveBeenCalled();
      cancel();
    },
  );
  it("stops an older request before a newer target and uses instant focused reveal under reduced motion", () => {
    const { reader, target } = fixture();
    const cancel = revealSource(reader, target, false, false);
    const staleUpdate = update;
    cancel();
    const latest = revealSource(reader, target, true, true);
    expect(reader.scrollTop).toBe(740);
    expect(target).toHaveFocus();
    staleUpdate(10);
    expect(reader.scrollTop).toBe(740);
    expect(mocks.animate).toHaveBeenCalledTimes(1);
    latest();
  });
});
