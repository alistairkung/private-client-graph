import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { candidates, mergeHits, type View } from "./api";
import { AccessProvider } from "../../../shared/access";
import { Intake } from "../Intake";
import { SearchSummary } from "./DiscoveryResults";
import { WorkspaceConnection } from "./WorkspaceConnection";
import { WorkspaceDiscovery } from "./WorkspaceDiscovery";

const view: View = {
  scope: {
    mailbox: "synthetic@example.test",
    folder: "folder-1",
    label: "alder-label",
    first_day: null,
    last_day: null,
  },
  can_inspect_more: false,
  original_query: "Alder Trust",
  original_item_limit: 50,
  revision: 0,
  returned_messages: ["same", "denied", "failed"],
  inspected: ["same"],
  inspected_titles: { same: "Letter" },
  skipped: ["denied"],
  failed: ["failed"],
  pending: [],
  suggestions: [],
  files: [{ id: "same", title: "Deed" }],
  more_pages: false,
  stop_reason: null,
  requests: 4,
  bytes: 400,
};

it("merges hits by provider and ID and keeps rejected mail out of every result set", () => {
  const hits = {
    revision: 0,
    query: "Name",
    more_pages: false,
    stop_reason: null,
    files: view.files,
    messages: ["same", "new", "denied", "failed"],
  };
  const original = mergeHits([], { messages: view.returned_messages, files: view.files });
  const followUp = mergeHits(original, hits, hits.query);
  expect(candidates(mergeHits(followUp, hits, hits.query), view, n => "Hit " + n)).toEqual([
    { kind: "email", id: "same", title: "Letter" },
    { kind: "pdf", id: "same", title: "Deed" },
    { kind: "email", id: "new", title: "Hit 2", followUp: "Name" },
  ]);
});

it("shows the search indicator only while discovery is pending", async () => {
  let finish!: (response: Response) => void;
  vi.spyOn(globalThis, "fetch").mockImplementationOnce(
    () => new Promise<Response>((resolve) => { finish = resolve; }),
  );
  render(<WorkspaceDiscovery onBusy={() => {}} />);
  await userEvent.click(screen.getByRole("button", { name: "Start private discovery" }));
  const status = screen.getByRole("status");
  expect(status).toHaveTextContent("Searching emails and PDFs…");
  expect(status.querySelector(".discovery-spinner")).toHaveAttribute("aria-hidden", "true");
  finish(new Response(JSON.stringify({ session: "local", view })));
  await screen.findByRole("heading", { name: "Select Sources" });
  expect(status.querySelector(".discovery-spinner")).toBeNull();
});

it("explains incomplete coverage without operational counters or a dead-end action", () => {
  render(<SearchSummary folder={view.scope.folder} label={view.scope.label} view={{ ...view, more_pages: true, stop_reason: "Session byte limit" }} searching={false} interrupted={false} retry={vi.fn()} />);
  expect(screen.getByText("Checked 1 of 3 emails for leads.")).toBeVisible();
  expect(screen.getByText("Unavailable emails: 2.")).toBeVisible();
  expect(screen.queryByText("Original search complete.")).toBeNull();
  expect(screen.getByText("This search reached its limit.")).toBeVisible();
  expect(screen.queryByText(/requests|bytes|Inspection details/i)).toBeNull();
  expect(screen.queryByRole("button")).toBeNull();
});

it("renders each original batch, preserves selection, and stops at the combined cap", async () => {
  const user = userEvent.setup();
  const partial = { ...view, revision: 3, can_inspect_more: true, more_pages: true };
  const post = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(Response.json({ session: "local", view: partial }));
  let finish!: (response: Response) => void;
  post.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  render(<WorkspaceDiscovery onBusy={() => {}} />);
  await user.click(screen.getByText("Start private discovery"));
  expect(await screen.findByText("Still searching emails and PDFs…")).toBeVisible();
  await user.click(screen.getByLabelText("Letter · Email"));
  expect(post).toHaveBeenCalledTimes(2);
  expect(post.mock.calls[1][0]).toMatch(/discovery\/inspect$/);
  expect(JSON.parse(String(post.mock.calls[1][1]?.body))).toEqual({ session: "local", revision: 3 });
  finish(Response.json({ ...partial, revision: 4, can_inspect_more: false, stop_reason: "Original item limit",
    files: [...view.files, { id: "late", title: "Appointment" }] }));
  expect(await screen.findByLabelText("Appointment · PDF")).toBeVisible();
  expect(screen.getByLabelText("Letter · Email")).toBeChecked();
  expect(screen.getByText("Stopped at 50 original results. More matches may be available.")).toBeVisible();
  expect(screen.queryByText("Still searching emails and PDFs…")).toBeNull();
  expect(post).toHaveBeenCalledTimes(2);
});

