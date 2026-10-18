import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { CanonicalState } from "../../shared/contracts";
import { EvidenceList } from "./EvidenceList";

const state: CanonicalState = {
  entities: [],
  sources: [{ id: "source", title: "Fictional source", text: "Exact quote." }],
  relationships: [
    {
      source: "person",
      target: "trust",
      type: "beneficiary_of",
      evidence_ids: ["first", "second", "third"],
    },
  ],
  evidence: ["first", "second", "third"].map((id) => ({
    id,
    source_id: "source",
    document: "Fictional source",
    supporting_text: "Exact quote.",
  })),
};
describe("active Evidence continuity", () => {
  it.each([
    { name: "a lower card", top: 350, height: 120, expected: 370 },
    { name: "a tall quote heading", top: 450, height: 400, expected: 550 },
    { name: "an earlier card", top: 30, height: 120, expected: 130 },
    { name: "an already visible card", top: 130, height: 120, expected: 200 },
  ])(
    "reveals $name only inside the inspector without changing focus or canonical order",
    ({ top, height, expected }) => {
      const props = {
        state,
        relationship: state.relationships[0],
        onSelect: vi.fn(),
      };
      const view = (id: string) => (
        <>
          <button>Source tab</button>
          <div className="inspector-body">
            <EvidenceList {...props} evidenceId={id} />
          </div>
        </>
      );
      const { container, rerender } = render(view("first"));
      const inspector =
        container.querySelector<HTMLElement>(".inspector-body")!;
      Object.defineProperty(inspector, "clientHeight", { value: 200 });
      inspector.scrollTop = 200;
      inspector.getBoundingClientRect = () => new DOMRect(0, 100, 400, 200);
      const cards =
        container.querySelectorAll<HTMLButtonElement>(".evidence-item");
      cards[2].getBoundingClientRect = () => new DOMRect(0, top, 400, height);
      const origin = screen.getByRole("button", { name: "Source tab" });
      origin.focus();
      fireEvent.scroll(inspector);
      rerender(view("third"));
      expect(inspector.scrollTop).toBe(expected);
      expect(origin).toHaveFocus();
      expect(window.scrollY).toBe(0);
      expect(cards[2]).toHaveAttribute("aria-pressed", "true");
      expect(
        [...cards].map(
          (card) => card.querySelector(".evidence-meta > span")?.textContent,
        ),
      ).toEqual(["first", "second", "third"]);
    },
  );
});
