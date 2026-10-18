import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { PractitionerApp } from "./PractitionerApp";
import { clearSessionState } from "../shared/session-state";

beforeEach(() => {
  clearSessionState();
  vi.stubGlobal("matchMedia", vi.fn().mockReturnValue({
    matches: false,
    addEventListener: () => {},
    removeEventListener: () => {},
  }));
});
afterEach(() => vi.unstubAllGlobals());
function mockReads(access: { can_write: boolean; sign_in_available: boolean }) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async url => {
    if (url === "/api/access") return new Response(JSON.stringify(access));
    if (String(url).includes("/proposal-42")) return new Response(JSON.stringify({
      id: "proposal-42", external_reference: "SYNTHETIC/42", matter_title: "Saved proposal",
      authoritative_source: { title: "Fictional Source", text: "Exact synthetic Source text." },
      proposed_graph: { entities: [], relationships: [], evidence: [] },
    }));
    return new Response(JSON.stringify([]));
  });
}
it.each(["/app", "/app/"])("%s composes public collections and account actions without requesting curated data", async path => {
  window.history.replaceState(null, "", path);
  const fetch = mockReads({ can_write: false, sign_in_available: true });
  render(<PractitionerApp />);
  expect(await screen.findByText("No proposals awaiting confirmation.")).toBeVisible();
  expect(screen.getByRole("heading", { name: "Accepted Matters" })).toBeVisible();
  expect(screen.getByText(/publicly readable, including proposals awaiting confirmation/)).toBeVisible();
  expect(screen.getAllByRole("link", { name: "New proposal" })).toHaveLength(2);
  await userEvent.click(screen.getByRole("button", { name: "Account menu" }));
  expect(screen.getByRole("link", { name: "Public showcase" })).toHaveAttribute("href", "/");
  expect(screen.queryByRole("button", { name: "Sign out" })).not.toBeInTheDocument();
  expect(fetch.mock.calls.map(call => call[0]).sort()).toEqual(["/api/access", "/api/matter-proposals", "/api/matters"]);
});
it("reads a persisted pending Source directly while anonymous and gates whole-proposal decisions", async () => {
  window.history.replaceState(null, "", "/app/matter-proposals/proposal-42");
  const fetch = mockReads({ can_write: false, sign_in_available: true });
  render(<PractitionerApp />);
  expect(await screen.findByRole("heading", { name: "Saved proposal" })).toBeVisible();
  expect(screen.getByText("Exact synthetic Source text.")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Confirm proposal" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Discard proposal" })).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Sign in to make changes" })).toBeVisible();
  expect(fetch.mock.calls.map(call => call[0]).sort()).toEqual(["/api/access", "/api/matter-proposals/proposal-42"]);
});
it("shows intake while access loads and enables it only after write capability is confirmed", async () => {
  window.history.replaceState(null, "", "/app/matter-proposals/new");
  let resolveAccess: (response: Response) => void = () => {};
  vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(resolve => { resolveAccess = resolve; }));
  render(<PractitionerApp />);
  expect(screen.getByRole("status")).toHaveTextContent("Checking sign-in");
  expect(screen.getByRole("heading", { name: "New proposal" })).toBeVisible();
  expect(screen.getByRole("checkbox")).toBeDisabled();
  expect(screen.getByRole("button", { name: "Upload and analyse" })).toBeDisabled();
  await act(async () => resolveAccess(new Response(JSON.stringify({ can_write: true, sign_in_available: true }))));
  expect(await screen.findByRole("checkbox")).toBeEnabled();
  expect(screen.getByText(/Saving a proposal publishes every Source title/)).toBeVisible();
});
it.each(["anonymous", "unavailable", "error"])("keeps the intake preview public and blocks uploads and submission when access is %s", async mode => {
  window.history.replaceState(null, "", "/app/matter-proposals/new");
  const fetch = vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
    if (mode === "error") throw new TypeError("offline");
    return new Response(JSON.stringify({ can_write: false, sign_in_available: mode === "anonymous" }));
  });
  render(<PractitionerApp />);
  if (mode === "anonymous") {
    expect(await screen.findByRole("link", { name: "Sign in to make changes" })).toHaveAttribute("href", "/auth/login?next=%2Fapp%2Fmatter-proposals%2Fnew");
  } else if (mode === "error") {
    expect(await screen.findByRole("button", { name: "Retry access check" })).toBeVisible();
  } else {
    expect(await screen.findByText(/Sign-in is currently unavailable/)).toBeVisible();
  }
  expect(screen.getByRole("heading", { name: "New proposal" })).toBeVisible();
  expect(screen.getByText(/Saving a proposal publishes every Source title/)).toBeVisible();
  expect(screen.getByLabelText("External Matter reference")).toBeDisabled();
  expect(screen.getByLabelText("PDF sources")).toBeDisabled();
  const submit = screen.getByRole("button", { name: "Upload and analyse" });
  expect(submit).toBeDisabled();
  fireEvent.drop(screen.getByText("Choose PDF sources").closest("label")!, {
    dataTransfer: { files: [new File(["synthetic"], "synthetic.pdf", { type: "application/pdf" })] },
  });
  expect(screen.queryByText("synthetic.pdf")).not.toBeInTheDocument();
  fireEvent.submit(submit.closest("form")!);
  expect(fetch.mock.calls.map(call => call[0])).toEqual(["/api/access"]);
});
it("retains readable pending Sources after sign-out and removes mutation actions without redirecting", async () => {
  window.history.replaceState(null, "", "/app/matter-proposals/proposal-42");
  let signedOut = false;
  vi.spyOn(globalThis, "fetch").mockImplementation(async url => {
    if (url === "/auth/logout") { signedOut = true; return new Response(null, { status: 204 }); }
    if (url === "/api/access") return new Response(JSON.stringify({ can_write: !signedOut, sign_in_available: true }));
    return new Response(JSON.stringify({
      id: "proposal-42", external_reference: "SYNTHETIC/42", matter_title: "Saved proposal",
      authoritative_source: { title: "Fictional Source", text: "Exact synthetic Source text." },
      proposed_graph: { entities: [], relationships: [], evidence: [] },
    }));
  });
  render(<PractitionerApp />);
  await screen.findByRole("button", { name: "Confirm proposal" });
  await userEvent.click(screen.getByRole("button", { name: "Account menu" }));
  await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
  await waitFor(() => expect(screen.queryByRole("button", { name: "Confirm proposal" })).not.toBeInTheDocument());
  expect(screen.getByRole("heading", { name: "Saved proposal" })).toBeVisible();
  expect(screen.getByText("Exact synthetic Source text.")).toBeInTheDocument();
  expect(window.location.pathname).toBe("/app/matter-proposals/proposal-42");
});
it.each([false, true])("uses the existing app route for curated selection and Back/Forward query state, compact=%s", async compact => {
  vi.mocked(window.matchMedia).mockReturnValue({ matches: compact, addEventListener: () => {}, removeEventListener: () => {} } as unknown as MediaQueryList);
  window.history.replaceState(null, "", "/app");
  vi.spyOn(window, "scrollTo").mockImplementation(() => {});
  const cases = [
    { id: "case-01", title: "Case 01 · Evergreen", description: "Synthetic example" },
    { id: "case-04", title: "Case 04 · Hillcrest", description: "Synthetic example" },
  ];
  vi.spyOn(globalThis, "fetch").mockImplementation(async url => {
    if (url === "/api/access") return new Response(JSON.stringify({ can_write: false, sign_in_available: true }));
    if (url === "/api/showcase/cases") return new Response(JSON.stringify(cases));
    if (String(url).startsWith("/api/showcase/cases/")) {
      const summary = cases.find(item => String(url).endsWith(item.id));
      return new Response(JSON.stringify({ ...summary, notice: "Synthetic curated example", state: { sources: [], entities: [], relationships: [], evidence: [] } }));
    }
    return new Response("[]");
  });
  render(<PractitionerApp />);
  await screen.findByText("No proposals awaiting confirmation.");
  if (compact) await userEvent.click(screen.getByRole("button", { name: "Menu" }));
  await userEvent.click(screen.getByRole("link", { name: "Curated examples" }));
  if (compact) expect(screen.getByRole("button", { name: "Menu" })).toHaveAttribute("aria-expanded", "false");
  expect(await screen.findByRole("heading", { name: "Case 01 · Evergreen" })).toBeVisible();
  expect(window.location.pathname + window.location.search).toBe("/app?example=case-01");
  if (!compact) expect(screen.getByRole("link", { name: "Curated examples" })).toHaveAttribute("aria-current", "page");
  await userEvent.selectOptions(screen.getByLabelText("Choose a synthetic case"), "case-04");
  expect(await screen.findByRole("heading", { name: "Case 04 · Hillcrest" })).toBeVisible();
  expect(window.location.search).toBe("?example=case-04");
  expect(screen.getByRole("button", { name: "Next example" })).toBeDisabled();
  await userEvent.click(screen.getByRole("button", { name: "Previous example" }));
  expect(await screen.findByRole("heading", { name: "Case 01 · Evergreen" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Previous example" })).toBeDisabled();
  await userEvent.click(screen.getByRole("button", { name: "Next example" }));
  expect(await screen.findByRole("heading", { name: "Case 04 · Hillcrest" })).toBeVisible();
  act(() => window.history.back());
  expect(await screen.findByRole("heading", { name: "Accepted Matters" })).toBeVisible();
  if (!compact) expect(screen.getByRole("link", { name: "Curated examples" })).not.toHaveAttribute("aria-current");
  act(() => window.history.forward());
  expect(await screen.findByRole("heading", { name: "Case 04 · Hillcrest" })).toBeVisible();
  expect(screen.getByLabelText("Choose a synthetic case")).toHaveValue("case-04");
});