it("retains a follow-up's email and PDF rows while an open email gains its inspected subject", async () => {
  const user = userEvent.setup();
  const lead = { query: "Mara Voss", origin: "same", passage: "Mara will send it.", rationale: "Find the deed." };
  const first = { ...view, can_inspect_more: true, suggestions: [lead] };
  let deliverBatch!: (response: Response) => void;
  vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(Response.json({ session: "local", view: first }))
    .mockImplementationOnce(() => new Promise(resolve => { deliverBatch = resolve; }))
    .mockResolvedValueOnce(Response.json({ messages: ["shared"], files: [{ id: "shared", title: "Old PDF title" }] }))
    .mockResolvedValueOnce(Response.json({ title: "Appointment email", text: "Private message" }));
  render(<WorkspaceDiscovery onBusy={() => {}} />);
  await user.click(screen.getByText("Start private discovery"));
  await user.click(screen.getByText("Search for Mara Voss"));
  const group = within(screen.getByRole("group", { name: "Found via Mara Voss" }));
  const trigger = group.getByRole("button", { name: "Read Uninspected email 2" });
  await user.click(trigger);
  await screen.findByRole("dialog", { name: "Appointment email" });
  await act(async () => deliverBatch(Response.json({
    ...view, revision: 1, returned_messages: [...view.returned_messages, "shared"],
    inspected_titles: { ...view.inspected_titles, shared: "Appointment email" },
    files: [...view.files, { id: "shared", title: "Revised PDF title" }],
  })));
  await user.click(screen.getByRole("button", { name: "Close dialog" }));
  expect(trigger).toHaveFocus();
  expect(group.getByRole("button", { name: "Read Appointment email" })).toBe(trigger);
  expect(group.getByLabelText("Revised PDF title · PDF")).toBeVisible();
  expect(screen.getAllByLabelText("Appointment email · Email")).toHaveLength(1);
});

it("shows the applied folder, label and inclusive Gmail dates even for an empty search", async () => {
  const scope = { folder: "folder-1", label: "alder-label", folder_name: "Trust deeds", label_name: "Trust mail" };
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(Response.json({
    session: "local",
    view: { ...view, scope: { ...view.scope, first_day: "2024-01-01", last_day: "2024-01-31" },
      returned_messages: [], inspected: [], skipped: [], failed: [], files: [] },
  }));
  render(<WorkspaceDiscovery scope={scope} onBusy={() => {}} />);
  await userEvent.click(screen.getByText("Start private discovery"));
  await screen.findByText("No Sources available to select.");
  expect(screen.getByText("Trust deeds")).toBeVisible();
  expect(screen.getByText("Trust mail")).toBeVisible();
  expect(screen.getByText("Gmail dates (UTC)")).toBeVisible();
  expect(screen.getByText("2024-01-01 – 2024-01-31")).toBeVisible();
});

it("stops on network loss and resumes the same revision only on request", async () => {
  const first = { ...view, can_inspect_more: true, more_pages: true };
  const post = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(Response.json({ session: "local", view: first }))
    .mockRejectedValueOnce(new TypeError("offline"));
  const { unmount } = render(<WorkspaceDiscovery onBusy={() => {}} />);
  await userEvent.click(screen.getByText("Start private discovery"));
  expect(await screen.findByText("Search interrupted. Results already found are available.")).toBeVisible();
  expect(post).toHaveBeenCalledTimes(2);
  let finish!: (response: Response) => void;
  post.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await userEvent.click(screen.getByText("Resume original search"));
  expect(post.mock.calls[2][1]?.body).toBe(post.mock.calls[1][1]?.body);
  const signal = post.mock.calls[2][1]?.signal;
  unmount();
  expect(signal?.aborted).toBe(true);
  await act(async () => finish(Response.json({ ...first, revision: 1 })));
  expect(post).toHaveBeenCalledTimes(3);
});

