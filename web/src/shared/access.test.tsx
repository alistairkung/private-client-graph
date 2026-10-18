import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { AccessNotice, AccessProvider, WriteGate, useAccess } from "./access";
import { request } from "./api";
import { clearSessionState, useSessionState } from "./session-state";

afterEach(() => { clearSessionState(); vi.unstubAllGlobals(); });
function Probe() {
  const [draft, setDraft] = useSessionState("intake:reference", "");
  const { refresh } = useAccess();
  return <><p>Public Matter remains readable</p><AccessNotice />
    <WriteGate><button>Upload and analyse</button></WriteGate>
    <input aria-label="Draft" value={draft} onChange={event => setDraft(event.target.value)} />
    <button onClick={refresh}>Refresh capabilities</button>
  </>;
}
const response = (can_write: boolean, sign_in_available = true) => new Response(JSON.stringify({ can_write, sign_in_available }));

it("keeps public reading available during unknown capability state and permits retry without claiming sign-in is unavailable", async () => {
  let fail: (reason: unknown) => void = () => {};
  const fetch = vi.fn().mockImplementationOnce(() => new Promise((_resolve, reject) => { fail = reject; })).mockResolvedValue(response(true));
  vi.stubGlobal("fetch", fetch);
  render(<AccessProvider><Probe /></AccessProvider>);
  expect(screen.getByText("Public Matter remains readable")).toBeVisible();
  expect(screen.getByRole("status")).toHaveTextContent("Checking sign-in");
  expect(screen.queryByText(/currently unavailable/)).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Upload and analyse" })).not.toBeInTheDocument();
  await act(async () => fail(new Error("offline")));
  fireEvent.click(await screen.findByRole("button", { name: "Retry access check" }));
  expect(await screen.findByRole("button", { name: "Upload and analyse" })).toBeEnabled();
});

it.each([true, false])("offers local sign-in only when the server confirms availability (%s)", async available => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(false, available)));
  render(<AccessProvider><Probe /></AccessProvider>);
  await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
  if (available) expect(screen.getByRole("link", { name: "Sign in to make changes" })).toHaveAttribute("href", "/auth/login?next=%2F");
  else expect(screen.getByText(/Sign-in is currently unavailable/)).toBeVisible();
  expect(screen.getByText("Public Matter remains readable")).toBeVisible();
});

it("clears session-owned drafts after confirmed demotion while preserving public content", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(response(true)).mockResolvedValue(response(false)));
  render(<AccessProvider><Probe /></AccessProvider>);
  await screen.findByRole("button", { name: "Upload and analyse" });
  fireEvent.change(screen.getByLabelText("Draft"), { target: { value: "SYNTHETIC-DRAFT" } });
  fireEvent.click(screen.getByRole("button", { name: "Refresh capabilities" }));
  await waitFor(() => expect(screen.getByLabelText("Draft")).toHaveValue(""));
  expect(screen.getByText("Public Matter remains readable")).toBeVisible();
});

it.each([401, 403])("clears drafts and rechecks capabilities when a mutation is denied (%s)", async status => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(response(true)).mockResolvedValueOnce(new Response("{}", { status })).mockResolvedValue(response(false)));
  render(<AccessProvider><Probe /></AccessProvider>);
  await screen.findByRole("button", { name: "Upload and analyse" });
  fireEvent.change(screen.getByLabelText("Draft"), { target: { value: "SYNTHETIC-DRAFT" } });
  await act(async () => { await expect(request("/api/matters", { method: "POST" })).rejects.toMatchObject({ status }); });
  expect(screen.getByLabelText("Draft")).toHaveValue("");
  expect(screen.getByText("Public Matter remains readable")).toBeVisible();
  expect(await screen.findByRole("link", { name: "Sign in to make changes" })).toBeVisible();
});
