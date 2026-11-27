import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { ProofTarget, RunObservation } from "../shared/contracts";
import { EvidenceComparison, RelationshipEvidence } from "./RelationshipEvidence";

const cited = {
  id: "note",
  source_id: "report",
  text: "Signed.",
  occurrences: [
    [0, 7],
    [8, 15],
  ] as [number, number][],
};
const missing = {
  source_id: "ledger",
  text: "Filed.",
  attached: false,
  occurrences: [],
};
const target: ProofTarget = {
  edge: ["Taylor", "trustee_of", "Blue Trust"],
  status: "complete",
  joint_only: true,
  alternatives: [
    {
      members: [
        missing,
        { ...cited, text: "Draft.", occurrences: [], attached: false },
      ],
    },
    {
      members: [
        { ...cited, attached: true },
        { ...cited, source_id: "seal", attached: true },
      ],
    },
  ],
};

it("starts on the complete alternative and preserves incomplete alternatives and their distinct evidence", () => {
  render(
    <EvidenceComparison
      edge={target.edge}
      target={target}
      expected={[]}
      predicted={[cited]}
      sources={[{ id: "report", title: "Report", text: "Signed. Signed." }]}
      onBack={vi.fn()}
    />,
  );
  expect(
    screen.getByRole("button", { name: /Alternative 2.*complete.*2 of 2/i }),
  ).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(
    screen.getByRole("button", { name: /Alternative 1.*incomplete/i }),
  );
  expect(
    screen.getByText("Source missing from this relationship"),
  ).toBeVisible();
  expect(screen.getByText("Quotation differs")).toBeVisible();
  const trigger = screen.getByRole("button", {
    name: /Read attached quotation from report/i,
  });
  fireEvent.click(trigger);
  const reader = screen.getByRole("region", { name: "Source reader" });
  expect(within(reader).getByText("Occurrence 1 of 2")).toBeVisible();
  fireEvent.click(
    within(reader).getByRole("button", { name: "Next occurrence" }),
  );
  expect(within(reader).getByText("Occurrence 2 of 2")).toBeVisible();
  fireEvent.click(within(reader).getByRole("button", { name: "Close reader" }));
  expect(trigger).toHaveFocus();
});

it.each([
  ["without_graph", "Prediction unavailable"],
  ["missed", "Relationship missing"],
] as const)(
  "keeps the expected proof inspectable for a %s target",
  (status, label) => {
    render(
      <EvidenceComparison
        edge={target.edge}
        target={{ ...target, status, alternatives: [{ members: [missing] }] }}
        expected={[]}
        predicted={[]}
        sources={[]}
        onBack={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("list", { name: "Members of alternative 1" }),
    ).toHaveTextContent(label);
    fireEvent.click(
      screen.getByRole("button", { name: /Read approved quotation/i }),
    );
    expect(
      screen.getByRole("region", { name: "Source reader" }),
    ).toHaveTextContent("Filed.");
    expect(
      screen.queryByText("Source missing from this relationship"),
    ).toBeNull();
  },
);

it("shows the projected best-alternative exact coverage beside the attached members", () => {
  render(
    <EvidenceComparison
      edge={target.edge}
      target={{
        ...target, status: "incomplete", best_alternative_coverage: 0.5,
        alternatives: [{ members: [{ ...cited, attached: true }, missing] }],
      }}
      expected={[]}
      predicted={[cited]}
      sources={[]}
      onBack={vi.fn()}
    />,
  );
  expect(screen.getByText("Best approved alternative exact coverage · 50.00%")).toBeVisible();
  expect(screen.getByText("Source missing from this relationship")).toBeVisible();
});

it("shows the no-formal-target state only for qualified expected relationships", () => {
  const observation = {
    id: "observed",
    relationships: [],
    benchmark: {
      role: "matched", proof_targets: [],
      expected_relationships: [{ edge: target.edge, quotes: [cited] }],
    },
  } as unknown as RunObservation;
  const { rerender } = render(<RelationshipEvidence observation={observation} edge={target.edge} onBack={vi.fn()} />);
  const status = "No formal proof target is annotated for this expected relationship.";
  expect(screen.getByText(status)).toBeVisible();
  rerender(<RelationshipEvidence observation={observation} edge={["Extra", "trustee_of", "Blue Trust"]} onBack={vi.fn()} />);
  expect(screen.queryByText(status)).not.toBeInTheDocument();
  rerender(<RelationshipEvidence observation={{
    ...observation,
    benchmark: { ...observation.benchmark!, role: "consensus" },
  }} edge={target.edge} onBack={vi.fn()} />);
  expect(screen.queryByText(status)).not.toBeInTheDocument();
});
