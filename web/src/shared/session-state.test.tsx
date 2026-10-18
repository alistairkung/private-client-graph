import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it } from "vitest";
import { clearSessionState, useSessionState } from "./session-state";

afterEach(clearSessionState);
function Draft() {
  const [value, setValue] = useSessionState("draft-test", "");
  return (
    <input
      aria-label="Draft"
      value={value}
      onChange={(event) => setValue(event.target.value)}
    />
  );
}
it("retains in-memory entries across route unmounts and clears them at sign-out", async () => {
  const view = render(<Draft />);
  await userEvent.type(screen.getByRole("textbox"), "Fictional source");
  view.unmount();
  const revisited = render(<Draft />);
  expect(screen.getByRole("textbox")).toHaveValue("Fictional source");
  revisited.unmount();
  clearSessionState();
  render(<Draft />);
  expect(screen.getByRole("textbox")).toHaveValue("");
});
