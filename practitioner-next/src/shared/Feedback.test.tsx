import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ErrorNotice } from "./Feedback";
import { RequestFailure } from "./api";
describe("safe and actionable failures", () => {
  it("shows a safe mapped failure and actual duplicate resource link without server diagnostics", () => {
    render(
      <ErrorNotice
        error={
          new RequestFailure(409, {
            code: "duplicate_reference",
            message: "provider-secret-diagnostic",
            retryable: false,
            existing_resource: {
              resource_kind: "matter",
              resource_id: "one",
              location: "https://untrusted.invalid",
            },
          })
        }
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "This external Matter reference already exists.",
    );
    expect(screen.queryByText("provider-secret-diagnostic")).toBeNull();
    expect(
      screen.getByRole("link", { name: "Open existing record" }),
    ).toHaveAttribute("href", "/app/matters/one");
  });
  it("requires checking the current state for an unknown mutation outcome", () => {
    render(
      <ErrorNotice
        error={
          new RequestFailure(502, {
            code: "outcome_unknown",
            message: "",
            retryable: false,
            outcome_unknown: true,
          })
        }
        retry={() => {}}
      />,
    );
    expect(screen.getByRole("link", { name: "Check Matters" })).toHaveAttribute(
      "href",
      "/app",
    );
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
  });
  it("provides an OIDC login link with the current app route on 401", () => {
    render(<ErrorNotice error={new RequestFailure(401)} />);
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/auth/login?next=" + encodeURIComponent(window.location.pathname),
    );
  });
});
