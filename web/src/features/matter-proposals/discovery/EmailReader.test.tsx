import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it } from "vitest";
import { EmailReader, type EmailReading } from "./EmailReader";

const message: EmailReading = {
  state: "ready", title: "Appointment notice", text: "Please review the attached notice.",
  sender: "Mara Voss <mara@example.test>", to: "alice@example.test",
  cc: "cora@example.test", bcc: "leo@example.test",
  sent_at: "2026-01-05T12:00:00+08:00", gmail_timestamp_ms: Date.UTC(2026, 0, 5, 4, 2),
};

it("shows the envelope and distinguishes sent time from Gmail’s separately recorded time", async () => {
  render(<EmailReader reading={message} close={() => {}} />);
  expect(screen.getByRole("dialog", { name: message.title })).toBeVisible();
  for (const [label, address] of [["From", message.sender], ["To", message.to], ["Cc", message.cc], ["Bcc", message.bcc]]) {
    expect(screen.getByText(label).nextElementSibling).toHaveTextContent(address);
  }
  const [sent, recorded] = Array.from(document.querySelectorAll("time"));
  expect(sent).toHaveAttribute("datetime", "2026-01-05T04:00:00.000Z");
  await waitFor(() => expect(sent).toBeVisible());
  expect(recorded).not.toBeVisible();
  fireEvent.click(screen.getByText("Gmail timestamp"));
  await waitFor(() => expect(recorded).toBeVisible());
  expect(recorded).toHaveAttribute("datetime", "2026-01-05T04:02:00.000Z");
});

it("omits undisclosed recipients and labels the timestamp honestly when there is no sent date", async () => {
  render(<EmailReader reading={{ ...message, sender: "", to: "", cc: "", bcc: "", sent_at: null }} close={() => {}} />);
  await waitFor(() => expect(screen.getByText("Sender unavailable")).toBeVisible());
  for (const label of ["To", "Cc", "Bcc", "Sent"]) expect(screen.queryByText(label)).toBeNull();
  expect(screen.getByText("Gmail timestamp").nextElementSibling?.querySelector("time")).toBeVisible();
});
