import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReviewPage } from "./ReviewPage";
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

describe("whole-proposal decision safeguards", () => {
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
      await userEvent.click(
        screen.getByRole("button", { name: "Keep reviewing" }),
      );
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
    await userEvent.click(
      screen.getByRole("button", { name: "Keep reviewing" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Confirm proposal" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "The proposal remains available",
    );
    expect(
      screen.getByRole("button", { name: "Confirm and create Matter" }),
    ).toBeEnabled();
    await userEvent.click(
      screen.getByRole("button", { name: "Keep reviewing" }),
    );
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
