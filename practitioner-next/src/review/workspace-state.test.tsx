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
    const quote = container.querySelector<HTMLButtonElement>(".evidence-item")!;
    await userEvent.click(quote);
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