it("closing a loading email discards its late body and leaves selection alone", async () => {
  const post = vi.spyOn(globalThis, "fetch");
  post.mockResolvedValueOnce(new Response(JSON.stringify({ session: "local", view })));
  render(<WorkspaceDiscovery onBusy={() => {}} />);
  await userEvent.click(screen.getByText("Start private discovery"));
  let finish!: (response: Response) => void;
  post.mockImplementationOnce(() => new Promise<Response>(resolve => { finish = resolve; }));
  await userEvent.click(screen.getByRole("button", { name: "Read Letter" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("Opening email…");
  await userEvent.click(screen.getByRole("button", { name: "Close dialog" }));
  await act(async () => finish(new Response(JSON.stringify({ title: "Letter", text: "Late private body" }))));
  expect(screen.queryByText("Late private body")).toBeNull();
  expect(screen.getByLabelText("Letter · Email")).not.toBeChecked();
  expect(screen.getByText("Preview exact Sources")).toBeDisabled();
});

it("reordering invalidates approval and a failed import requires another exact preview", async () => {
  const user = userEvent.setup();
  const post = vi.spyOn(globalThis, "fetch");
  const result = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status });
  post.mockResolvedValueOnce(result({ session: "local", view }));
  render(<WorkspaceDiscovery onBusy={() => {}} />);
  await user.click(screen.getByText("Start private discovery"));
  await user.click(screen.getByLabelText("Letter · Email"));
  await user.click(screen.getByLabelText("Deed · PDF"));
  async function preview(token: string) {
    post.mockResolvedValueOnce(
      result({
        token,
        sources: [{ id: "source_001", title: "Reviewed", text: "Full text" }],
      }),
    );
    await user.click(screen.getByText("Preview exact Sources"));
    await screen.findByText("Full text");
  }
  await preview("one");
  await user.type(screen.getByLabelText("Matter title"), "Example");
  await user.type(screen.getByLabelText("External Matter reference"), "REF");
  await user.click(screen.getByLabelText(/I approve publishing/));
  expect(screen.queryByRole("heading", { name: "Select Sources" })).toBeNull();
  await user.click(screen.getByRole("button", { name: "Edit selection" }));
  expect(screen.getByRole("heading", { name: "Select Sources" })).toHaveFocus();
  await user.click(screen.getByText("Preview order"));
  await user.click(screen.getByRole("button", { name: "Move Deed up" }));
  expect(screen.queryByText("Create public proposal")).toBeNull();
  await preview("two");
  expect(screen.getByText("Create public proposal")).toBeDisabled();
  await user.click(screen.getByLabelText(/I approve publishing/));
  post.mockResolvedValueOnce(
    result(
      { error: { code: "preview_required", message: "", retryable: false } },
      409,
    ),
  );
  await user.click(screen.getByText("Create public proposal"));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Preview the selected Sources again",
  );
  expect(screen.queryByText("Full text")).toBeNull();
  await preview("three");
  expect(screen.getByText("Create public proposal")).toBeDisabled();
  expect(screen.getByLabelText("Matter title")).toHaveValue("Example");
});

it("retiring a Workspace grant removes private results and offers a fresh connection", async () => {
  const user = userEvent.setup();
  const respond = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status });
  const post = vi.spyOn(globalThis, "fetch");
  post.mockResolvedValueOnce(
    respond({
      connected: true,
      generation: "one",
      expires: Date.now() / 1000 + 300,
      account: "pilot@example.test",
      folder: "folder",
      label: "label",
      folder_name: "Alder",
      label_name: "Letters",
    }),
  );
  render(<WorkspaceConnection onBusy={vi.fn()} />);
  const start = await screen.findByText("Start private discovery");
  expect(post).toHaveBeenCalledTimes(1);
  post.mockResolvedValueOnce(
    respond({ session: "first", view: { ...view, can_inspect_more: true } }),
  );
  let finish!: (response: Response) => void;
  post.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await user.click(start);
  expect(await screen.findByLabelText("Letter · Email")).toBeVisible();
  await act(async () => finish(respond(
    { error: { code: "workspace_reconnect", message: "", retryable: false } }, 409,
  )));
  expect(
    await screen.findByRole("button", { name: "Reconnect" }),
  ).toBeEnabled();
  expect(screen.queryByLabelText("Letter · Email")).toBeNull();
  expect(screen.queryByText("Start private discovery")).toBeNull();
});

