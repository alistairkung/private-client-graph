import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ExploratoryWorkload } from "./ExploratoryWorkload";

afterEach(() => vi.unstubAllGlobals());

it("inspects exact Source text in delivered order", async () => {
  vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: string) => url.endsWith("/reference")
    ? new Response(null, { status: 404 })
    : Response.json({
    manifest: { workload_id: "example", source_file_sha256: "test-digest" },
    sources: [
      { id: "z-last-alphabetically", title: "First in custody", text: "First original body." },
      { id: "a-first-alphabetically", title: "Second in custody", text: "Second original body." },
    ],
  })));
  render(<ExploratoryWorkload />);

  const picker = await screen.findByRole("combobox", { name: "Frozen Source" });
  expect(screen.getByText("First original body.")).toBeVisible();
  expect(screen.getAllByRole("option").map((option) => option.textContent)).toEqual([
    "1. First in custody", "2. Second in custody",
  ]);
  fireEvent.change(picker, { target: { value: "a-first-alphabetically" } });
  expect(screen.getByText("Second original body.")).toBeVisible();
  expect(screen.queryByText("First original body.")).not.toBeInTheDocument();
});

it("retries an unavailable release without inventing Source content", async () => {
  const sources = vi.fn()
    .mockResolvedValueOnce(new Response(null, { status: 409 }))
    .mockResolvedValueOnce(Response.json({
      manifest: { workload_id: "example", source_file_sha256: "test-digest" },
      sources: [{ id: "one", title: "Original", text: "Original body." }],
    }));
  vi.stubGlobal("fetch", (url: string) =>
    url.endsWith("/reference") ? Promise.resolve(new Response(null, { status: 404 })) : sources()
  );
  render(<ExploratoryWorkload />);

  expect(await screen.findByRole("alert")).toHaveTextContent("could not be loaded");
  expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Retry read" }));
  expect(await screen.findByText("Original body.")).toBeVisible();
});

it("distinguishes majority, adjudicated and disputed relationships and opens an exact Source", async () => {
  const sources = [
    { id: "d1", title: "One", text: "First body." },
    { id: "d2", title: "Two", text: "Second body." },
  ];
  vi.stubGlobal("fetch", async (url: string) => url.endsWith("/reference") ? Response.json({
    cutoff: "2030-01-01 17:00",
    reviewer_count: 10,
    majority: 6,
    relationships: [
      {
        source: "Ann", predicate: "parent_of", target: "Ben",
        counts: { support: 7, reject: 1, uncertain: 0, omitted: 2 },
        evidence_decision: "supported", evidence_reason: "Exact documentary route.",
        routes: [{ approved: true, members: [{ source_id: "d2", quote: "Second body." }] }],
      },
      {
        source: "Ann", predicate: "spouse_of", target: "Cara",
        counts: { support: 3, reject: 0, uncertain: 0, omitted: 7 },
        evidence_decision: "below_majority", evidence_reason: null, routes: [],
      },
    ],
    limitations: ["A synthetic fixture."],
    reviewer_open_questions: ["An effective-date question."],
  }) : Response.json({
    manifest: { workload_id: "fixture", source_file_sha256: "test-digest" }, sources,
  }));
  render(<ExploratoryWorkload />);
  expect(await screen.findByText("7/10 support · Evidence-adjudicated")).toBeInTheDocument();
  expect(screen.getByText("3/10 support · Below majority")).toBeInTheDocument();
  fireEvent.click(screen.getByText("Ann · parent of · Ben"));
  fireEvent.click(screen.getByText("Accepted documentary route 1"));
  fireEvent.click(screen.getByRole("button", { name: "Read Source d2" }));
  expect(screen.getByRole("combobox", { name: "Frozen Source" })).toHaveValue("d2");
  expect(screen.getByRole("heading", { name: "Two" })).toBeInTheDocument();
});
