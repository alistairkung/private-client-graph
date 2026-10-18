import { StrictMode } from "react";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import LandingPage from "./LandingPage";
import { canonicalSourceExcerpts } from "./landing-layout";
import { EvidenceDemo } from "./EvidenceDemo";
import type { CanonicalState } from "../shared/contracts";
import { getPublicExample, type PublicExample } from "./landing-api";
const motionState = vi.hoisted(() => ({ animate: vi.fn() }));
vi.mock("motion/react", async (original) => ({
  ...(await original<typeof import("motion/react")>()),
  animate: motionState.animate,
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

function currentClock() {
  return motionState.animate.mock.calls.at(-1)![0] as {
    set: (value: number) => void;
  };
}
function currentControls() {
  return motionState.animate.mock.results.at(-1)!.value;
}
let media: EventTarget & { matches: boolean };
let removeMediaListener: ReturnType<typeof vi.spyOn>;
function changeReducedMotion(matches: boolean) {
  act(() => {
    media.matches = matches;
    media.dispatchEvent(new Event("change"));
  });
}
beforeEach(() => {
  vi.clearAllMocks();
  media = Object.assign(new EventTarget(), { matches: false });
  removeMediaListener = vi.spyOn(media, "removeEventListener");
  vi.stubGlobal("matchMedia", () => media);
  motionState.animate.mockImplementation(() => ({
    stop: vi.fn(),
    pause: vi.fn(),
    play: vi.fn(),
    then: vi.fn(),
  }));
  vi.mocked(getPublicExample).mockResolvedValue(example);
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});
describe("two-capability synthetic showcase", () => {
  it("opens with source, reveals actual entities and canonical edges, and freezes/resumes the same clock", async () => {
    const { container } = render(<EvidenceDemo state={example.state} />);
    const region = screen.getByRole("region", {
      name: "Explore the synthetic example",
    });
    expect(region).toHaveAttribute("data-capability", "builder");
    expect(container.querySelector("mark")).toBeNull();
    expect(
      [...container.querySelectorAll(".landing-source-excerpt")].map(
        (item) => item.textContent,
      ),
    ).toEqual(canonicalSourceExcerpts(example.state, "source-one"));
    expect(container.querySelector(".landing-source-entity")).toHaveTextContent(
      "Alice",
    );
    expect(container.querySelector(".landing-entity-content")).toHaveStyle({
      opacity: "0",
    });
    expect(container.querySelector(".landing-connectors > path")).toHaveStyle({
      opacity: "0",
    });
    expect(
      screen.getByRole("button", { name: "Alice — parent of — Bob" }),
    ).toBeDisabled();
    act(() => currentClock().set(1.2));
    expect(region).toHaveAttribute("data-construction-phase", "entities");
    await waitFor(() =>
      expect(container.querySelector(".landing-entity-content")).toHaveStyle({
        opacity: "1",
      }),
    );
    expect(container.querySelector(".landing-connectors > path")).toHaveStyle({
      opacity: "0",
    });
    act(() => currentClock().set(1.9));
    await waitFor(() =>
      expect(container.querySelector(".landing-connectors > path")).toHaveStyle(
        { opacity: "1" },
      ),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Pause construction" }),
    );
    expect(currentControls().pause).toHaveBeenCalled();
    expect(region).toHaveAttribute("data-playback", "paused");
    await userEvent.click(
      screen.getByRole("button", { name: "Resume construction" }),
    );
    expect(currentControls().play).toHaveBeenCalled();
    expect(motionState.animate).toHaveBeenCalledTimes(1);
  });
  it("settles on Evidence, supports roving tabs and retains exact selection across tabs and Replay", async () => {
    const { container } = render(<EvidenceDemo state={example.state} />);
    const builder = screen.getByRole("tab", {
      name: /Build the trust structure/,
    });
    builder.focus();
    await userEvent.keyboard("{End}");
    const evidenceTab = screen.getByRole("tab", { name: /Trace the Evidence/ });
    expect(evidenceTab).toHaveFocus();
    expect(evidenceTab).toHaveAttribute("aria-selected", "true");
    expect(builder).toHaveAttribute("tabindex", "-1");
    expect(screen.getByRole("tabpanel")).toHaveAccessibleName(
      /Trace the Evidence/,
    );
    const claim = screen.getByRole("button", {
      name: "Bob — beneficiary of — Trust",
    });
    await userEvent.click(claim);
    expect(claim).toHaveFocus();
    expect(claim).toHaveAttribute("aria-pressed", "true");
    expect(container.querySelector("mark")).toHaveTextContent(
      "Bob is a beneficiary of Trust.",
    );
    expect(container.querySelector("mark")).toHaveAttribute(
      "data-evidence-id",
      "e-two",
    );
    expect(container.querySelector(".landing-paper")).toHaveAttribute(
      "data-source-id",
      "source-one",
    );
    evidenceTab.focus();
    await userEvent.keyboard("{ArrowLeft}");
    expect(builder).toHaveFocus();
    expect(screen.getByRole("region")).toHaveAttribute(
      "data-playback",
      "complete",
    );
    expect(claim).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(
      screen.getByRole("button", { name: "Replay construction" }),
    );
    expect(screen.getByRole("region")).toHaveAttribute(
      "data-construction-phase",
      "source",
    );
    expect(claim).toHaveAttribute("aria-pressed", "true");
    fireEvent.scroll(window);
    fireEvent.wheel(window);
    expect(claim).toHaveAttribute("aria-pressed", "true");
  });
  it("settles immediately on reduced motion changes and never replays timed motion under that preference", async () => {
    const { unmount } = render(<EvidenceDemo state={example.state} />);
    const controls = currentControls();
    changeReducedMotion(true);
    expect(controls.stop).toHaveBeenCalled();
    expect(screen.getByRole("region")).toHaveAttribute(
      "data-playback",
      "complete",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Replay construction" }),
    );
    expect(motionState.animate).toHaveBeenCalledTimes(1);
    changeReducedMotion(false);
    expect(screen.getByRole("region")).toHaveAttribute(
      "data-playback",
      "complete",
    );
    unmount();
    expect(removeMediaListener).toHaveBeenCalledWith(
      "change",
      expect.any(Function),
    );
  });
  it("honors the initial reduced-motion snapshot without starting a timed construction", () => {
    media.matches = true;
    render(<EvidenceDemo state={example.state} />);
    expect(motionState.animate).not.toHaveBeenCalled();
    expect(screen.getByRole("region")).toHaveAttribute(
      "data-playback",
      "complete",
    );
  });
  it("hands completion focus to Replay only when Pause or Resume owned focus", async () => {
    render(<EvidenceDemo state={example.state} />);
    const pause = screen.getByRole("button", { name: "Pause construction" });
    await userEvent.click(pause);
    await userEvent.click(
      screen.getByRole("button", { name: "Resume construction" }),
    );
    expect(pause).toHaveFocus();
    act(() => {
      currentClock().set(4);
      currentControls().then.mock.calls[0][0]();
    });
    const replay = screen.getByRole("button", { name: "Replay construction" });
    expect(replay).toHaveFocus();
    await userEvent.tab();
    expect(
      screen.getByRole("button", { name: "Alice — parent of — Bob" }),
    ).toHaveFocus();
    await userEvent.click(replay);
    const builder = screen.getByRole("tab", {
      name: "Build the trust structure",
    });
    builder.focus();
    act(() => {
      currentClock().set(4);
      currentControls().then.mock.calls[0][0]();
    });
    expect(builder).toHaveFocus();
  });
  it("resets the internal source scroll on tab and claim changes while retaining control focus", async () => {
    const { container } = render(<EvidenceDemo state={example.state} />);
    const fragment =
      container.querySelector<HTMLDivElement>(".landing-fragment")!;
    fragment.scrollTop = 240;
    const evidenceTab = screen.getByRole("tab", { name: "Trace the Evidence" });
    await userEvent.click(evidenceTab);
    expect(fragment.scrollTop).toBe(0);
    expect(evidenceTab).toHaveFocus();
    fragment.scrollTop = 80;
    const claim = screen.getByRole("button", {
      name: "Bob — beneficiary of — Trust",
    });
    await userEvent.click(claim);
    expect(fragment.scrollTop).toBe(0);
    expect(claim).toHaveFocus();
    expect(container.querySelector("mark")).toHaveTextContent(
      "Bob is a beneficiary of Trust.",
    );
  });
  it("preserves all six canonical connector dashes/arrows and scopes marker IDs to each diagram", async () => {
    const state: CanonicalState = {
      ...example.state,
      relationships: [
        ...example.state.relationships,
        ...(
          ["spouse_of", "sibling_of", "settlor_of", "trustee_of"] as const
        ).map((type) => ({
          source: "person_001",
          target: "person_003",
          type,
          evidence_ids: ["e-one"],
        })),
      ],
    };
    const { container } = render(
      <>
        <EvidenceDemo state={state} />
        <EvidenceDemo state={state} />
      </>,
    );
    await userEvent.click(
      screen.getAllByRole("tab", { name: /Trace the Evidence/ })[0],
    );
    const paths = container.querySelectorAll<SVGPathElement>(
      ".landing-demo:first-child .landing-connectors > path",
    );
    expect(paths).toHaveLength(6);
    paths.forEach((path, index) => {
      expect(path.style.strokeDasharray).toBe("");
      expect(path).not.toHaveAttribute("pathLength");
      expect(path).toHaveAttribute(
        "data-source",
        state.relationships[index].source,
      );
      expect(path).toHaveAttribute(
        "data-target",
        state.relationships[index].target,
      );
      const family = ["parent_of", "spouse_of", "sibling_of"].includes(
        state.relationships[index].type,
      );
      if (family) expect(path).toHaveAttribute("stroke-dasharray", "5 5");
      else expect(path).not.toHaveAttribute("stroke-dasharray");
    });
    const markers = container.querySelectorAll("marker");
    expect(markers[0].id).not.toBe(markers[1].id);
    expect(paths[0]).toHaveAttribute("marker-end", `url(#${markers[0].id})`);
  });
  it("auto-pauses hidden/offscreen playback, retains a manual pause, and cleans observers and stale completions", async () => {
    let observed: IntersectionObserverCallback | undefined;
    const disconnect = vi.fn();
    const observe = vi.fn();
    vi.stubGlobal(
      "IntersectionObserver",
      class {
        constructor(callback: IntersectionObserverCallback) {
          observed = callback;
        }
        observe = observe;
        disconnect = disconnect;
      },
    );
    const hidden = vi.spyOn(document, "hidden", "get").mockReturnValue(false);
    const { unmount } = render(<EvidenceDemo state={example.state} />);
    const controls = currentControls();
    expect(observe).toHaveBeenCalledWith(
      document.querySelector(".landing-drawing"),
    );
    expect(screen.getByRole("region")).toHaveAttribute(
      "data-playback",
      "paused",
    );
    act(() =>
      observed?.(
        [
          {
            isIntersecting: false,
            intersectionRatio: 0,
          } as IntersectionObserverEntry,
        ],
        {} as IntersectionObserver,
      ),
    );
    expect(controls.pause).toHaveBeenCalled();
    act(() =>
      observed?.(
        [
          {
            isIntersecting: true,
            intersectionRatio: 1,
          } as IntersectionObserverEntry,
        ],
        {} as IntersectionObserver,
      ),
    );
    expect(controls.play).toHaveBeenCalled();
    await userEvent.click(
      screen.getByRole("button", { name: "Pause construction" }),
    );
    controls.play.mockClear();
    hidden.mockReturnValue(true);
    fireEvent(document, new Event("visibilitychange"));
    hidden.mockReturnValue(false);
    fireEvent(document, new Event("visibilitychange"));
    expect(controls.play).not.toHaveBeenCalled();
    await userEvent.click(
      screen.getByRole("button", { name: "Replay construction" }),
    );
    const staleCompletion = controls.then.mock.calls[0][0];
    act(() => staleCompletion());
    expect(screen.getByRole("region")).toHaveAttribute(
      "data-playback",
      "playing",
    );
    const latestControls = currentControls();
    unmount();
    expect(disconnect).toHaveBeenCalled();
    expect(latestControls.stop).toHaveBeenCalled();
  });
  it("restarts a cleaned mount under React StrictMode", () => {
    render(
      <StrictMode>
        <EvidenceDemo state={example.state} />
      </StrictMode>,
    );
    expect(motionState.animate).toHaveBeenCalledTimes(2);
    expect(motionState.animate.mock.results[0].value.stop).toHaveBeenCalled();
    expect(currentControls().stop).not.toHaveBeenCalled();
  });
  it("offers retry after read failure and aborts outstanding reads on unmount", async () => {
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
