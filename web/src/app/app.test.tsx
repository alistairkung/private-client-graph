import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { App } from "./App";

test.each(["/app", "/app/"])(
  "%s composes the practitioner shell without requesting showcase data",
  async (path) => {
    const user = userEvent.setup();
    window.history.replaceState(null, "", path);
    const fetcher = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async url => new Response(JSON.stringify(url === "/api/access" ? { can_write: false, sign_in_available: true } : [])));

    render(<App />);

    expect(screen.getByRole("heading", { name: "Matters" })).toBeVisible();
    expect(await screen.findByText("No accepted Matters yet")).toBeVisible();
    const proposals = screen.getByRole("heading", { name: "Awaiting confirmation" });
    const accepted = screen.getByRole("heading", { name: "Accepted Matters" });
    expect(proposals.compareDocumentPosition(accepted) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByRole("link", { name: "Matters" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.queryByRole("link", { name: "Public showcase" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Sign out" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Account and application menu" }));
    expect(screen.getByRole("link", { name: "Public showcase" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(screen.queryByRole("button", { name: "Sign out" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Sign in to make changes" })).toHaveLength(2);
    expect(fetcher.mock.calls.map(call => call[0]).sort()).toEqual(["/api/access", "/api/matter-proposals", "/api/matters"]);
    expect(document.title).toBe("Matters · Private Client Graph");
  },
);

test("practitioner notice remains visible outside the account menu", async () => {
  window.history.replaceState(null, "", "/app");
  vi.spyOn(globalThis, "fetch").mockImplementation(async url => new Response(JSON.stringify(url === "/api/access" ? { can_write: false, sign_in_available: true } : [])));
  render(<App />);
  expect(screen.getByText(/not suitable for real confidential client information/i)).toBeVisible();
  expect(screen.getByText(/publicly readable, including proposals awaiting confirmation/)).toBeVisible();
  expect(screen.getByRole("button", { name: "Account and application menu" })).toBeVisible();
  expect(screen.queryByRole("button", { name: "Sign out" })).not.toBeInTheDocument();
});

test("creation direct entry requires write access without loading analysis", async () => {
  window.history.replaceState(null, "", "/app/matter-proposals/new");
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ can_write: true, sign_in_available: true })));
  render(<App />);
  expect(await screen.findByRole("heading", { name: "Create Matter" })).toBeVisible();
  expect(screen.getByRole("checkbox", { name: /synthetic or fictional/ })).toBeVisible();
  expect(fetcher).toHaveBeenCalledExactlyOnceWith("/api/access", undefined);
  expect(document.title).toBe("Create Matter · Private Client Graph");
});

test("proposal direct entry reads its persisted source and graph without reanalysis", async () => {
  window.history.replaceState(null, "", "/app/matter-proposals/proposal-42");
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
    id: "proposal-42", external_reference: "Firm/42", matter_title: "Saved proposal",
    authoritative_source: { title: "Source title", text: "Saved source" },
    proposed_graph: { entities: [], relationships: [], evidence: [] },
  })));
  render(<App />);
  expect(await screen.findByRole("heading", { name: "Saved proposal" })).toBeVisible();
  expect(screen.getByRole("heading", { name: "Proposed relationships" })).toBeVisible();
  expect(fetcher.mock.calls.map(call => call[0]).sort()).toEqual(["/api/access", "/api/matter-proposals/proposal-42"]);
  expect(document.title).toBe("Saved proposal · Private Client Graph");
});


test("an unavailable capability endpoint leaves public Matters readable and write controls hidden", async () => {
  window.history.replaceState(null, "", "/app");
  vi.spyOn(globalThis, "fetch").mockImplementation(async url => {
    if (url === "/api/access") throw new TypeError("Unavailable");
    return new Response(JSON.stringify([]));
  });
  render(<App />);
  expect(await screen.findByText("No accepted Matters yet")).toBeVisible();
  expect(screen.queryByRole("link", { name: "Create Matter" })).not.toBeInTheDocument();
});

test("anonymous direct intake entry offers sign-in without exposing uploads", async () => {
  window.history.replaceState(null, "", "/app/matter-proposals/new");
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ can_write: false, sign_in_available: true })));
  render(<App />);
  expect(await screen.findByRole("link", { name: "Sign in to make changes" })).toHaveAttribute("href", "/auth/login?next=/app/matter-proposals/new");
  expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
});

test.each(["/app", "/app/matter-proposals/new"])(
  "%s distinguishes pending access from unavailable sign-in and reveals signed-in creation",
  async path => {
    window.history.replaceState(null, "", path);
    let resolveAccess!: (response: Response) => void;
    vi.spyOn(globalThis, "fetch").mockImplementation(url => url === "/api/access"
      ? new Promise(resolve => { resolveAccess = resolve; })
      : Promise.resolve(new Response(JSON.stringify([]))));
    render(<App />);
    expect(screen.getByText("Checking sign-in and editing access…")).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Account and application menu" }));
    expect(screen.queryByText(/Sign-in is currently unavailable/)).not.toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();

    await act(async () => resolveAccess(new Response(JSON.stringify({ can_write: true, sign_in_available: true }))));
    expect(screen.queryByText("Checking sign-in and editing access…")).not.toBeInTheDocument();
    if (path === "/app") expect(screen.getByRole("link", { name: "Create Matter" })).toBeVisible();
    else expect(screen.getByRole("checkbox", { name: /synthetic or fictional/ })).toBeVisible();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeVisible();
  },
);

test("failed access checks keep public reading and can recover signed-in creation without reloading", async () => {
  window.history.replaceState(null, "", "/app");
  let attempts = 0;
  vi.spyOn(globalThis, "fetch").mockImplementation(async url => {
    if (url !== "/api/access") return new Response(JSON.stringify([]));
    if (++attempts === 1) throw new TypeError("Unavailable");
    return new Response(JSON.stringify({ can_write: true, sign_in_available: true }));
  });
  render(<App />);
  expect(await screen.findByText("No accepted Matters yet")).toBeVisible();
  expect(await screen.findByText("Sign-in and editing access could not be checked. You can still read Matters and proposals.")).toBeVisible();
  expect(screen.queryByText(/Sign-in is currently unavailable/)).not.toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "Create Matter" })).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Retry access check" }));
  expect(await screen.findByRole("link", { name: "Create Matter" })).toBeVisible();
  expect(attempts).toBe(2);
});
