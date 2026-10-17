import { test, expect } from "@playwright/test";

test("retained fresh outputs become a zero-call saved replay in the same Experiment", async ({ page }) => {
  await page.goto("/");
  const origin = new URL(page.url()).origin;
  const headers = { Origin: origin };
  const workspace = await (await page.request.post("/api/research/v2/experiments", {
    headers, data: { request_id: crypto.randomUUID(), name: "Retained extraction browser control" },
  })).json();
  const configuration = {
    ...workspace.draft.configuration,
    input_ids: ["case_01_fixture"], input_mode: "fresh",
    execution_mode: "recorded", resolver: "none", invocation_cap: 1,
  };
  const draft = await (await page.request.put(`/api/research/v2/experiments/${workspace.id}/draft`, {
    headers, data: { request_id: crypto.randomUUID(), expected_revision: 0, configuration },
  })).json();
  const baseline = await (await page.request.post(`/api/research/v2/experiments/${workspace.id}/runs`, {
    headers, data: { request_id: crypto.randomUUID(), expected_revision: draft.revision },
  })).json();
  const runPath = `/api/research/v2/experiments/${workspace.id}/runs/${baseline.id}`;
  const started = await page.request.post(`${runPath}/start`, {
    headers, data: { request_id: crypto.randomUUID(), plan_digest: baseline.digest },
  });
  expect(started.ok()).toBe(true);
  await expect.poll(async () => (await (await page.request.get(runPath)).json()).lifecycle).toBe("complete");
  const original = await (await page.request.get(runPath)).json();
  await page.goto(`/#workspace=${workspace.id}`);
  await page.getByRole("combobox", { name: "Input origin" }).selectOption(baseline.id);
  await expect(page.getByText(/Using all 1 retained extractions/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Run", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Run", exact: true }).click();
  const review = page.getByRole("dialog", { name: "Review next Run" });
  await expect(review).toContainText("Provider-free replay");
  await expect(review).toContainText("0 new attempts maximum");
  await review.getByRole("button", { name: "Freeze Run", exact: true }).click();
  await page.getByRole("dialog", { name: "Ready to start Run 2", exact: true })
    .getByRole("button", { name: "Start Run", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Run 2 · Execution · complete", exact: true })).toBeVisible();
  const runs = await (await page.request.get(`/api/research/v2/experiments/${workspace.id}/runs`)).json();
  expect(runs[1].attempts).toHaveLength(0);
  expect(runs[1].observations[0].result.sourced_extraction).toEqual(original.observations[0].result.sourced_extraction);
  expect(runs[0].artifact_digest).toEqual(original.artifact_digest);
});
