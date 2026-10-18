import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
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
  it("chooses sources by ID even when titles match and provides return action", async () => {
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
        onReturn={onReturn}
      />,
    );
    await userEvent.click(
      screen.getAllByRole("button", { name: /Same title/ })[1],
    );
    expect(onSource).toHaveBeenCalledWith("two");
    await userEvent.click(
      screen.getByRole("button", { name: "Back to relationship" }),
    );
    expect(onReturn).toHaveBeenCalledOnce();
  });
});
