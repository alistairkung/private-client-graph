import { LocaleProvider } from "../../shared/locale";
import { StrictMode } from "react";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { motionValue } from "motion/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import LandingPage from "./LandingPage";
import { DocumentStory } from "./DocumentStory";
import { getPublicExample, type PublicExample } from "./landing-api";
vi.mock("./landing-api", async (original) => ({
  ...(await original<typeof import("./landing-api")>()),
  getPublicExample: vi.fn(),
}));
vi.mock("motion/react", async (original) => ({
  ...(await original<typeof import("motion/react")>()),
  useScroll: vi.fn(),
  useInView: () => true,
}));
import { useScroll } from "motion/react";
const example: PublicExample = {
  id: "case-01",
  title: "Synthetic example",
  notice: "Synthetic",
  result_kind: "curated_ideal_fixture",
  state: {
    entities: [
      { id: "alice", name: "Alice", type: "person" },
      { id: "bob", name: "Bob", type: "person" },
      { id: "trust", name: "Trust", type: "trust" },
    ],
    relationships: [
      {
        source: "alice",
        type: "parent_of",
        target: "bob",
        evidence_ids: ["one"],
      },
      {
        source: "bob",
        type: "beneficiary_of",
        target: "trust",
        evidence_ids: ["two", "three"],
      },
    ],
    evidence: [
      {
        id: "one",
        document: "Note",
        source_id: "source",
        supporting_text: "Alice is Bob’s parent.",
      },
      {
        id: "two",
        document: "Note",
        source_id: "source",
        supporting_text: "Bob is a beneficiary of Trust.",
      },
      {
        id: "three",
        document: "Note",
        source_id: "source",
        supporting_text: "Bob is a beneficiary of Trust.",
      },
    ],
    sources: [
      {
        id: "source",
        title: "Synthetic note",
        text: "Introduction.\n\nAlice is Bob’s parent.\nBob is a beneficiary of Trust.\nClosing.",
      },
    ],
  },
};
let progress = motionValue(0);
let media: EventTarget & { matches: boolean };
let observers: {
  observe: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
}[];
const scrollTo = vi.fn();
beforeEach(() => {
  vi.clearAllMocks();
  const preferences = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => preferences.get(key) ?? null,
    setItem: (key: string, value: string) => preferences.set(key, value),
  });
  progress = motionValue(0);
  vi.mocked(useScroll).mockReturnValue({
    scrollYProgress: progress,
    scrollXProgress: motionValue(0),
    scrollX: motionValue(0),
    scrollY: motionValue(0),
  });
  media = Object.assign(new EventTarget(), { matches: false });
  vi.stubGlobal("matchMedia", () => media);
  observers = [];
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe = vi.fn();
      disconnect = vi.fn();
      constructor() {
        observers.push(this);
      }
    },
  );
  vi.stubGlobal(
    "DOMMatrix",
    class {
      m41 = 0;
    },
  );
  vi.stubGlobal("scrollTo", scrollTo);
  Object.defineProperty(HTMLElement.prototype, "scrollTo", {
    configurable: true,
    writable: true,
    value: vi.fn(),
  });
  Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
    configurable: true,
    writable: true,
    value: vi.fn(),
  });
  vi.spyOn(HTMLElement.prototype, "scrollTo").mockImplementation(scrollTo);
  vi.spyOn(HTMLElement.prototype, "scrollIntoView").mockImplementation(
    () => {},
  );
  vi.mocked(getPublicExample).mockResolvedValue(example);
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});
function reduced(matches: boolean) {
  act(() => {
    media.matches = matches;
    media.dispatchEvent(new Event("change"));
  });
}
function setProgress(value: number) {
  act(() => progress.set(value));
}

