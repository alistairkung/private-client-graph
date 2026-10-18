import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReviewPage } from "./ReviewPage";
import { useAppPath } from "../app/navigation";
import {
  confirmProposal,
  discardProposal,
  getReview,
  RequestFailure,
} from "../shared/api";

vi.mock("../shared/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../shared/api")>()),
  getReview: vi.fn(),
  confirmProposal: vi.fn(),
  discardProposal: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    value: function (this: HTMLDialogElement) {
      this.setAttribute("open", "");
    },
  });
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    value: function (this: HTMLDialogElement) {
      this.removeAttribute("open");
    },
  });
  vi.mocked(getReview).mockResolvedValue({
    id: "proposal",
    external_reference: "SYNTHETIC-ONLY",
    matter_title: "Fictional Matter",
    authoritative_source: null,
    state: { sources: [], entities: [], relationships: [], evidence: [] },
  });
});

async function closeDecision() {
  await userEvent.click(screen.getByRole("button", { name: "Keep reviewing" }));
  await waitFor(() =>
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
  );
}

describe("whole-proposal decision safeguards", () => {
  it.each(["confirm", "discard"] as const)(
    "keeps a deferred %s dialog attached through Back and link navigation until the completed action navigates",
    async (decision) => {
      window.history.replaceState(null, "", "/app");
      window.history.pushState(null, "", "/app/matter-proposals/proposal");
      const scroll = vi.spyOn(window, "scrollTo").mockImplementation(() => {});
      let finish = () => {};
      if (decision === "confirm") {
        vi.mocked(confirmProposal).mockImplementation(
          () =>
            new Promise<string>((resolve) => {
              finish = () => resolve("/app/matters/created");
            }),
        );
      } else {
        vi.mocked(discardProposal).mockImplementation(
          () =>
            new Promise<void>((resolve) => {
              finish = () => resolve();
            }),
        );
      }
      function RoutedDecision() {
        const path = useAppPath();
        return (
          <>
            <output data-testid="route">{path}</output>
            {path === "/app/matter-proposals/proposal" && (
              <ReviewPage kind="matter-proposals" id="proposal" />
            )}
          </>
        );
      }
      render(<RoutedDecision />);
      await userEvent.click(
        await screen.findByRole("button", {
          name:
            decision === "confirm" ? "Confirm proposal" : "Discard proposal",
        }),
      );
      await userEvent.click(
        screen.getByRole("button", {
          name:
            decision === "confirm"
              ? "Confirm and create Matter"
              : "Discard entire proposal",
        }),
      );
      expect(
        screen.getByRole("button", {
          name: decision === "confirm" ? "Confirming…" : "Discarding…",
        }),
      ).toBeDisabled();
      await userEvent.click(
        screen.getByRole("link", { name: /Back to Matters/ }),
      );
      expect(window.location.pathname).toBe("/app/matter-proposals/proposal");
      await act(async () => {
        const popped = new Promise<void>((resolve) =>
          window.addEventListener("popstate", () => resolve(), { once: true }),
        );
        window.history.back();
        await popped;
      });
      expect(window.location.pathname).toBe("/app/matter-proposals/proposal");
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      await act(async () => finish());
      await waitFor(() =>
        expect(screen.getByTestId("route")).toHaveTextContent(
          decision === "confirm" ? "/app/matters/created" : "/app",
        ),
      );
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      expect(
        decision === "confirm" ? confirmProposal : discardProposal,
      ).toHaveBeenCalledTimes(1);
      scroll.mockRestore();
    },
  );
  it.each([
    {
      action: "confirm",
      code: "outcome_unknown",
      retryable: true,
      outcome_unknown: true,
    },
    {
      action: "discard",
      code: "invalid_proposal",
      retryable: false,
      outcome_unknown: false,
    },
  ])(
    "retains $action terminal failure after dismissal and blocks both mutation paths",
    async (scenario) => {
      const failure = new RequestFailure(503, { ...scenario, message: "" });
      vi.mocked(confirmProposal).mockRejectedValue(failure);
      vi.mocked(discardProposal).mockRejectedValue(failure);
      render(<ReviewPage kind="matter-proposals" id="proposal" />);
      await userEvent.click(
        await screen.findByRole("button", {
          name:
            scenario.action === "confirm"
              ? "Confirm proposal"
              : "Discard proposal",
        }),
      );
      await userEvent.click(
        screen.getByRole("button", {
          name:
            scenario.action === "confirm"
              ? "Confirm and create Matter"
              : "Discard entire proposal",
        }),
      );
      await screen.findByRole("alert");
      expect(
        screen.getByRole("button", {
          name:
            scenario.action === "confirm"
              ? "Confirm and create Matter"
              : "Discard entire proposal",
        }),
      ).toBeDisabled();
      await closeDecision();
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(
        screen.getAllByRole("link", { name: "Check Matters" }).length,
      ).toBeGreaterThan(0);
      const confirm = screen.getByRole("button", { name: "Confirm proposal" });
      const discard = screen.getByRole("button", { name: "Discard proposal" });
      expect(confirm).toBeDisabled();
      expect(discard).toBeDisabled();
      await userEvent.click(confirm);
      await userEvent.click(discard);
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      expect(vi.mocked(confirmProposal)).toHaveBeenCalledTimes(
        scenario.action === "confirm" ? 1 : 0,
      );
      expect(vi.mocked(discardProposal)).toHaveBeenCalledTimes(
        scenario.action === "discard" ? 1 : 0,
      );
    },
  );

  it("preserves a known retryable failure through reopening and switching decisions while allowing a deliberate retry", async () => {
    const failure = new RequestFailure(503, {
      code: "confirmation_failed",
      message: "",
      retryable: true,
    });
    vi.mocked(confirmProposal).mockRejectedValue(failure);
    vi.mocked(discardProposal).mockRejectedValue(failure);
    render(<ReviewPage kind="matter-proposals" id="proposal" />);
    await userEvent.click(
      await screen.findByRole("button", { name: "Confirm proposal" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Confirm and create Matter" }),
    );
    await screen.findByRole("alert");
    await closeDecision();
    await userEvent.click(
      screen.getByRole("button", { name: "Confirm proposal" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "The proposal remains available",
    );
    expect(
      screen.getByRole("button", { name: "Confirm and create Matter" }),
    ).toBeEnabled();
    await closeDecision();
    await userEvent.click(
      screen.getByRole("button", { name: "Discard proposal" }),
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Discard entire proposal" }),
    ).toBeEnabled();
    await userEvent.click(
      screen.getByRole("button", { name: "Discard entire proposal" }),
    );
    expect(discardProposal).toHaveBeenCalledTimes(1);
    await screen.findByRole("alert");
  });
});
