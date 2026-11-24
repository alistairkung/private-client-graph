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
  const family = page.getByRole("button", { name: /Family F\b/ });
  await expect(family).toContainText("Identify the current trustee");
  await expect(family).toContainText("Complete proofs");
  await family.press("Enter");
  await expect(page.getByRole("tab", { name: /F0/ })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  const expected = page.getByRole("region", {
    name: "Expected graph",
    exact: true,
  });
  await expected
    .getByRole("button", {
      name: /Morgan Example.*trustee of.*North Example Trust/i,
    })
    .press("Enter");
  const proof = page.getByRole("region", {
    name: "Sufficient Evidence Alternatives",
  });
  await expect(proof.getByText("Quotation differs")).toBeVisible();
  await expect(proof.getByText("Morgan was nominated earlier.")).toBeVisible();
  const member = proof.getByRole("button", {
    name: /Read approved quotation from register/i,
  });
  await member.press("Enter");
  const reader = page.getByRole("region", { name: "Source reader" });
  await expect(reader.locator("mark")).toHaveText(
    "Morgan is the current holder.",
  );
  await reader.getByRole("button", { name: "Close reader" }).press("Enter");
  await expect(member).toBeFocused();
  await proof.getByRole("button", { name: /Alternative 2,/ }).press("Enter");
  await expect(
    proof.getByText("Source missing from this relationship"),
  ).toBeVisible();

  await page.getByRole("tab", { name: /F0/ }).press("ArrowRight");
  await expect(page.getByRole("tab", { name: /F1/ })).toBeFocused();
  await expect(
    page.getByText("Prediction unavailable", { exact: true }).first(),
  ).toBeVisible();
  await expect(expected).toBeVisible();
  await expect(proof).toHaveCount(0);
  const failure = page.getByRole("region", { name: "Unavailable prediction" });
  await failure.getByText(/Retained candidates/).click();
  await expect(
    failure.getByRole("list", { name: "Parsed candidates" }),
  ).toContainText("Invalid quote absent from the Source.");
  await failure.getByText(/Frozen Sources/).click();
  await failure
    .getByRole("combobox", { name: "Source in retained order" })
    .selectOption("1");
  await expect(
    failure.getByRole("region", { name: "Full frozen Source" }),
  ).toContainText("Morgan was nominated earlier.");

  await page.getByRole("button", { name: /Family G\b/ }).press("Enter");
  const switchSide = page.getByRole("button", {
    name: "Predicted",
    exact: true,
  });
  if (await switchSide.isVisible()) await switchSide.click();
  await expect(
    page.getByRole("region", { name: "Predicted graph", exact: true }),
  ).toContainText(/valid empty graph/i);
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(await page.evaluate(() => window.innerWidth + 1));
  await expect(page).toHaveURL(new RegExp(control + "$"));

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
