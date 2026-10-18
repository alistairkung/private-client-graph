import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
const motionState = vi.hoisted(() => ({
  reduced: false,
  deferred: false,
  update: (_value: number) => {},
}));
vi.mock("motion/react", async (original) => ({
  ...(await original<typeof import("motion/react")>()),
  useReducedMotion: () => motionState.reduced,
}));
vi.mock("motion", () => ({
  animate: (
    _from: number,
    to: number,
    options: { onUpdate: (value: number) => void },
  ) => {
    motionState.update = options.onUpdate;
    if (!motionState.deferred) options.onUpdate(to);
    return { stop: vi.fn() };
  },
}));
beforeEach(() => {
  motionState.reduced = false;
  motionState.deferred = false;
});

import { SourceReader } from "./SourceReader";
import { LocaleProvider } from "../shared/locale";

const sources = [
  {
    id: "one",
    title: "Same title",
    text: "First exact quote. First exact quote.",
  },
  { id: "two", title: "Same title", text: "Second exact quote." },
];
describe("exact source-aware Evidence reading", () => {
  it("preserves source scroll on selection and moves only the source container for an explicit Evidence action", () => {
    const item = {
      id: "first",
      source_id: "one",
      document: "Same title",
      supporting_text: "First exact quote.",
    };
    const props = {
      sources,
      sourceId: "one",
      onSource: vi.fn(),
      onReturn: vi.fn(),
      memoryKey: "source-scroll-regression",
    };
    const { container, rerender } = render(
      <SourceReader {...props} evidence={item} />,
    );
    const reader = container.querySelector<HTMLElement>(".source-scroll")!;
    reader.scrollTop = 275;
    fireEvent.scroll(reader);
    rerender(<SourceReader {...props} evidence={{ ...item, id: "second" }} />);
    expect(reader.scrollTop).toBe(275);
    const target = container.querySelector<HTMLElement>("mark")!;
    vi.spyOn(reader, "getBoundingClientRect").mockReturnValue(
      new DOMRect(0, 100, 300, 300),
    );
    vi.spyOn(target, "getBoundingClientRect").mockReturnValue(
      new DOMRect(0, 620, 200, 20),
    );
    Object.defineProperty(reader, "scrollHeight", {
      configurable: true,
      value: 2000,
    });
    Object.defineProperty(reader, "clientHeight", {
      configurable: true,
      value: 300,
    });
    rerender(
      <SourceReader
        {...props}
        evidence={{ ...item, id: "second" }}
        jumpRequest={1}
      />,
    );
    expect(reader.scrollTop).toBe(735);
    expect(target).toHaveFocus();
    expect(window.scrollY).toBe(0);
    rerender(
      <SourceReader
        {...props}
        sourceId="two"
        evidence={{ ...item, id: "second" }}
        jumpRequest={1}
      />,
    );
    expect(reader.scrollTop).toBe(0);
    reader.scrollTop = 123;
    fireEvent.scroll(reader);
    rerender(
      <SourceReader
        {...props}
        evidence={{ ...item, id: "second" }}
        jumpRequest={1}
      />,
    );
    expect(reader.scrollTop).toBe(735);
  });
  it.each([false, true])(
    "settles an ongoing reveal when reduced motion changes, unless the reader has taken control (%s)",
    (interrupted) => {
      motionState.deferred = true;
      const props = {
        sources,
        sourceId: "one",
        evidence: {
          id: "e",
          document: "",
          source_id: "one",
          supporting_text: "First exact quote.",
        },
        onSource: vi.fn(),
        onReturn: vi.fn(),
        focusOnReveal: false,
        memoryKey: "reduce-transition-" + interrupted,
      };
      const { container, rerender } = render(<SourceReader {...props} />);
      const reader = container.querySelector<HTMLElement>(".source-scroll")!;
      const mark = container.querySelector<HTMLElement>("mark")!;
      Object.defineProperties(reader, {
        clientHeight: { value: 300 },
        scrollHeight: { value: 2000 },
      });
      reader.getBoundingClientRect = () => new DOMRect(0, 100, 300, 300);
      mark.getBoundingClientRect = () =>
        new DOMRect(0, 900 - reader.scrollTop, 200, 20);
      rerender(<SourceReader {...props} jumpRequest={1} />);
      motionState.update(200);
      if (interrupted) fireEvent.wheel(reader);
      motionState.reduced = true;
      rerender(<SourceReader {...props} jumpRequest={1} />);
      expect(reader.scrollTop).toBe(interrupted ? 200 : 740);
      motionState.update(300);
      expect(reader.scrollTop).toBe(interrupted ? 200 : 740);
    },
  );
  it("highlights one exact occurrence in the selected source, retaining the backend Evidence ID", () => {
    const { container, rerender } = render(
      <LocaleProvider>
        <SourceReader
          sources={sources}
          sourceId="one"
          evidence={{
            id: "e-one",
            document: "Same title",
            source_id: "one",
            supporting_text: "First exact quote.",
          }}
          onSource={vi.fn()}
          onReturn={vi.fn()}
        />
      </LocaleProvider>,
    );
    expect(container.querySelectorAll("mark")).toHaveLength(1);
    expect(container.querySelector("mark")).toHaveTextContent(
      "First exact quote.",
    );
    expect(container.querySelector("mark")).toHaveAttribute(
      "data-evidence-id",
      "e-one",
    );
    expect(container.querySelector(".source-text")?.textContent).toBe(
      sources[0].text,
    );
    rerender(
      <LocaleProvider>
        <SourceReader
          sources={sources}
          sourceId="two"
          evidence={{
            id: "e-two",
            document: "Same title",
            source_id: "two",
            supporting_text: "Second exact quote.",
          }}
          onSource={vi.fn()}
          onReturn={vi.fn()}
        />
      </LocaleProvider>,
    );
    expect(container.querySelector("mark")).toHaveAttribute(
      "data-evidence-id",
      "e-two",
    );
    expect(container.querySelector(".source-text")?.textContent).toBe(
      sources[1].text,
    );
  });
  it("never highlights an approximate match or Evidence in the wrong source", () => {
    const { container, rerender } = render(
      <SourceReader
        sources={sources}
        sourceId="one"
        evidence={{
          id: "missing",
          document: "",
          source_id: "one",
          supporting_text: "first exact quote.",
        }}
        onSource={vi.fn()}
        onReturn={vi.fn()}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "The exact Evidence text could not be located",
    );
    expect(container.querySelector("mark")).toBeNull();
    rerender(
      <SourceReader
        sources={sources}
        sourceId="two"
        evidence={{
          id: "other",
          document: "",
          source_id: "one",
          supporting_text: "First exact quote.",
        }}
        onSource={vi.fn()}
        onReturn={vi.fn()}
      />,
    );
    expect(container.querySelector("mark")).toBeNull();
  });
  it("marks supporting sources by canonical ID even when titles match and provides return action", async () => {
    const onSource = vi.fn(),
      onReturn = vi.fn();
    render(
      <SourceReader
        sources={sources}
        sourceId="one"
        evidence={{
          id: "e",
          document: "",
          source_id: "one",
          supporting_text: "First exact quote.",
        }}
        onSource={onSource}
        supportingEvidence={[
          {
            id: "e",
            document: "",
            source_id: "two",
            supporting_text: "Second exact quote.",
          },
        ]}
        onReturn={onReturn}
      />,
    );
    await userEvent.click(
      screen.getAllByRole("button", { name: /Same title/ })[1],
    );
    expect(onSource).toHaveBeenCalledWith("two");
    const supportSlots = document.querySelectorAll(".source-support");
    expect(supportSlots).toHaveLength(sources.length);
    expect(supportSlots[0]).toBeEmptyDOMElement();
    expect(supportSlots[1]).toHaveTextContent("Supporting Evidence");
    expect(
      screen.getAllByRole("button", { name: /Same title/ })[1],
    ).toHaveTextContent("Supporting Evidence");
    expect(
      screen.getAllByRole("button", { name: /Same title/ })[0],
    ).not.toHaveTextContent("Supporting Evidence");
    await userEvent.click(
      screen.getByRole("button", { name: "Back to relationship" }),
    );
    expect(onReturn).toHaveBeenCalledOnce();
  });
});
