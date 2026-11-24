import { expect, test } from "@playwright/test";

const experiment = "e".repeat(32);
const control = "1".repeat(32);
const treatment = "2".repeat(32);
const reordered = "3".repeat(32);
const workspace = `/api/research/v2/experiments/${experiment}`;

test("read-only import exposes protocol metrics, proof, unavailable and empty graphs", async ({
  page,
  request,
}) => {
  await page.goto(`/#workspace=${experiment}&run=${control}`);
  await expect(
    page.getByRole("heading", { name: /Benchmark v3/, level: 2 }),
  ).toBeVisible();
  await expect(page.getByText(/All-condition F1 0.667/)).toBeVisible();
  await page.getByText("Observations & Evidence", { exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Expected graph", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Predicted graph", exact: true }),
  ).toBeVisible();
  const proof = page.getByRole("region", { name: "Sufficient Evidence Alternatives" });
  await expect(proof.locator("q").filter({ hasText: "Morgan is the current holder." })).toBeVisible();
  await expect(proof.locator("q").filter({ hasText: "The audit confirms Morgan holds the office." })).toBeVisible();
  await expect(proof.getByText(/Wrong quotation on this relationship/)).toBeVisible();
  await expect(proof.getByText(/Source missing from this relationship/)).toBeVisible();
  await proof.getByText("View proof member in Source", { exact: true }).first().click();
  await expect(proof.getByRole("article", { name: "Frozen proof Source" }).locator("mark")).toBeVisible();

  const picker = page
    .getByRole("combobox", { name: /Observation|Condition/ })
    .first();
  await picker.selectOption("F1");
  await expect(
    page.getByText(/Predicted canonical graph unavailable/),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Expected graph", exact: true }),
  ).toBeVisible();
  await picker.selectOption("G0");
  await expect(
    page.getByRole("region", { name: /valid empty graph/i }),
  ).toBeVisible();

  expect(
    (
      await request.post(`${workspace}/runs/${control}/start`, { data: {} })
    ).status(),
  ).toBe(404);
  expect((await request.put(`${workspace}/draft`, { data: {} })).status()).toBe(
    404,
  );
  await expect(
    page.getByRole("button", { name: "Use as next draft" }),
  ).toHaveCount(0);
});

test("compatible imports compare the full roster and changed order withholds deltas", async ({
  page,
  request,
}) => {
  const compared = await request.get(
    `${workspace}/comparison?left=${control}&right=${treatment}`,
  );
  expect(compared.ok()).toBeTruthy();
  const compatible = await compared.json();
  expect(compatible.comparable_scope).toBe(true);
  expect(
    compatible.benchmark.conditions.map(
      (row: { condition: string }) => row.condition,
    ),
  ).toEqual(["F0", "F1", "G0"]);
  expect(compatible.benchmark.conditions[1]).toMatchObject({
    left_outcome: "validation_failure",
    right_outcome: "not_attempted",
    fn: 0,
  });

  await page.goto(`/#workspace=${experiment}&run=${control}`);
  const comparator = page.getByRole("combobox", {
    name: /Compare with (?:verified )?Run/,
  });
  await comparator.selectOption(treatment);
  await expect(
    page.getByRole("heading", { name: /Condition-aligned comparison/ }),
  ).toBeVisible();
  await expect(
    page.getByText(
      /validation failure.*not attempted|not attempted.*validation failure/i,
    ),
  ).toBeVisible();
  await comparator.selectOption(reordered);
  await expect(
    page.getByText(/order of the planned Conditions differs/i),
  ).toBeVisible();
  await expect(page.getByText(/deltas withheld/i)).toBeVisible();
});
