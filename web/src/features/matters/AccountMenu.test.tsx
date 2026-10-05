import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { AccountMenu } from "./AccountMenu";

test("reveals only the authenticated practitioner's secondary actions", async () => {
  const user = userEvent.setup();
  render(<AccountMenu />);

  const trigger = screen.getByRole("button", { name: "Account and application menu" });
  expect(trigger).toHaveAttribute("aria-expanded", "false");
  expect(screen.queryByRole("link", { name: "Public showcase" })).not.toBeInTheDocument();

  await user.click(trigger);

  expect(trigger).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByRole("link", { name: "Public showcase" })).toHaveAttribute("href", "/");
  expect(screen.getByRole("button", { name: "Sign out" })).toBeVisible();
  expect(screen.queryByText(/settings|notifications|profile/i)).not.toBeInTheDocument();
});

test("supports keyboard toggling and returns focus after Escape", async () => {
  const user = userEvent.setup();
  render(<AccountMenu />);
  const trigger = screen.getByRole("button", { name: "Account and application menu" });

  trigger.focus();
  await user.keyboard("{Enter}");
  expect(screen.getByRole("link", { name: "Public showcase" })).toBeVisible();
  expect(trigger).toHaveFocus();

  await user.tab();
  expect(screen.getByRole("link", { name: "Public showcase" })).toHaveFocus();
  await user.keyboard("{Escape}");

  expect(screen.queryByRole("link", { name: "Public showcase" })).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();

  await user.keyboard(" ");
  expect(screen.getByRole("link", { name: "Public showcase" })).toBeVisible();
});

test("closes when the user clicks or moves focus outside the control", async () => {
  const user = userEvent.setup();
  render(<><AccountMenu /><button type="button">Other action</button></>);
  const trigger = screen.getByRole("button", { name: "Account and application menu" });
  const other = screen.getByRole("button", { name: "Other action" });

  await user.click(trigger);
  await user.click(document.body);
  expect(screen.queryByRole("link", { name: "Public showcase" })).not.toBeInTheDocument();

  await user.click(trigger);
  await user.tab();
  await user.tab();
  await user.tab();
  expect(other).toHaveFocus();
  expect(screen.queryByRole("link", { name: "Public showcase" })).not.toBeInTheDocument();
});

test("keeps failed sign-out in the menu and permits a protected retry", async () => {
  let finishRetry!: (response: Response) => void;
  vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-pcg-csrf=logout-csrf");
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(new Response("Unavailable", { status: 503 }))
    .mockImplementationOnce(() => new Promise(resolve => { finishRetry = resolve; }));
  const user = userEvent.setup();
  render(<AccountMenu />);

  await user.click(screen.getByRole("button", { name: "Account and application menu" }));
  await user.click(screen.getByRole("button", { name: "Sign out" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("Could not sign out. Please try again.");
  expect(fetcher.mock.calls[0]).toEqual(["/auth/logout", {
    method: "POST", headers: { "x-csrftoken": "logout-csrf" },
  }]);

  await user.click(screen.getByRole("button", { name: "Sign out" }));
  expect(screen.getByRole("button", { name: "Signing out…" })).toBeDisabled();
  expect(screen.getByRole("link", { name: "Public showcase" })).toBeVisible();
  await user.click(document.body);
  await user.keyboard("{Escape}");
  expect(screen.getByRole("button", { name: "Signing out…" })).toBeDisabled();
  finishRetry(new Response("Unavailable", { status: 503 }));
  expect(await screen.findByRole("button", { name: "Sign out" })).toBeEnabled();
});

test("completes successful sign-out through the supplied navigation boundary", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));
  const signedOut = vi.fn();
  const user = userEvent.setup();
  render(<AccountMenu onSignOut={signedOut} />);

  await user.click(screen.getByRole("button", { name: "Account and application menu" }));
  await user.click(screen.getByRole("button", { name: "Sign out" }));

  await waitFor(() => expect(signedOut).toHaveBeenCalledOnce());
});
