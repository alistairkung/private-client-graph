import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { CreateMatter } from "./CreateMatter";

const pdf = new File(["%PDF-fictional"], "Attendance note.pdf", { type: "application/pdf" });

async function fillIntake() {
  const user = userEvent.setup();
  await user.type(screen.getByRole("textbox", { name: "External Matter reference" }), "Firm/42");
  await user.type(screen.getByRole("textbox", { name: "Matter title" }), "Fictional family");
  await user.type(screen.getByRole("textbox", { name: "Authoritative Source title" }), "Attendance note");
  await user.upload(screen.getByLabelText("PDF"), pdf);
  return user;
}

test("requires synthetic confirmation, waits for one synchronous response, and opens the saved proposal", async () => {
  let finish!: (response: Response) => void;
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const navigate = vi.fn();
  render(<CreateMatter onNavigate={navigate} />);
  const user = await fillIntake();
  const submit = screen.getByRole("button", { name: "Upload and analyse" });
  expect(submit).toBeDisabled();
  await user.click(submit);
  expect(fetcher).not.toHaveBeenCalled();
  await user.click(screen.getByRole("checkbox", { name: /synthetic or fictional/ }));
  fireEvent.submit(submit.closest("form")!);
  expect(screen.getByRole("status")).toHaveTextContent("Uploading and analysing");
  expect(submit).toBeDisabled();
  expect(screen.getByRole("textbox", { name: "Matter title" })).toBeDisabled();
  expect(navigate).not.toHaveBeenCalled();
  finish(new Response(JSON.stringify({ id: "proposal-42" }), { status: 201 }));
  await waitFor(() => expect(navigate).toHaveBeenCalledWith("/app/matter-proposals/proposal-42"));
  expect(fetcher).toHaveBeenCalledOnce();
});

test.each(["matter_proposal", "matter"] as const)("explicit retry keeps local inputs and opens the existing %s from a duplicate response", async resourceKind => {
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(new Response(JSON.stringify({ error: { code: "provider_transient", message: "Analysis could not finish. No proposal was saved.", retryable: true } }), { status: 503 }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ error: { code: "duplicate_reference", message: "This reference already exists.", retryable: false, existing_resource: {
      resource_kind: resourceKind, resource_id: "existing-42", location: resourceKind === "matter" ? "/api/matters/existing-42" : "/api/matter-proposals/existing-42",
    } } }), { status: 409 }));
  const navigate = vi.fn();
  render(<CreateMatter onNavigate={navigate} />);
  const user = await fillIntake();
  await user.click(screen.getByRole("checkbox"));
  fireEvent.submit(screen.getByRole("button", { name: "Upload and analyse" }).closest("form")!);
  expect(await screen.findByRole("alert")).toHaveTextContent("No proposal was saved.");
  expect(screen.getByRole("textbox", { name: "Matter title" })).toHaveValue("Fictional family");
  expect((screen.getByLabelText("PDF") as HTMLInputElement).files?.[0]).toBe(pdf);
  expect(fetcher).toHaveBeenCalledOnce();
  fireEvent.submit(screen.getByRole("button", { name: "Retry analysis" }).closest("form")!);
  await waitFor(() => expect(navigate).toHaveBeenCalledWith(resourceKind === "matter" ? "/app/matters/existing-42" : "/app/matter-proposals/existing-42"));
  const form = fetcher.mock.calls[1][1]?.body as FormData;
  expect(form.get("pdf")).toBe(pdf);
  expect(form.get("external_reference")).toBe("Firm/42");
  expect(form.get("synthetic_confirmation")).toBe("true");
});

test.each([
  { code: "provider_configuration", message: "Analysis is unavailable.", retryable: false },
  { code: "quota_exhausted", message: "The analysis allowance is exhausted.", retryable: false, resets_at: "2099-10-05T00:00:00Z" },
])("$code does not encourage repeated analysis and preserves correction inputs", async error => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ error }), { status: 503 }));
  render(<CreateMatter onNavigate={vi.fn()} />);
  const user = await fillIntake();
  await user.click(screen.getByRole("checkbox"));
  const submit = screen.getByRole("button", { name: "Upload and analyse" });
  fireEvent.submit(submit.closest("form")!);
  expect(await screen.findByRole("alert")).toHaveTextContent(error.message);
  expect(submit).toBeDisabled();
  expect(screen.queryByRole("button", { name: "Retry analysis" })).not.toBeInTheDocument();
  if ("resets_at" in error) expect(document.querySelector("time")).toHaveAttribute("datetime", error.resets_at);
  fireEvent.submit(submit.closest("form")!);
  expect(fetcher).toHaveBeenCalledOnce();
});

test("an ambiguous response offers reference recovery without claiming the proposal failed", async () => {
  vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Network disconnected"));
  render(<CreateMatter onNavigate={vi.fn()} />);
  const user = await fillIntake();
  await user.click(screen.getByRole("checkbox"));
  fireEvent.submit(screen.getByRole("button", { name: "Upload and analyse" }).closest("form")!);
  expect(await screen.findByRole("alert")).toHaveTextContent("could not be confirmed");
  expect(screen.getByRole("button", { name: "Check reference and retry" })).toBeEnabled();
  expect(screen.getByRole("link", { name: "Check Matters and proposals" })).toHaveAttribute("href", "/app");
});

test("allowance reset permits an explicit retry without losing the local PDF or starting analysis automatically", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch");
  render(<CreateMatter onNavigate={vi.fn()} />);
  const user = await fillIntake();
  await user.click(screen.getByRole("checkbox"));
  vi.useFakeTimers();
  try {
    const reset = new Date(Date.now() + 1000).toISOString();
    fetcher.mockResolvedValue(new Response(JSON.stringify({ error: { code: "allowance_exhausted", message: "The analysis allowance is exhausted.", retryable: false, resets_at: reset } }), { status: 429 }));
    const submit = screen.getByRole("button", { name: "Upload and analyse" });
    await act(async () => { fireEvent.submit(submit.closest("form")!); });
    expect(submit).toBeDisabled();
    await act(async () => { vi.advanceTimersByTime(1001); });
    expect(submit).toBeEnabled();
    expect((screen.getByLabelText("PDF") as HTMLInputElement).files?.[0]).toBe(pdf);
    expect(fetcher).toHaveBeenCalledOnce();
  } finally {
    vi.useRealTimers();
  }
});
