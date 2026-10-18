import { afterEach, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { mayLeave, navigate, useAppPath, useNavigationLock } from "./navigation";

function Routes({ locked = false }: { locked?: boolean }) {
  const path = useAppPath();
  useNavigationLock(locked);
  return (
    <main id="main" tabIndex={-1}>
      <output>{path}</output>
      <a href="/app/matters/example">Open Matter</a>
      <a href="/auth/login?next=/app">Sign in</a>
      <a href="/">Public landing</a>
    </main>
  );
}
afterEach(() => {
  window.history.replaceState(null, "", "/app");
  vi.restoreAllMocks();
});
it("keeps native links while navigating practitioner routes without a document reload", async () => {
  window.history.replaceState(null, "", "/app");
  vi.spyOn(window, "scrollTo").mockImplementation(() => {});
  render(<Routes />);
  const anchor = screen.getByRole("link", { name: "Open Matter" });
  expect(anchor).toHaveAttribute("href", "/app/matters/example");
  await userEvent.click(anchor);
  await waitFor(() =>
    expect(screen.getByRole("status")).toHaveTextContent(
      "/app/matters/example",
    ),
  );
  expect(document.getElementById("main")).toHaveFocus();
  expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
    "href",
    "/auth/login?next=/app",
  );
});
it("refuses external destinations and authentication routes in client navigation", () => {
  expect(() => navigate("https://example.com/app")).toThrow();
  expect(() => navigate("/auth/login")).toThrow();
});
it("keeps an in-flight submission open while allowing its completed workflow to navigate", async () => {
  window.history.replaceState(null, "", "/app");
  vi.spyOn(window, "scrollTo").mockImplementation(() => {});
  render(<Routes locked />);
  await userEvent.click(screen.getByRole("link", { name: "Open Matter" }));
  expect(window.location.pathname).toBe("/app");
  act(() => navigate("/app/matters/completed"));
  await waitFor(() =>
    expect(screen.getByRole("status")).toHaveTextContent(
      "/app/matters/completed",
    ),
  );
});

it("restores the position of both pages through Back and Forward", async () => {
  window.history.replaceState(null, "", "/app");
  let scroll = 120;
  vi.spyOn(window, "scrollY", "get").mockImplementation(() => scroll);
  vi.spyOn(window, "scrollTo").mockImplementation((...args: unknown[]) => {
    const options = args[0];
    if (
      typeof options === "object" &&
      options &&
      "top" in options &&
      typeof options.top === "number"
    )
      scroll = options.top;
  });
  render(<Routes />);
  expect(window.history.scrollRestoration).toBe("manual");
  await userEvent.click(screen.getByRole("link", { name: "Open Matter" }));
  scroll = 480;
  act(() => window.history.back());
  await waitFor(() =>
    expect(screen.getByRole("status")).toHaveTextContent(/^\/app$/),
  );
  expect(scroll).toBe(120);
  act(() => window.history.forward());
  await waitFor(() =>
    expect(screen.getByRole("status")).toHaveTextContent(
      "/app/matters/example",
    ),
  );
  expect(scroll).toBe(480);
});

it("blocks landing, sign-in and sign-out navigation while a submission is in flight", () => {
  render(<Routes locked />);
  for (const name of ["Public landing", "Sign in"]) {
    const event = new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 });
    screen.getByRole("link", { name }).dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  }
  expect(mayLeave("/app")).toBe(false);
});
