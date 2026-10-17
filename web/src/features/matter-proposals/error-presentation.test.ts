import { expect, test } from "vitest";
import { proposalFailureMessage } from "./error-presentation";

test("maps provider failures to safe presentation without exposing returned diagnostics", () => {
  expect(proposalFailureMessage({ code: "provider_authorization_unavailable", message: "secret diagnostic", retryable: false }))
    .toBe("Shared provider authorization is unavailable. No analysis was started.");
  expect(proposalFailureMessage({ code: "unexpected", message: "secret diagnostic", retryable: true }))
    .toBe("The request could not be completed. Return to Matters and check the current state before retrying.");
});


test("unknown error codes cannot resolve inherited Object properties", () => {
  expect(proposalFailureMessage({ code: "constructor", message: "internal", retryable: false }))
    .toBe("The request could not be completed. Return to Matters and check the current state before retrying.");
});
