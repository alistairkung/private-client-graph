import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReviewPage } from "./ReviewPage";
import { getReview } from "../shared/api";
import { clearSessionState } from "../shared/session-state";
import type { CanonicalState } from "../shared/contracts";

vi.mock("../shared/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../shared/api")>()),
  getReview: vi.fn(),
}));
vi.mock("./GraphDrawing", () => ({
  GraphDrawing: () => {
    const [pan, setPan] = useState(0);
    return (
      <div data-testid="retained-graph">
        <button onClick={() => setPan(pan + 1)}>Pan graph {pan}</button>
      </div>
    );
  },
}));
const state: CanonicalState = {
  sources: [
    {
      id: "source",
      title: "Fictional note",
      text: "Exact synthetic evidence. Other text.",
    },
  ],
  entities: [
    { id: "alice", name: "Alice Chen", type: "person" },
    { id: "trust", name: "Evergreen Trust", type: "trust" },
  ],
  relationships: [
    {
      source: "alice",
      target: "trust",
      type: "settlor_of",
      evidence_ids: ["first"],
    },
  ],
  evidence: [
    {
      id: "first",
      source_id: "source",
      document: "Fictional note",
      supporting_text: "Exact synthetic evidence.",
    },
  ],
};
beforeEach(() => {
  clearSessionState();
  vi.mocked(getReview).mockResolvedValue({
    id: "workspace-fixture",
    external_reference: "SYN-STATE",
    matter_title: "Fictional review",
    authoritative_source: null,
    state,
  });
});
describe("continuous review workspace", () => {
  it("retains graph local state, list query/scroll, source position and selected Evidence across view changes", async () => {
    const { container } = render(
      <ReviewPage kind="matter-proposals" id="workspace-fixture" />,
    );
    await screen.findByRole("heading", { name: "Fictional review" });
    const graph = screen.getByTestId("retained-graph");
    await userEvent.click(screen.getByRole("button", { name: "Pan graph 0" }));
    await userEvent.click(screen.getByRole("tab", { name: "List" }));
    const search = screen.getByRole("searchbox", { name: "Find relationship" });
    await userEvent.type(search, "Alice");
    const list = container.querySelector<HTMLElement>(
      ".relationship-list-scroll",
    )!;
    list.scrollTop = 144;
    fireEvent.scroll(list);
    await userEvent.click(
      container.querySelector<HTMLButtonElement>("#relationship-0")!,
    );
    const reader = container.querySelector<HTMLElement>(".source-scroll")!;
    reader.scrollTop = 211;
    fireEvent.scroll(reader);
    await userEvent.click(screen.getByRole("tab", { name: "Graph" }));
    expect(
      screen.getByRole("button", { name: "Pan graph 1" }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("retained-graph")).toBe(graph);
    await userEvent.click(screen.getByRole("tab", { name: "List" }));
    expect(
      screen.getByRole("searchbox", { name: "Find relationship" }),
    ).toHaveValue("Alice");
    expect(list.scrollTop).toBe(144);
    expect(reader.scrollTop).toBe(211);
    expect(container.querySelector("mark")).toHaveAttribute(
      "data-evidence-id",
      "first",
    );
    expect(container.querySelector("#relationship-0")).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
  it("automatically reveals the first canonical Evidence, preserves desktop focus, and navigates supporting sources by ID", async () => {
    const multi = structuredClone(state);
    multi.sources.push(
      {
        id: "second",
        title: "Fictional note",
        text: "Second supporting quote.",
      },
      {
        id: "unrelated",
        title: "Unrelated",
        text: "No supporting claim here.",
      },
    );
    multi.evidence.push(
      {
        id: "second-evidence",
        document: "Fictional note",
        source_id: "second",
        supporting_text: "Second supporting quote.",
      },
      {
        id: "later-evidence",
        document: "Fictional note",
        source_id: "second",
        supporting_text: "quote.",
      },
    );
    multi.relationships[0].evidence_ids = [
      "second-evidence",
      "first",
      "later-evidence",
    ];
    vi.mocked(getReview).mockResolvedValue({
      id: "multi",
      external_reference: "SYN-MULTI",
      title: "Multiple sources",
      authoritative_source: null,
      state: multi,
    });
    const { container } = render(<ReviewPage kind="matters" id="multi" />);
    await screen.findByRole("heading", { name: "Multiple sources" });
    await userEvent.click(screen.getByRole("tab", { name: "List" }));
    const origin =
      container.querySelector<HTMLButtonElement>("#relationship-0")!;
    await userEvent.click(origin);
    expect(origin).toHaveFocus();
    expect(container.querySelector("mark")).toHaveAttribute(
      "data-evidence-id",
      "second-evidence",
    );
    expect(container.querySelector(".source-text")).toHaveTextContent(
      "Second supporting quote.",
    );
    const tabs = container.querySelectorAll<HTMLButtonElement>(
      ".source-tabs button",
    );
    expect(tabs[1]).toHaveAttribute("aria-pressed", "true");
    expect(tabs[0]).toHaveTextContent("Supporting Evidence");
    expect(tabs[1]).toHaveTextContent("Supporting Evidence");
    expect(tabs[2]).not.toHaveTextContent("Supporting Evidence");
    await userEvent.click(tabs[0]);
    expect(container.querySelector("mark")).toHaveAttribute(
      "data-evidence-id",
      "first",
    );
    const reader = container.querySelector<HTMLElement>(".source-scroll")!;
    await userEvent.click(tabs[2]);
    expect(container.querySelector("mark")).toBeNull();
    reader.scrollTop = 135;
    fireEvent.scroll(reader);
    await userEvent.click(tabs[1]);
    expect(container.querySelector("mark")).toHaveAttribute(
      "data-evidence-id",
      "second-evidence",
    );
    await userEvent.click(tabs[2]);
    expect(reader.scrollTop).toBe(135);
    await userEvent.click(
      screen.getByRole("button", { name: "Back to relationship" }),
    );
    await vi.waitFor(() => expect(origin).toHaveFocus());
  });
  it("retains the selected canonical relationship beside Sources and returns focus without discarding list context", async () => {
    const original = window.innerWidth;
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 390,
    });
    const { container } = render(
      <ReviewPage kind="matter-proposals" id="workspace-fixture" />,
    );
    await screen.findByRole("heading", { name: "Fictional review" });
    await userEvent.click(
      container.querySelector<HTMLButtonElement>("#relationship-0")!,
    );

    expect(
      container.querySelector(".source-relationship-context"),
    ).toHaveTextContent("Alice Chen — settlor of — Evergreen Trust");
    expect(container.querySelector(".source-column")).toHaveAttribute(
      "aria-hidden",
      "false",
    );
    expect(container.querySelector("mark")).toHaveFocus();
    await userEvent.click(
      screen.getByRole("button", { name: "Back to relationship" }),
    );
    await vi.waitFor(() =>
      expect(container.querySelector("#relationship-0")).toHaveFocus(),
    );
    expect(screen.getByRole("tab", { name: "List" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: original,
    });
  });
});
