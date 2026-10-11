import { test, expect } from "@playwright/test";

test("explicit approval, checkpoint, continuation and exact Evidence with substituted provider", async ({
  page,
}, info) => {
  await page.goto("/#legacy-new=1");
  await page.getByRole("button", { name: /Extract relationships/ }).click();
  await page
    .getByRole("combobox", { name: "Execution mode", exact: true })
    .selectOption("live");
  await page.getByRole("button", { name: /Resolve aliases/ }).click();
  await page
    .getByRole("spinbutton", { name: "Resolver repetitions", exact: true })
    .fill("2");
  // Shared task survives every viewport's experiment; this is an explicit proposed cap, not a reset.
  await page
    .getByRole("spinbutton", {
      name: "Proposed total task call cap",
      exact: true,
    })
    .fill("20");
  await page.getByRole("button", { name: "Customize inputs" }).click();
  await page.getByRole("button", { name: "Clear selection" }).click();
  await page.getByRole("checkbox", { name: /case_03_fixture/ }).check();
  await page.getByRole("button", { name: "Apply inputs" }).click();
  await page.getByRole("button", { name: "Review frozen plan" }).click();
  const approve = page.getByRole("button", {
    name: "Authorize and start",
    exact: true,
  });
  await expect(approve).toBeDisabled();
  const budget = page.getByRole("region", {
    name: "Approve bounded live execution",
  });
  await expect(budget).toContainText("Substituted provider browser test task");
  await expect(budget).toContainText(
    "A call cap is not a guaranteed dollar cap",
  );
  await expect(
    page.getByRole("heading", { name: "Execution · frozen", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(approve).toBeDisabled();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `../.impeccable/review/research-live/approval-${info.project.name}.png`,
    fullPage: true,
  });
  const consent = page.getByRole("checkbox", {
    name: "I approve this task cap and bounded live invocation for the frozen plan.",
  });
  await consent.focus();
  await page.keyboard.press("Space");
  await approve.click();
  await expect(
    page.getByRole("heading", { name: "Execution · stopped", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Execution · stopped", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Review continuation" }).click();
  await expect(
    page.getByRole("button", { name: "Authorize and continue" }),
  ).toBeDisabled();
  await page.screenshot({
    path: `../.impeccable/review/research-live/continuation-${info.project.name}.png`,
    fullPage: true,
  });
  await consent.check();
  await page.getByRole("button", { name: "Authorize and continue" }).click();
  await expect(
    page.getByRole("heading", { name: "Execution · complete", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Relationship evaluation", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Treatment repetition", exact: true })
    .selectOption("generative_full_source-2");
  await page
    .getByRole("link", { name: "Baseline missing: 1", exact: true })
    .click();
  await expect(
    page.getByRole("combobox", { name: "Treatment repetition", exact: true }),
  ).toHaveValue("generative_full_source-2");
  await page.getByRole("link", { name: "Inspect persisted results" }).click();
  await expect(page.locator(".experiment-heading")).toContainText(
    "Live experiment",
  );
  await page.getByRole("link", { name: "Investigate", exact: true }).click();
  await page
    .getByRole("link", { name: "Baseline Missing: 1", exact: true })
    .click();
  await page.locator(".relationship-list a").first().click();
  await expect(
    page.getByText("No predicted relationship", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "View expected in Source" })
    .first()
    .click();
  await expect(
    page
      .getByRole("article", { name: "Frozen Source" })
      .locator("mark")
      .first(),
  ).toBeVisible();
});

test("workspace authorizes before separate start and explicitly continues provisional coverage", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByLabel("Experiment name", { exact: true })
    .fill("Bounded resolver investigation");
  await page
    .getByRole("button", { name: "Create experiment", exact: true })
    .click();
  await page.getByRole("button", { name: "Choose cases" }).click();
  await page.getByRole("button", { name: "Clear selection" }).click();
  await page.getByRole("checkbox", { name: /case_03_fixture/ }).check();
  await page.getByRole("button", { name: "Apply cases" }).click();
  await page.getByRole("button", { name: /Extract relationships/ }).click();
  await page
    .getByRole("combobox", { name: "Execution mode", exact: true })
    .selectOption("live");
  await page.getByRole("button", { name: /Resolve aliases/ }).click();
  await page
    .getByRole("spinbutton", { name: "Resolver repetitions", exact: true })
    .fill("2");
  await page
    .getByRole("spinbutton", { name: "Proposed total task call cap" })
    .fill("20");
  await page.getByRole("button", { name: "Run", exact: true }).click();
  await page.getByRole("button", { name: "Freeze Run", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Authorize invocation" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Start Run", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("checkbox", { name: /I approve this task cap/ }).check();
  await page.getByRole("button", { name: "Authorize invocation" }).click();
  await expect(
    page.getByRole("heading", { name: "Execution · frozen", exact: true }),
  ).toBeVisible();
  const frozen = await (
    await page.request.get(
      `/api/research/v2/experiments/${new URLSearchParams(page.url().split("#")[1]).get("workspace")}/runs`,
    )
  ).json();
  expect(frozen[0].attempts).toHaveLength(0);
  await page.getByRole("button", { name: "Start Run", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Execution · stopped", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".chart-point.provisional")).toHaveCount(1);
  await expect(
    page.getByText("Provisional evaluation", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Review continuation" }).click();
  await page.getByRole("checkbox", { name: /I approve this task cap/ }).check();
  await page.getByRole("button", { name: "Authorize invocation" }).click();
  await page.getByRole("button", { name: "Continue Run", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Execution · complete", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".chart-point")).toHaveCount(1);
  await expect(page.locator(".chart-point.provisional")).toHaveCount(0);
  await page.getByRole("button", { name: "Use as next draft" }).click();
  await page.getByRole("button", { name: "Run", exact: true }).click();
  await page.getByRole("button", { name: "Freeze Run", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Authorize invocation" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Start Run", exact: true }),
  ).toHaveCount(0);
});