it("keeps the selection editable when a single Source becomes unavailable", async () => {
  const user = userEvent.setup();
  const post = vi.spyOn(globalThis, "fetch");
  const response = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status });
  const grantLost = vi.fn();
  render(
    <WorkspaceDiscovery
      onBusy={() => {}}
      onGrantLoss={grantLost}
      scope={{
        folder: "folder",
        label: "label",
        label_name: "Letters",
        folder_name: "Deeds",
      }}
    />,
  );
  post.mockResolvedValueOnce(response({ session: "first", view }));
  await user.click(screen.getByText("Start private discovery"));
  await user.click(screen.getByLabelText("Letter · Email"));
  await user.click(screen.getByLabelText("Deed · PDF"));
  post.mockResolvedValueOnce(
    response(
      { error: { code: "source_unavailable", message: "", retryable: false, source_number: 2 } },
      409,
    ),
  );
  await user.click(screen.getByText("Preview exact Sources"));
  expect(await screen.findByText("Check Source 2 · Deed")).toBeVisible();
  await user.click(
    await screen.findByRole("button", { name: "Review selection" }),
  );
  expect(screen.getByRole("heading", { name: "Select Sources" })).toHaveFocus();
  await user.click(screen.getByLabelText("Deed · PDF"));
  expect(screen.getByLabelText("Letter · Email")).toBeChecked();
  expect(screen.getByLabelText("Deed · PDF")).not.toBeChecked();
  expect(screen.getByText("Preview exact Sources")).toBeEnabled();
  expect(grantLost).not.toHaveBeenCalled();
});

it("stops checking Workspace after a forbidden request even when the login still has write access", async () => {
  const capabilities = { can_write: true, sign_in_available: true, workspace_discovery: true, workspace_connection: true };
  let checks = 0;
  const fetch = vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => {
    if (url === "/api/access") return Response.json(capabilities);
    if (url === "/api/matter-proposals/discovery/connection") {
      checks++;
      // End a regression loop deterministically.
      if (checks > 1) throw new Error("Repeated connection check");
      return new Response("CSRF token verification failed", { status: 403 });
    }
    throw new Error("Unexpected request");
  });
  window.history.replaceState(null, "", "/app/matter-proposals/new?workspace=connect");
  render(<AccessProvider><Intake /></AccessProvider>);
  const recovery = await screen.findByRole("link", { name: "Sign in again" });
  expect(recovery).toHaveAttribute("href", "/auth/login?next=%2Fapp%2Fmatter-proposals%2Fnew%3Fworkspace%3Dconnect");
  expect(checks).toBe(1);
  expect(fetch.mock.calls.filter(([url]) => url === "/api/access")).toHaveLength(2);
  expect(screen.queryByText("Checking Workspace access…")).toBeNull();
});

it("clears a private preview and offers sign-in after the server forgets the login", async () => {
  const user = userEvent.setup();
  const respond = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status });
  const fetch = vi.spyOn(globalThis, "fetch");
  fetch.mockResolvedValueOnce(
    respond({
      can_write: true,
      sign_in_available: true,
      workspace_discovery: true,
      workspace_connection: true,
    }),
  );
  render(
    <AccessProvider>
      <Intake />
    </AccessProvider>,
  );
  fetch.mockResolvedValueOnce(
    respond({
      connected: true,
      generation: "first",
      account: "pilot@example.test",
      folder: "folder",
      label: "label",
      folder_name: "Alder",
      label_name: "Letters",
    }),
  );
  await user.click(
    await screen.findByRole("radio", { name: "Search Workspace" }),
  );
  fetch.mockResolvedValueOnce(
    respond({
      session: "old",
      view: {
        ...view,
        suggestions: [
          {
            query: "Mara Voss",
            passage: "Mara will circulate the appointment.",
            origin: "same",
            rationale: "An appointment is outstanding.",
          },
        ],
      },
    }),
  );
  await user.click(
    await screen.findByRole("button", { name: "Start private discovery" }),
  );
  await user.click(screen.getByLabelText("Deed · PDF"));
  fetch.mockResolvedValueOnce(
    respond({
      token: "old-preview",
      sources: [
        {
          id: "source_001",
          title: "Appointment",
          text: "Reviewed private text",
        },
      ],
    }),
  );
  await user.click(
    screen.getByRole("button", { name: "Preview exact Sources" }),
  );
  await user.click(screen.getByLabelText(/I approve publishing/));
  expect(screen.getByText("Reviewed private text")).toBeVisible();
  fetch
    .mockResolvedValueOnce(
      respond(
        {
          error: {
            code: "sign_in_required",
            message: "Sign in again.",
            retryable: false,
          },
        },
        401,
      ),
    )
    .mockResolvedValueOnce(
      respond({ can_write: false, sign_in_available: true }),
    );
  fireEvent.focus(window);
  expect(
    await screen.findByRole("link", { name: "Sign in again" }),
  ).toHaveAttribute(
    "href",
    "/auth/login?next=%2Fapp%2Fmatter-proposals%2Fnew%3Fworkspace%3Dconnect",
  );
  expect(screen.getByRole("alert")).toHaveTextContent("Sign in and reconnect Workspace to start a fresh search.");
  expect(screen.queryByLabelText("PDF sources")).toBeNull();
  expect(screen.getByText("Your session has expired")).toBeVisible();
  expect(screen.queryByText("Reviewed private text")).toBeNull();
  expect(
    screen.queryByRole("button", { name: "Search for Mara Voss" }),
  ).toBeNull();
  expect(screen.queryByLabelText("Deed · PDF")).toBeNull();
  expect(screen.queryByLabelText(/I approve publishing/)).toBeNull();
  expect(screen.queryByRole("button", { name: /try again|retry/i })).toBeNull();
});

