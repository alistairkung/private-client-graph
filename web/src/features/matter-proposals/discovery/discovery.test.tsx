import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { candidates, type View } from "./api";
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
  expect(candidates(view, [hits, hits], (id) => "Hit " + id)).toEqual([
    { kind: "email", id: "same", title: "Letter" },
    { kind: "pdf", id: "same", title: "Deed" },
    { kind: "email", id: "new", title: "Hit new" },
  ]);
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
  await user.click(screen.getAllByText("Move up")[1]);
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
  const { WorkspaceConnection } = await import("./WorkspaceConnection");
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
  await user.click(start);
  expect(await screen.findByLabelText("Letter · Email")).toBeVisible();
  post.mockResolvedValueOnce(
    respond(
      { error: { code: "workspace_reconnect", message: "", retryable: false } },
      409,
    ),
  );
  await user.click(screen.getByText("Inspect more original results"));
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
      { error: { code: "source_unavailable", message: "", retryable: false } },
      409,
    ),
  );
  await user.click(screen.getByText("Preview exact Sources"));
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