describe("document-to-review landing", () => {
  it("starts with four illustrative formats, the exact source excerpts, and no playback controls", () => {
    const { container } = render(<DocumentStory state={example.state} />);
    expect(
      screen.getByRole("heading", { name: "It begins with your documents" }),
    ).toBeVisible();
    expect(
      [...container.querySelectorAll("[data-document-kind]")].map((item) =>
        item.getAttribute("data-document-kind"),
      ),
    ).toEqual(["attendance", "email", "timesheet", "legal"]);
    expect(
      container.querySelector(".landing-story-document-attendance"),
    ).toHaveTextContent("Alice is Bob’s parent.");
    expect(screen.queryByRole("tab")).toBeNull();
    expect(
      screen.queryByRole("button", { name: /Replay|Pause|Resume/ }),
    ).toBeNull();
    expect(container.querySelector("#landing-story-review")).toHaveAttribute(
      "inert",
    );
    expect(
      container.querySelector(".landing-story-source-text")?.textContent,
    ).toBe(example.state.sources[0].text);
  });
  it("holds the completed review before inviting exploration and preserves an explicit relationship when scrolling backwards", async () => {
    const { container } = render(<DocumentStory state={example.state} />);
    setProgress(0.7);
    expect(container.querySelector("[data-inviting]")).toBeNull();
    expect(container.querySelector(".landing-story-invitation-trace")).toBeNull();
    expect(container.querySelector("#landing-story-review")).toHaveAttribute(
      "inert",
    );
    setProgress(0.78);
    expect(container.querySelector("#landing-story-review")).not.toHaveAttribute("inert");
    expect(container.querySelector("[data-inviting]")).toBeNull();
    setProgress(0.82);
    const claim = screen.getByRole("button", {
      name: "Bob — beneficiary of — Trust",
    });
    expect(claim).toHaveAttribute("data-inviting", "true");
    expect(claim).not.toHaveAttribute("aria-describedby");
    expect(screen.queryByText("Try this relationship")).not.toBeInTheDocument();
    expect(claim).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Alice — parent of — Bob" }))
      .toHaveAttribute("aria-pressed", "true");
    expect(container.querySelector("mark")).toHaveTextContent("Alice is Bob’s parent.");
    expect(container.querySelector("mark")).not.toHaveAttribute("data-reveal");
    await userEvent.click(claim);
    expect(container.querySelector(".landing-story-invitation-trace")).toBeNull();
    expect(claim).not.toHaveAttribute("data-inviting");
    expect(claim).toHaveAttribute("aria-pressed", "true");
    expect(container.querySelector("mark")).toHaveAttribute(
      "data-evidence-ids",
      "two three",
    );
    expect(container.querySelector("mark")).toHaveAttribute("data-reveal", "true");
    expect(container.querySelector(".landing-story-note")).toHaveAttribute(
      "aria-hidden",
      "true",
    );
    setProgress(0.1);
    setProgress(0.99);
    expect(container.querySelector("[data-inviting]")).toBeNull();
    expect(claim).toHaveAttribute("aria-pressed", "true");
    expect(container.querySelector("mark")).toHaveTextContent(
      "Bob is a beneficiary of Trust.",
    );
  });
  it("reacts to a live reduced-motion change without losing selection and removes its media listener", async () => {
    const remove = vi.spyOn(media, "removeEventListener");
    const { container, unmount } = render(
      <DocumentStory state={example.state} />,
    );
    reduced(true);
    expect(container.querySelector("[data-inviting]")).not.toBeNull();
    expect(container.querySelector(".landing-story-invitation-trace")).toBeNull();
    expect(container.querySelector(".landing-story")).toHaveAttribute(
      "data-story-mode",
      "static",
    );
    const claim = screen.getByRole("button", {
      name: "Bob — beneficiary of — Trust",
    });
    await userEvent.click(claim);
    reduced(false);
    setProgress(0.99);
    expect(claim).toHaveAttribute("aria-pressed", "true");
    expect(container.querySelectorAll("[data-document-kind]")).toHaveLength(4);
    unmount();
    expect(remove).toHaveBeenCalled();
    expect(
      observers.every((observer) => observer.disconnect.mock.calls.length),
    ).toBe(true);
  });
  it("keyboard skip opens and focuses the review without changing the selected relationship", async () => {
    render(<DocumentStory state={example.state} />);
    const skip = screen.getByRole("link", {
      name: "Skip to relationship review",
    });
    skip.focus();
    await userEvent.keyboard("{Enter}");
    await waitFor(() =>
      expect(document.getElementById("landing-story-review")).toHaveFocus(),
    );
    expect(document.getElementById("landing-story-review")).not.toHaveAttribute(
      "inert",
    );
    expect(scrollTo).toHaveBeenCalledWith(
      expect.objectContaining({ behavior: "instant" }),
    );
  });
  it.each(["{Enter}", " "])("ends the invitation when keyboard selection %s reaffirms the initial relationship", async (key) => {
    const { container } = render(<DocumentStory state={example.state} />);
    setProgress(0.99);
    const initial = screen.getByRole("button", { name: "Alice — parent of — Bob" });
    initial.focus();
    await userEvent.keyboard(key);
    expect(container.querySelector("[data-inviting]")).toBeNull();
    expect(initial).toHaveAttribute("aria-pressed", "true");
    setProgress(0.1);
    setProgress(0.99);
    expect(container.querySelector("[data-inviting]")).toBeNull();
  });
  it.each(["pointer", "keyboard"])("%s exploration ends the invitation without selecting or scrolling Evidence", (input) => {
    const { container } = render(<DocumentStory state={example.state} />);
    setProgress(0.99);
    const claim = screen.getByRole("button", {
      name: "Bob — beneficiary of — Trust",
    });
    expect(claim).toHaveAttribute("data-inviting", "true");
    const evidence = container.querySelector("mark");
    scrollTo.mockClear();
    if (input === "pointer") fireEvent.pointerEnter(claim, { pointerType: "mouse" });
    else fireEvent.focus(claim);
    expect(container.querySelector("[data-inviting]")).toBeNull();
    expect(container.querySelector(".landing-story-invitation-trace")).toBeNull();
    expect(claim).toHaveAttribute("aria-pressed", "false");
    expect(evidence).toBe(container.querySelector("mark"));
    expect(evidence).toHaveTextContent("Alice is Bob’s parent.");
    expect(evidence).not.toHaveAttribute("data-reveal");
    expect(scrollTo).not.toHaveBeenCalled();
    setProgress(0.1);
    setProgress(0.99);
    expect(container.querySelector("[data-inviting]")).toBeNull();
  });
  it("cleans up StrictMode measurement observers and does not call a provider", async () => {
    const { unmount } = render(
      <StrictMode>
        <LandingPage />
      </StrictMode>,
    );
    await screen.findByRole("heading", {
      name: "It begins with your documents",
    });
    unmount();
    expect(
      observers.every((observer) => observer.disconnect.mock.calls.length),
    ).toBe(true);
    expect(
      vi
        .mocked(getPublicExample)
        .mock.calls.every(([signal]) => signal.aborted),
    ).toBe(true);
  });
  it("remeasures the actual deck on resize and ignores font completion after unmount", async () => {
    let resolveFonts!: () => void;
    const previous = Object.getOwnPropertyDescriptor(document, "fonts");
    Object.defineProperty(document, "fonts", {
      configurable: true,
      value: {
        ready: new Promise<void>((resolve) => {
          resolveFonts = resolve;
        }),
      },
    });
    const rectangles = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect");
    const { unmount } = render(<DocumentStory state={example.state} />);
    expect(
      observers.flatMap((observer) =>
        observer.observe.mock.calls.map(([element]) => element.className),
      ),
    ).toEqual(
      expect.arrayContaining([
        "landing-story-montage-intro",
        "landing-story-document-deck",
        "landing-story-document landing-story-document-attendance",
      ]),
    );
    const beforeResize = rectangles.mock.calls.length;
    act(() => window.dispatchEvent(new Event("resize")));
    expect(rectangles.mock.calls.length).toBeGreaterThan(beforeResize);
    unmount();
    const beforeFonts = rectangles.mock.calls.length;
    await act(async () => resolveFonts());
    expect(rectangles.mock.calls.length).toBe(beforeFonts);
    if (previous) Object.defineProperty(document, "fonts", previous);
    else Reflect.deleteProperty(document, "fonts");
  });
  it("preserves canonical selection and source text when the visitor switches language", async () => {
    reduced(true);
    const { container } = render(<LocaleProvider><LandingPage /></LocaleProvider>);
    const claim = await screen.findByRole("button", {
      name: "Bob — beneficiary of — Trust",
    });
    expect(claim).toHaveAttribute("data-inviting", "true");
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Language" }),
      "zh-CN",
    );
    expect(claim).toHaveAttribute("data-inviting", "true");
    expect(screen.queryByText("试着选择这项关系")).not.toBeInTheDocument();
    await userEvent.click(claim);
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "语言" }),
      "en",
    );
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Language" }),
      "zh-CN",
    );
    expect(container.querySelector("[data-inviting]")).toBeNull();
    expect(
      screen.getByRole("heading", { name: "从您的文件开始" }),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Bob — 受益人 — Trust" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      container.querySelector(".landing-story-source-text")?.textContent,
    ).toBe(example.state.sources[0].text);
  });
  it("retries a failed public read without fabricating a source or graph", async () => {
    vi.mocked(getPublicExample).mockRejectedValueOnce(new Error("Unavailable"));
    render(<LocaleProvider><LandingPage /></LocaleProvider>);
    const retry = await screen.findByRole("button", { name: "Try again" });
    expect(
      screen.queryByRole("heading", { name: "It begins with your documents" }),
    ).toBeNull();
    await userEvent.click(retry);
    await screen.findByRole("heading", {
      name: "It begins with your documents",
    });
    expect(getPublicExample).toHaveBeenCalledTimes(2);
  });
});