it("checks the current grant before revealing a draft after a method switch", async () => {
  const user = userEvent.setup();
  const onBusy = vi.fn();
  const connected = {
    connected: true, generation: "one", account: "synthetic@example.test",
    folder: "folder-1", label: "alder-label", folder_name: "Deeds", label_name: "Letters",
  };
  const post = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(Response.json(connected))
    .mockResolvedValueOnce(Response.json({ session: "local", view }));
  const { rerender } = render(<WorkspaceConnection active onBusy={onBusy} />);
  await user.click(await screen.findByText("Start private discovery"));
  await user.click(screen.getByLabelText("Letter · Email"));
  rerender(<WorkspaceConnection active={false} onBusy={onBusy} />);
  let finish!: (response: Response) => void;
  post.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  rerender(<WorkspaceConnection active onBusy={onBusy} />);
  expect(screen.getByText("Checking Workspace access…")).toBeVisible();
  expect(screen.queryByRole("checkbox", { name: "Letter · Email" })).toBeNull();
  await act(async () => finish(Response.json({ ...connected, connected: false, generation: null })));
  expect(screen.getByRole("button", { name: "Reconnect" })).toBeVisible();
  expect(screen.queryByLabelText("Letter · Email")).toBeNull();
});

it("retries a failed connection status read without repeating a discovery action", async () => {
  const fetch = vi
    .spyOn(globalThis, "fetch")
    .mockRejectedValueOnce(new TypeError("Network unavailable"));
  render(<WorkspaceConnection onBusy={vi.fn()} />);
  const retry = await screen.findByRole("button", { name: "Try again" });
  fetch.mockResolvedValueOnce(
    new Response(
      JSON.stringify({
        connected: false,
        account: "pilot@example.test",
        folder_name: "Alder",
        label_name: "Letters",
      }),
    ),
  );
  await userEvent.click(retry);
  expect(
    await screen.findByRole("button", { name: "Continue to Google" }),
  ).toBeEnabled();
  expect(fetch.mock.calls.map(([url]) => url)).toEqual(
    Array(2).fill("/api/matter-proposals/discovery/connection"),
  );
});

it("reports private batch progress and only presents the completed preview for approval", async () => {
  const user = userEvent.setup();
  const files = Array.from({ length: 6 }, (_, index) => ({ id: String(index), title: "File " + index }));
  const search = { ...view, files, returned_messages: [], inspected: [], inspected_titles: {} };
  let finish!: (response: Response) => void;
  const post = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(Response.json({ session: "local", view: search }))
    .mockResolvedValueOnce(Response.json({ continuation: "next", completed: 5, total: 6 }))
    .mockImplementationOnce(() => new Promise<Response>(resolve => { finish = resolve; }));
  render(<WorkspaceDiscovery onBusy={() => {}} />);
  await user.click(screen.getByText("Start private discovery"));
  await user.click(screen.getByText("Select all 6 results"));
  await user.click(screen.getByText("Preview exact Sources"));
  expect(screen.getByText("Prepared 5 of 6 Sources…")).toBeVisible();
  expect(screen.queryByLabelText(/I approve publishing/)).toBeNull();
  expect(post.mock.calls[2][1]?.body).toBe(JSON.stringify({ session: "local", continuation: "next" }));
  await act(async () => finish(Response.json({
    token: "reviewed", sources: files.map(file => ({ ...file, text: file.title + " text" })),
  })));
  expect(screen.getByText("File 5 text")).toBeVisible();
  expect(screen.getByLabelText(/I approve publishing/)).not.toBeChecked();
});
