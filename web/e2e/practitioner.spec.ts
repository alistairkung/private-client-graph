import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const familyPdf = fileURLToPath(
  new URL("../../tests/fixtures/synthetic-proposal.pdf", import.meta.url),
);
const trustPdf = fileURLToPath(
  new URL("../../tests/fixtures/multiple-role-proposal.pdf", import.meta.url),
);
const evergreen = "/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369";

test.beforeEach(async ({ page }) => {
  await page.goto("/auth/login?next=/app");
  await expect(
    page.getByRole("heading", { name: "Matters", exact: true }),
  ).toBeVisible();
});

async function intake(
  page: import("@playwright/test").Page,
  reference: string,
  files = [familyPdf],
) {
  await page.goto("/app/matter-proposals/new");
  await page.locator('input[name="external_reference"]').fill(reference);
  await page
    .locator('input[name="matter_title"]')
    .fill("Fictional family review");
  await page.locator('input[type="file"]').setInputFiles(files);
  await page.getByRole("checkbox").check();
  await page
    .getByRole("button", { name: "Upload and analyse", exact: true })
    .click();
  await expect(page).toHaveURL(/\/app\/matter-proposals\/[a-f0-9-]+$/);
  await expect(
    page.getByRole("heading", { name: "Fictional family review", exact: true }),
  ).toBeVisible();
}

test("ledger search, direct Matter entry and refresh preserve accepted review", async ({
  page,
}, info) => {
  await page.getByRole("searchbox").fill("PC/2026/0142");
  await page.getByRole("link", { name: /PC\/2026\/0142/ }).click();
  await expect(page).toHaveURL(evergreen);
  await expect(
    page.getByRole("heading", { name: "Evergreen Family Trust", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Evergreen Family Trust", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Current", { exact: true }).first(),
  ).toBeVisible();
  if (info.project.name === "desktop") {
    const label = page
      .locator(".entity-node strong")
      .filter({ hasText: /^Alice Chen$/ });
    const lines = await label.evaluate(
      (element) =>
        element.clientHeight / parseFloat(getComputedStyle(element).lineHeight),
    );
    expect(lines).toBeLessThan(1.1);
  }
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `artifacts/${info.project.name}-workspace.png`,
    fullPage: true,
  });
});

