import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { expect, it } from "vitest";
import type { Capabilities, Proposal } from "../shared/contracts";
import { Pipeline } from "./Pipeline";
const capabilities: Capabilities = {
  api_version: "1",
  live_enabled: false,
  live_reason: "Disabled",
  live_task: null,
  inputs: [],
  models: ["deepseek-flash"],
  provider: "Recorded",
  fresh_input_id: "case_03_fixture",
  maximum_extraction_samples: 5,
  maximum_resolver_repetitions: 3,
};
const initial: Proposal = {
  retained_experiment_id: null,
  retained_run_id: null,
  input_ids: ["case_03_fixture"],
  input_mode: "saved",
  execution_mode: "replay",
  resolver: "none",
  extraction_samples: 1,
  resolver_repetitions: 1,
  invocation_cap: 0,
  task_call_cap: 0,
  temperature: null,
  timeout_seconds: 90,
  model: "deepseek-flash",
};
function Draft() {
  const [proposal, setProposal] = useState(initial);
  return (
    <Pipeline
      proposal={proposal}
      capabilities={capabilities}
      update={(changes) => setProposal((p) => ({ ...p, ...changes }))}
    />
  );
}
it("inserts only a recorded resolver, preserves inline edits, and restores the no-op insertion focus", async () => {
  const user = userEvent.setup();
  render(<Draft />);
  const insert = screen.getByRole("button", { name: "Add alias resolution" });
  await user.click(screen.getByRole("button", { name: "Add optional stage" }));
  expect(
    screen.getByRole("button", { name: "Add generative resolver" }),
  ).toHaveFocus();
  await user.keyboard("{Escape}");
  expect(insert).toHaveFocus();
  expect(
    screen.queryByRole("button", { name: "Add generative resolver" }),
  ).not.toBeInTheDocument();
  await user.click(insert);
  await user.click(
    screen.getByRole("button", { name: "Add generative resolver" }),
  );
  expect(
    screen.queryByRole("button", { name: "Add alias resolution" }),
  ).not.toBeInTheDocument();
  const repetitions = screen.getByRole("spinbutton", {
    name: "Resolver repetitions",
  });
  await user.clear(repetitions);
  await user.type(repetitions, "3");
  await user.click(screen.getByRole("button", { name: /Resolve aliases/ }));
  await user.click(screen.getByRole("button", { name: /Resolve aliases/ }));
  expect(
    screen.getByRole("spinbutton", { name: "Resolver repetitions" }),
  ).toHaveValue(3);
  await user.click(
    screen.getByRole("button", { name: /Extract relationships/ }),
  );
  expect(screen.getByRole("combobox", { name: "Execution mode" })).toHaveValue(
    "recorded",
  );
  expect(
    screen.queryByRole("spinbutton", { name: "Resolver repetitions" }),
  ).not.toBeInTheDocument();
  await user.click(
    screen.getByRole("button", { name: "Bypass alias resolution" }),
  );
  expect(
    await screen.findByRole("button", { name: "Add alias resolution" }),
  ).toBeVisible();
  expect(
    screen.queryByRole("button", { name: /Remove.*graph/ }),
  ).not.toBeInTheDocument();
});
it("frozen pipelines expose configuration without mutation controls", async () => {
  render(<Pipeline proposal={{ ...initial, resolver: "generative" }} />);
  expect(
    screen.queryByRole("button", { name: "Bypass alias resolution" }),
  ).not.toBeInTheDocument();
  await userEvent.click(
    screen.getByRole("button", { name: /Resolve aliases/ }),
  );
  expect(
    within(
      screen.getByRole("region", { name: "Resolve aliases settings" }),
    ).getByText(/Frozen configuration · Read-only. No execution/),
  ).toBeVisible();
});
