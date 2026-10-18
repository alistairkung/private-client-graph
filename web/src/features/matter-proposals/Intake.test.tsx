import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { createProposal, RequestFailure } from "../../shared/api";
import { clearSessionState } from "../../shared/session-state";
import { Intake } from "./Intake";

vi.mock("../../shared/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../shared/api")>()),
  createProposal: vi.fn(),
}));
beforeEach(() => {
  vi.clearAllMocks();
  clearSessionState();
});
async function enterDraft() {
  await userEvent.type(
    screen.getByLabelText("External Matter reference"),
    "FICTIONAL/DRAFT",
  );
  await userEvent.type(
    screen.getByLabelText("Matter title"),
    "Fictional retained Matter",
  );
  await userEvent.upload(
    screen.getByLabelText("PDF sources"),
    new File(["fictional source"], "fictional.pdf", {
      type: "application/pdf",
    }),
  );
  await userEvent.click(screen.getByRole("checkbox"));
}

it("retains a non-retryable analysis failure with its draft after leaving and returning", async () => {
  vi.mocked(createProposal).mockRejectedValue(
    new RequestFailure(503, {
      code: "outcome_unknown",
      message: "",
      retryable: false,
      outcome_unknown: true,
    }),
  );
  const view = render(<Intake />);
  await enterDraft();
  await userEvent.click(
    screen.getByRole("button", { name: "Upload and analyse" }),
  );
  await screen.findByRole("alert");
  view.unmount();
  render(<Intake />);
  expect(screen.getByLabelText("External Matter reference")).toHaveValue(
    "FICTIONAL/DRAFT",
  );
  expect(screen.getByRole("alert")).toHaveTextContent("outcome is unknown");
  expect(
    screen.getByRole("button", { name: "Check reference and retry" }),
  ).toBeDisabled();
  expect(createProposal).toHaveBeenCalledTimes(1);
});

it("clears mounted draft fields and removes the unload warning when the session ends", async () => {
  render(<Intake />);
  await enterDraft();
  expect(
    window.dispatchEvent(new Event("beforeunload", { cancelable: true })),
  ).toBe(false);
  act(clearSessionState);
  expect(screen.getByLabelText("External Matter reference")).toHaveValue("");
  expect(screen.getByLabelText("Matter title")).toHaveValue("");
  expect(
    window.dispatchEvent(new Event("beforeunload", { cancelable: true })),
  ).toBe(true);
  await waitFor(() =>
    expect(screen.queryByText("fictional.pdf")).not.toBeInTheDocument(),
  );
});