test("keyboard relationship selection locates exact Evidence and restores focus", async ({
  page,
}, info) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(evergreen);
  await page.getByRole("tab", { name: "List", exact: true }).click();
  const relationship = page.locator("#relationship-0");
  await relationship.focus();
  await relationship.press("Enter");
  const evidence = page.locator(".evidence-item").first();
  const quote = await evidence.locator("q").textContent();
  if (info.project.name === "desktop") await evidence.click();
  await expect(page.locator(".source-text mark")).toBeVisible();
  expect(await page.locator(".source-text mark").textContent()).toBe(quote);
  await page.screenshot({
    path: `artifacts/${info.project.name}-evidence.png`,
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Back to relationship", exact: true })
    .click();
  await expect(relationship).toBeFocused();
});

test("single-PDF proposal requires explicit confirmation and reopens as current Matter", async ({
  page,
}, info) => {
  const reference = `NEXT/UI/${info.project.name}/${crypto.randomUUID()}`;
  await intake(page, reference);
  let releaseConfirmation = () => {};
  const confirmationGate = new Promise<void>((resolve) => {
    releaseConfirmation = resolve;
  });
  await page.route("**/api/matters", async (route) => {
    if (route.request().method() === "POST") await confirmationGate;
    await route.continue();
  });
  await page
    .getByRole("button", { name: "Confirm proposal", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await dialog
    .getByRole("button", { name: "Confirm and create Matter", exact: true })
    .click();
  await expect(
    dialog.getByRole("button", { name: "Confirming…", exact: true }),
  ).toBeDisabled();
  await page.goBack();
  await expect(page).toHaveURL(/\/app\/matter-proposals\/[a-f0-9-]+$/);
  await expect(dialog).toBeVisible();
  releaseConfirmation();
  await expect(page).toHaveURL(/\/app\/matters\/[a-f0-9-]+$/);
  const url = page.url();
  await expect(
    page.getByRole("heading", { name: "Fictional family review", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Confirm proposal", exact: true }),
  ).toHaveCount(0);
  await page.goto("/app");
  await page.getByRole("searchbox").fill(reference);
  await page.getByRole("link", { name: new RegExp(reference) }).click();
  await expect(page).toHaveURL(url);
  await page
    .getByRole("link", { name: /Back to Matters$|^Matters$/ })
    .filter({ visible: true })
    .last()
    .click();
  await page
    .getByRole("link", { name: "New proposal", exact: true })
    .filter({ visible: true })
    .last()
    .click();
  await expect(page.locator('input[name="external_reference"]')).toHaveValue(
    "",
  );
  await expect(page.locator('input[name="matter_title"]')).toHaveValue("");
  await expect(page.locator(".source-uploads li")).toHaveCount(0);
});

test("multi-PDF proposal retains each Source and can be explicitly discarded", async ({
  page,
}, info) => {
  const reference = `NEXT/MULTI/${info.project.name}/${crypto.randomUUID()}`;
  await intake(page, reference, [familyPdf, trustPdf]);
  const response = await page.request.get(page.url().replace("/app/", "/api/"));
  const proposal = await response.json();
  expect(proposal.state.sources).toHaveLength(2);
  const secondSource = proposal.state.sources[1].id;
  const relationshipIndex = proposal.state.relationships.findIndex(
    (edge: { evidence_ids: string[] }) =>
      edge.evidence_ids.some((id) =>
        proposal.state.evidence.some(
          (item: { id: string; source_id: string }) =>
            item.id === id && item.source_id === secondSource,
        ),
      ),
  );
  expect(relationshipIndex).toBeGreaterThanOrEqual(0);
  await page.getByRole("tab", { name: "List", exact: true }).click();
  await page.locator(`#relationship-${relationshipIndex}`).click();
  const secondEvidence = proposal.state.relationships[
    relationshipIndex
  ].evidence_ids.find((id: string) =>
    proposal.state.evidence.some(
      (item: { id: string; source_id: string }) =>
        item.id === id && item.source_id === secondSource,
    ),
  );
  const quote = proposal.state.evidence.find(
    (item: { id: string }) => item.id === secondEvidence,
  ).supporting_text;
  if (info.project.name === "desktop")
    await page
      .locator(".evidence-item")
      .filter({ hasText: secondEvidence })
      .click();
  else await page.locator(".source-tabs > button").nth(1).click();
  await expect(page.locator(".source-text mark")).toBeVisible();
  expect(await page.locator(".source-text mark").textContent()).toBe(quote);
  await page.screenshot({
    path: `artifacts/${info.project.name}-proposal.png`,
    fullPage: true,
  });
  if (info.project.name === "phone")
    await page
      .getByRole("button", { name: "Back to relationship", exact: true })
      .click();
  await page
    .getByRole("button", { name: "Discard proposal", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Discard entire proposal", exact: true })
    .click();
  await expect(page).toHaveURL(/\/app$/);
  await page.getByRole("searchbox").fill(reference);
  await expect(
    page.getByRole("link", { name: new RegExp(reference) }),
  ).toHaveCount(0);
});

test("intake keeps user input across language changes and enforces PDF admission", async ({
  page,
}, info) => {
  await page.goto("/app/matter-proposals/new");
  await page.locator('input[name="external_reference"]').fill("NEXT/LOCALE");
  await page.locator('input[name="matter_title"]').fill("Original title");
  await page.locator('input[type="file"]').setInputFiles(familyPdf);
  await page
    .locator('input[name="source_title_0"]')
    .fill("Original Source title");
  if (info.project.name === "phone")
    await page.getByRole("button", { name: "Menu", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Language", exact: true })
    .selectOption("zh-CN");
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
  await expect(page.locator('input[name="external_reference"]')).toHaveValue(
    "NEXT/LOCALE",
  );
  await expect(page.locator('input[name="matter_title"]')).toHaveValue(
    "Original title",
  );
  await expect(page.locator('input[name="source_title_0"]')).toHaveValue(
    "Original Source title",
  );
  await page
    .getByRole("combobox")
    .filter({ visible: true })
    .first()
    .selectOption("en");
  if (info.project.name === "phone")
    await page.getByRole("button", { name: "Menu", exact: true }).click();
  await page.getByRole("checkbox").check();
  await page.screenshot({
    path: `artifacts/${info.project.name}-intake.png`,
    fullPage: true,
  });
  await page.locator('input[type="file"]').setInputFiles({
    name: "notes.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("fictional source"),
  });
  await expect(page.getByRole("alert")).toContainText(
    "Select a valid text-layer PDF.",
  );
  await expect(
    page.getByRole("button", { name: "Upload and analyse", exact: true }),
  ).toBeDisabled();
});

// Deliberate isolated UI error substitutions; successful journeys above use real APIs.
test("duplicate reference links to the existing record without losing form entries", async ({
  page,
}) => {
  await page.route("**/api/matter-proposals", (route) =>
    route.request().method() === "POST"
      ? route.fulfill({
          status: 409,
          json: {
            error: {
              code: "duplicate_reference",
              message: "diagnostic must not render",
              retryable: false,
              existing_resource: {
                resource_kind: "matter",
                resource_id: "ff985caf-60c5-4e65-a238-f3c26381c369",
                location: "/api/matters/ff985caf-60c5-4e65-a238-f3c26381c369",
              },
            },
          },
        })
      : route.continue(),
  );
  await page.goto("/app/matter-proposals/new");
  await page.locator('input[name="external_reference"]').fill("PC/2026/0142");
  await page.locator('input[name="matter_title"]').fill("Preserved title");
  await page.locator('input[type="file"]').setInputFiles(familyPdf);
  await page.getByRole("checkbox").check();
  await page
    .getByRole("button", { name: "Upload and analyse", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("already exists");
  await expect(page.locator('input[name="matter_title"]')).toHaveValue(
    "Preserved title",
  );
  await expect(page.getByText("diagnostic must not render")).toHaveCount(0);
  await page
    .getByRole("link", { name: "Open existing record", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Evergreen Family Trust", exact: true }),
  ).toBeVisible();
});

test("missing Matter has recovery and expired sessions keep reading with sign-in for changes", async ({
  page, context,
}) => {
  await page.goto("/app/matters/00000000-0000-0000-0000-000000000000");
  await expect(
    page.getByRole("heading", { name: "Matter not found", exact: true }),
  ).toBeVisible();
  await context.clearCookies();
  await page.goto("/app");
  await expect(page.getByRole("link", { name: /PC\/2026\/0142/ })).toBeVisible();
  await page.locator('.page-heading a[href="/app/matter-proposals/new"]').click();
  await expect(
    page.getByRole("link", { name: "Sign in to make changes", exact: true }).first(),
  ).toHaveAttribute("href", "/auth/login?next=%2Fapp%2Fmatter-proposals%2Fnew");
  await expect(page.getByRole("button", { name: "Upload and analyse", exact: true })).toBeDisabled();
});

test("fictional prompt and account controls close accessibly; sign out ends the session", async ({
  page,
}, info) => {
  await page.goto("/app/matter-proposals/new");
  const prompt = page.getByRole("button", {
    name: "Need a fictional source?",
    exact: true,
  });
  await prompt.click();
  await expect(page.getByRole("dialog")).toContainText(
    "Create a fictional source",
  );
  await expect(
    page
      .getByRole("dialog")
      .getByRole("button", { name: "Copy prompt", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(prompt).toBeFocused();
  await page
    .locator('input[name="external_reference"]')
    .fill("SYNTHETIC/LOGOUT");
  await page
    .locator('input[name="matter_title"]')
    .fill("Fictional draft to clear");
  await page.locator('input[type="file"]').setInputFiles(familyPdf);
  let unloadPrompts = 0;
  page.on("dialog", async (dialog) => {
    unloadPrompts++;
    await dialog.dismiss();
  });
  if (info.project.name === "phone")
    await page.getByRole("button", { name: "Menu", exact: true }).click();
  const account = page.getByRole("button", {
    name: "Account menu",
    exact: true,
  });
  await account.click();
  await expect(
    page.getByRole("link", { name: "Public showcase", exact: true }),
  ).toHaveAttribute("href", "/");
  await page.keyboard.press("Escape");
  await expect(account).toBeFocused();
  await account.click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(
    page.getByRole("link", { name: "Sign in to make changes", exact: true }).first(),
  ).toBeVisible();
  expect(unloadPrompts).toBe(0);
  await expect(page.locator('input[name="matter_title"]')).toHaveValue("");
  await expect(page.locator('input[name="matter_title"]')).toBeDisabled();
  await expect(page.locator('input[name="external_reference"]')).toHaveValue("");
  await expect(page.locator('input[type="file"]')).toBeDisabled();
  await expect(page.locator('.source-uploads > li')).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Upload and analyse", exact: true })).toBeDisabled();
  expect((await page.request.get("/api/matters")).status()).toBe(200);
});
