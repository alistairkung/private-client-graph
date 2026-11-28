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
  expect(await screen.findByText(/No accepted Matters yet/)).toBeVisible();
  expect(screen.getByRole("heading", { name: "Matters" })).toBeVisible();
  expect(screen.getByRole("link", { name: "Review" })).toHaveAttribute("href", "/app/review");
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
  expect(fetch.mock.calls.map(call => call[0]).sort()).toEqual(["/api/access", "/api/matter-proposals", "/api/matter-proposals/proposal-42"]);
});
it("shows intake while access loads and enables it only after write capability is confirmed", async () => {
  window.history.replaceState(null, "", "/app/matter-proposals/new");
  let resolveAccess: (response: Response) => void = () => {};
  vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => {
    if (url === "/api/matter-proposals") return new Response("[]");
    return new Promise(resolve => { resolveAccess = resolve; });
  });
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
  expect(fetch.mock.calls.map(call => call[0]).sort()).toEqual(["/api/access", "/api/matter-proposals"]);
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
  await screen.findByText(/No accepted Matters yet/);
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
  expect(await screen.findByRole("heading", { name: "Matters" })).toBeVisible();
  if (!compact) expect(screen.getByRole("link", { name: "Curated examples" })).not.toHaveAttribute("aria-current");
  act(() => window.history.forward());
  expect(await screen.findByRole("heading", { name: "Case 04 · Hillcrest" })).toBeVisible();
  expect(screen.getByLabelText("Choose a synthetic case")).toHaveValue("case-04");
});

it("keeps the Review count global and preserves independent searches across both indexes", async () => {
  window.history.replaceState(null, "", "/app");
  vi.spyOn(window, "scrollTo").mockImplementation(() => {});
  const pending = [
    { id: "one", external_reference: "P/01", matter_title: "Larch proposal" },
    { id: "two", external_reference: "P/02", matter_title: "Cedar proposal" },
  ];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => {
    if (url === "/api/access")
      return new Response(JSON.stringify({ can_write: false, sign_in_available: true }));
    if (url === "/api/matters")
      return new Response(JSON.stringify([{ id: "accepted", external_reference: "M/01", title: "Accepted example" }]));
    return new Response(JSON.stringify(pending));
  });
  render(<PractitionerApp />);

  const reviewLink = await screen.findByRole("link", { name: "Review, 2 proposals awaiting confirmation" });
  const matterSearch = screen.getByRole("searchbox", { name: "Search Matters" });
  expect(await screen.findByRole("link", { name: /Accepted example/ })).toBeVisible();
  expect(screen.queryByRole("link", { name: /Larch proposal/ })).not.toBeInTheDocument();
  await userEvent.type(matterSearch, "M/01");
  await userEvent.click(reviewLink);
  const proposalSearch = screen.getByRole("searchbox", { name: "Search proposals" });
  expect(proposalSearch).toHaveValue("");
  expect(await screen.findByRole("link", { name: /Larch proposal/ })).toBeVisible();
  await userEvent.type(proposalSearch, "Larch");
  expect(screen.queryByRole("link", { name: /Cedar proposal/ })).not.toBeInTheDocument();
  expect(await screen.findByRole("link", { name: "Review, 2 proposals awaiting confirmation" })).toHaveAttribute("aria-current", "page");

  pending.pop();
  await userEvent.click(screen.getByRole("link", { name: "Matters" }));
  expect(screen.getByRole("searchbox", { name: "Search Matters" })).toHaveValue("M/01");
  await userEvent.click(await screen.findByRole("link", { name: "Review, 1 proposal awaiting confirmation" }));
  expect(screen.getByRole("searchbox", { name: "Search proposals" })).toHaveValue("Larch");
});

it("keeps Review available when the proposal read fails and recovers to the empty queue", async () => {
  window.history.replaceState(null, "", "/app/review");
  let attempts = 0;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => {
    if (url === "/api/access")
      return new Response(JSON.stringify({ can_write: false, sign_in_available: true }));
    if (++attempts === 1) throw new TypeError("offline");
    return new Response("[]");
  });
  render(<PractitionerApp />);
  expect(screen.getByRole("link", { name: "Review" })).toHaveAttribute("aria-current", "page");
  await userEvent.click(await screen.findByRole("button", { name: "Try again" }));
  expect(await screen.findByText("No proposals awaiting confirmation.")).toBeVisible();
  expect(screen.queryByRole("searchbox", { name: "Search proposals" })).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Review" })).toHaveAttribute("href", "/app/review");
  expect(attempts).toBe(2);
});
