import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { RunDetail } from "../shared/contracts";
import { ObservationInspection } from "./ObservationInspection";

vi.mock("../../src/features/review/GraphDrawing", () => ({
  GraphDrawing: () => <div role="img" aria-label="Graph" />,
}));

it("keeps observations collapsed until explicitly expanded", () => {
  render(
    <ObservationInspection
      run={{ observations: [] } as unknown as RunDetail}
    />,
  );
  const summary = screen.getByText("Observations & Evidence");
  const observation = screen.getByLabelText("Observation");
  expect(observation).not.toBeVisible();
  fireEvent.click(summary);
  expect(observation).toBeVisible();
  fireEvent.click(summary);
  expect(observation).not.toBeVisible();
});

it("shows a rejected Source association alongside a perfect quotation score", () => {
  const result = {
    evaluation: { precision: 1, recall: 1, f1: 1, provenance_accuracy: 1 },
    source_attribution: {
      assessed: 1,
      passed: 0,
      failures: [
        {
          edge: ["Jo", "trustee_of", "Elm"],
          evidence_id: "e1",
          source_id: "draft",
          supporting_text: "Jo is trustee of Elm.",
        },
      ],
    },
  };
  render(
    <ObservationInspection
      run={
        {
          observations: [
            { id: "one", case_id: "test", result, relationships: [] },
          ],
        } as unknown as RunDetail
      }
    />,
  );
  fireEvent.click(screen.getByText("Observations & Evidence"));
  expect(
    screen.getByText(/Approved Source.quote associations/),
  ).toHaveTextContent("0 / 1");
  expect(
    screen.getByRole("list", { name: "Unapproved Source/quote associations" }),
  ).toHaveTextContent("Jo · trustee_of · Elm — draft: Jo is trustee of Elm.");
});

it("shows every proof alternative and distinguishes a missing Source from a quotation mismatch", () => {
  const expected = {
    sources: [],
    entities: [],
    relationships: [],
    evidence: [],
  };
  render(
    <ObservationInspection
      run={
        {
          observations: [
            {
              id: "condition",
              case_id: "case",
              status: "completed",
              source: "A correct quotation.",
              sources: [{ id: "present", text: "An unrelated quote." }],
              relationships: [],
              result: {
                state: {
                  sources: [{ id: "present", text: "An unrelated quote." }],
                  entities: [
                    { id: "a", name: "A", type: "person" },
                    { id: "b", name: "B", type: "person" },
                  ],
                  relationships: [
                    {
                      source: "a",
                      type: "parent_of",
                      target: "b",
                      evidence_ids: ["e1"],
                    },
                  ],
                  evidence: [
                    {
                      id: "e1",
                      document: "present",
                      source_id: "present",
                      supporting_text: "An unrelated quote.",
                    },
                  ],
                },
              },
              benchmark: {
                family: "Family A",
                condition: "natural",
                role: "natural",
                contrast: "matched contrast",
                outcome: "valid_graph",
                expected,
                expected_edges: 1,
                expected_relationships: [],
                graph: null,
                failure_detail: null,
                metrics: {
                  tp: 0,
                  fp: 0,
                  fn: 1,
                  planned_proofs: 1,
                  complete_proofs: 0,
                  planned_joint_proofs: 1,
                  complete_joint_proofs: 0,
                  incomplete_proofs: 0,
                  missed_proofs: 0,
                  quote_passed: 0,
                  quote_assessed: 0,
                  attribution_passed: 0,
                  attribution_assessed: 0,
                },
                proof_targets: [
                  {
                    edge: ["A", "parent_of", "B"],
                    joint_only: true,
                    status: "without_graph",
                    alternatives: [
                      {
                        members: [
                          {
                            source_id: "present",
                            text: "A different quotation.",
                            attached: false,
                            occurrences: [],
                          },
                          {
                            source_id: "absent",
                            text: "Missing Source quotation.",
                            attached: false,
                            occurrences: [],
                          },
                        ],
                      },
                      {
                        members: [
                          {
                            source_id: "present",
                            text: "A correct quotation.",
                            attached: true,
                            occurrences: [],
                          },
                        ],
                      },
                    ],
                  },
                ],
              },
            },
          ],
        } as unknown as RunDetail
      }
    />,
  );
  fireEvent.click(screen.getByText("Observations & Evidence"));
  expect(
    screen.getByText(/natural · natural · matched contrast/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("list", { name: "Proof outcomes" }),
  ).toHaveTextContent("without graph");
  expect(
    screen.getByText(/Wrong quotation on this relationship/),
  ).toBeInTheDocument();
  expect(screen.getByText(/Source missing/)).toBeInTheDocument();
  expect(screen.getByText(/Alternative 2/)).toBeInTheDocument();
  expect(screen.getByText(/Attached to this relationship/)).toBeInTheDocument();
});
