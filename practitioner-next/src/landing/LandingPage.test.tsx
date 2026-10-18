import { useRef } from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import LandingPage from "./LandingPage";
import { EvidenceDemo } from "./EvidenceDemo";
import type { CanonicalState } from "../shared/contracts";
import { getPublicExample, type PublicExample } from "./landing-api";
const motionState = vi.hoisted(() => ({
  reduced: false,
  animate: vi.fn(),
  stop: vi.fn(),
}));
vi.mock("motion/react", async (original) => ({
  ...(await original<typeof import("motion/react")>()),
  useReducedMotion: () => motionState.reduced,
  useAnimate: () => [useRef<HTMLDivElement>(null), motionState.animate],
}));
vi.mock("./landing-api", async (original) => ({
  ...(await original<typeof import("./landing-api")>()),
  getPublicExample: vi.fn(),
}));
const example: PublicExample = {
  id: "case-01",
  title: "Synthetic example",
  notice: "Synthetic",
  result_kind: "curated_ideal_fixture",
  state: {
    entities: [
      { id: "person_001", type: "person", name: "Alice" },
      { id: "person_003", type: "person", name: "Bob" },
      { id: "trust_001", type: "trust", name: "Trust" },
    ],
    relationships: [
      {
        source: "person_001",
        target: "person_003",
        type: "parent_of",
        evidence_ids: ["e-one"],
      },
      {
        source: "person_003",
        target: "trust_001",
        type: "beneficiary_of",
        evidence_ids: ["e-two"],
      },
    ],
    evidence: [
      {
        id: "e-one",
        document: "Fictional note",
        source_id: "source-one",
        supporting_text: "Alice is Bob’s parent.",
      },
      {
        id: "e-two",
        document: "Fictional note",
        source_id: "source-one",
        supporting_text: "Bob is a beneficiary of Trust.",
      },
    ],
    sources: [
      {
        id: "source-one",
        title: "Fictional note",
        text: "Alice is Bob’s parent. Bob is a beneficiary of Trust.",
      },
    ],
  },
};
beforeEach(() => {
  vi.clearAllMocks();
  motionState.reduced = false;
  motionState.animate.mockReturnValue({
    stop: motionState.stop,
    then: vi.fn(),
  });
  vi.mocked(getPublicExample).mockResolvedValue(example);
});
afterEach(() => vi.unstubAllGlobals());
describe("landing Evidence thread", () => {
  it("lets early keyboard input finish intro and atomically selects canonical Evidence without losing focus or being overwritten by scroll", async () => {
    const { container } = render(<LandingPage />);
    const region = await screen.findByRole("region", {
      name: "Explore the synthetic example",
    });
    const claim = within(region).getByRole("button", {
      name: "Bob — beneficiary of — Trust",
    });
    claim.focus();
    await userEvent.keyboard("{Enter}");
    expect(claim).toHaveFocus();
    expect(claim).toHaveAttribute("aria-pressed", "true");
    expect(container.querySelector("mark")).toHaveTextContent(
      "Bob is a beneficiary of Trust.",
    );
    expect(container.querySelector("mark")).toHaveAttribute(
      "data-evidence-id",
      "e-two",
    );
    expect(region).toHaveTextContent("source-one");
    expect(region).toHaveTextContent("e-two");
    expect(motionState.stop).toHaveBeenCalled();
    expect(motionState.animate).toHaveBeenLastCalledWith(
      expect.arrayContaining([
        [
          ".landing-entity-content",
          { y: 0, opacity: 1 },
          { at: 0, duration: 0 },
        ],
      ]),
    );
    fireEvent.scroll(window);
    fireEvent.wheel(window);
    expect(claim).toHaveAttribute("aria-pressed", "true");
  });
  it("settles all intro values if reduced motion becomes enabled during the intro", async () => {
    const { rerender } = render(<LandingPage />);
    await screen.findByRole("region", {
      name: "Explore the synthetic example",
    });
    motionState.reduced = true;
    rerender(<LandingPage />);
    expect(motionState.stop).toHaveBeenCalled();
    expect(motionState.animate).toHaveBeenLastCalledWith(
      expect.arrayContaining([
        [".landing-paper", { y: 0, opacity: 1 }, { duration: 0 }],
      ]),
    );
  });
  it("preserves all six static connector patterns and arrows after early input and reduced-motion interruption", async () => {
    const state: CanonicalState = {
      ...example.state,
      relationships: [
        {
          source: "person_001",
          target: "person_003",
          type: "parent_of",
          evidence_ids: ["e-one"],
        },
        {
          source: "person_001",
          target: "person_003",
          type: "spouse_of",
          evidence_ids: ["e-one"],
        },
        {
          source: "person_001",
          target: "person_003",
          type: "sibling_of",
          evidence_ids: ["e-one"],
        },
        {
          source: "person_001",
          target: "trust_001",
          type: "settlor_of",
          evidence_ids: ["e-one"],
        },
        {
          source: "person_001",
          target: "trust_001",
          type: "trustee_of",
          evidence_ids: ["e-one"],
        },
        {
          source: "person_003",
          target: "trust_001",
          type: "beneficiary_of",
          evidence_ids: ["e-two"],
        },
      ],
    };
    const { container, rerender } = render(<EvidenceDemo state={state} />);
    expect(container.querySelector(".landing-intro-path")).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Alice — spouse of — Bob" }),
    );
    expect(container.querySelector(".landing-intro-path")).toBeNull();
    motionState.reduced = true;
    rerender(<EvidenceDemo state={state} />);
    const basePaths = container.querySelectorAll<SVGPathElement>(
      ".landing-connectors > path",
    );
    expect(basePaths).toHaveLength(6);
    basePaths.forEach((path, index) => {
      expect(path.style.strokeDasharray).toBe("");
      expect(path).not.toHaveAttribute("pathLength");
      expect(path).toHaveAttribute(
        "data-source",
        state.relationships[index].source,
      );
      if (index < 3) expect(path).toHaveAttribute("stroke-dasharray", "5 5");
      else expect(path).not.toHaveAttribute("stroke-dasharray");
    });
    expect(basePaths[0]).toHaveAttribute(
      "marker-end",
      "url(#landing-parent-arrow)",
    );
    const animatedSelectors = motionState.animate.mock.calls.flatMap((call) =>
      call[0].map((segment: unknown[]) => segment[0]),
    );
    expect(animatedSelectors).not.toContain(".landing-connectors > path");
    expect(animatedSelectors).not.toContain(".landing-selected-line");
  });
  it("offers a working retry after an honest read failure and aborts outstanding reads on unmount", async () => {
    vi.mocked(getPublicExample).mockRejectedValueOnce(
      new Error("private diagnostics"),
    );
    const { unmount } = render(<LandingPage />);
    expect(await screen.findByRole("alert")).not.toHaveTextContent(
      "private diagnostics",
    );
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByRole("region", {
      name: "Explore the synthetic example",
    });
    const signal = vi.mocked(getPublicExample).mock.calls.at(-1)![0];
    unmount();
    expect(signal.aborted).toBe(true);
  });
});
