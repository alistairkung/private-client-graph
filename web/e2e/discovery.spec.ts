import { expect, test } from "@playwright/test";

// Private search responses and review tokens must stay out of recorded traces.
test.use({ trace: "off", screenshot: "off", video: "off" });

test("sixth original email leads to an approved PDF and publicly reopened Evidence", async ({
  page,
  browser,
}, info) => {
  const reference = "ALDER/" + info.project.name + "/" + crypto.randomUUID();
  const reader = await browser.newContext({
    ignoreHTTPSErrors: true,
    baseURL: "https://127.0.0.1:4173",
  });
  try {
    await page.goto("/auth/login?next=/app/matter-proposals/new");
    const upload = page.getByRole("radio", { name: "Upload PDFs" });
    const workspace = page.getByRole("radio", { name: "Search Workspace" });
    await expect(upload).toBeChecked();
    await page.getByLabel("External Matter reference", { exact: true }).fill(reference);
    await upload.focus();
    await page.keyboard.press("ArrowRight");
    await expect(workspace).toBeChecked();
    await workspace.press("ArrowLeft");
    await expect(upload).toBeChecked();
    await expect(page.getByLabel("External Matter reference", { exact: true })).toHaveValue(reference);
    await workspace.check();
    await page.getByRole("button", { name: "Start private discovery" }).click();
    await expect(page.getByRole("status")).toContainText("5 inspected");
    await expect(page.getByText("Checked 5 of 5 emails for leads.")).toBeVisible();
    await expect(page.getByText("More matches may be available.")).toBeVisible();
    await page.getByRole("button", { name: "Search for Alice Reed" }).click();
    const uninspected = page.getByRole("button", { name: "Read Uninspected email 6" });
    await uninspected.click();
    const email = page.getByRole("dialog", { name: "Alice Reed dispatch" });
    await expect(email).toContainText("Cora Patel will circulate the signed deed.");
    await page.keyboard.press("Escape");
    await expect(email).toHaveCount(0);
    await expect(uninspected).toBeFocused();
    await expect(page.getByRole("button", { name: "Preview exact Sources" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Search for Mara Voss" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Search for Cora Patel" })).toHaveCount(0);
    await page
      .getByRole("button", { name: "Check more results" })
      .click();
    await expect(page.getByRole("blockquote").first()).toHaveText(
      "Mara Voss will circulate the executed appointment separately.",
    );
    await page.getByRole("button", { name: "Search for Mara Voss" }).click();
    await page.getByLabel("Mara Voss appointment · PDF").check();
    await page.getByLabel("Alder Trust correspondence 06 · Email").check();
    await page.getByRole("button", { name: "Move Alder Trust correspondence 06 up" }).last().click();
    await page.getByRole("button", { name: "Preview exact Sources" }).click();
    await expect(page.locator(".discovery article pre").nth(1)).toHaveText(
      "Alice Example is the parent of Ben Example.",
    );
    const preview = await page
      .locator(".discovery article pre")
      .allTextContents();
    await page.getByLabel("External Matter reference").fill(reference);
    await page.getByLabel("Matter title").fill("Alder Trust review");
    await expect(
      page.getByRole("button", { name: "Create public proposal" }),
    ).toBeDisabled();
    const listed = await (
      await reader.request.get("/api/matter-proposals")
    ).json();
    expect(
      listed.some(
        (p: { external_reference: string }) =>
          p.external_reference === reference,
      ),
    ).toBe(false);
    await page.getByLabel(/I approve publishing/).check();
    await page.getByRole("button", { name: "Create public proposal" }).click();
    await expect(page).toHaveURL(/\/app\/matter-proposals\/[a-f0-9-]+$/);
    const proposal = await (
      await reader.request.get(page.url().replace("/app/", "/api/"))
    ).json();
    expect(proposal.state.sources).toEqual([
      {
        id: "source_001",
        title: "Alder Trust correspondence 06",
        text: preview[0],
      },
      { id: "source_002", title: "Mara Voss appointment", text: preview[1] },
    ]);
    expect(proposal.state.evidence[0]).toMatchObject({
      source_id: "source_002",
      supporting_text: preview[1],
    });
    expect(JSON.stringify(proposal)).not.toMatch(
      /folder-1|alder-label|signed notice|synthetic@example|shortlist/,
    );
    await page
      .getByRole("button", { name: "Confirm proposal", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Confirm and create Matter" })
      .click();
    await expect(page).toHaveURL(/\/app\/matters\/[a-f0-9-]+$/);
    const reopened = await reader.newPage();
    await reopened.goto(page.url());
    await expect(
      reopened.getByRole("heading", { name: "Alder Trust review" }),
    ).toBeVisible();
    await reopened.getByRole("tab", { name: "List", exact: true }).click();
    await reopened.locator("#relationship-0").click();
    await expect(reopened.locator(".source-text mark")).toHaveText(preview[1]);
    await expect(
      reopened.locator(".source-tabs button[aria-pressed=true]"),
    ).toContainText("Mara Voss appointment");
    const matter = await (
      await reader.request.get(page.url().replace("/app/", "/api/"))
    ).json();
    expect(matter.state.sources).toEqual(proposal.state.sources);
    expect(matter.state.evidence).toEqual(proposal.state.evidence);
  } finally {
    await reader.close();
  }
});

test("inline reconnection after expiry opens a fresh search", async ({
  page,
}) => {
  let generation = 0;
  let searches = 0;
  const root = "**/api/matter-proposals/discovery/";
  await page.clock.install();
  await page.route("**/api/access", async (route) => {
    const response = await route.fetch();
    await route.fulfill({
      response,
      json: { ...(await response.json()), workspace_connection: true },
    });
  });
  await page.route(root + "connect", async (route) => {
    generation++;
    await route.fulfill({
      json: { url: "/app/matter-proposals/new?workspace=ready" },
    });
  });
  await page.route(root + "connection", async (route) => {
    const now = await page.evaluate(() => Date.now());
    await route.fulfill({
      json: {
        connected: generation > 0,
        generation: String(generation),
        expires: generation ? now / 1000 + 300 : null,
        account: "synthetic@example.test",
        label: "alder-label",
        folder: "folder-1",
        label_name: "Alder correspondence",
        folder_name: "Alder Trust",
      },
    });
  });
  page.on("request", (request) => {
    if (request.url().endsWith("/discovery/start")) searches++;
  });

  await page.goto("/auth/login?next=/app/matter-proposals/new");
  await page
    .getByRole("radio", { name: "Search Workspace" })
    .click();
  const connect = page.getByRole("button", { name: "Continue to Google" });
  await expect(connect).toBeVisible();
  await expect(page.getByRole("radio", { name: "Search Workspace" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(connect).toBeFocused();
  await connect.press("Enter");
  await expect(
    page.getByRole("heading", { name: "Workspace connected" }),
  ).toBeFocused();
  expect(searches).toBe(0);
  await page.getByRole("button", { name: "Start private discovery" }).click();
  const deed = page.getByRole("checkbox", { name: /· PDF/ }).first();
  await deed.check();
  await page.getByRole("button", { name: "Preview exact Sources" }).click();
  await expect(page.getByLabel(/I approve publishing/)).toBeVisible();

  await page.clock.fastForward(301_000);
  const reconnect = page.getByRole("button", {
    name: "Reconnect",
    exact: true,
  });
  await expect(reconnect).toBeVisible();
  await expect(page.getByLabel(/I approve publishing/)).toHaveCount(0);
  await reconnect.click();
  await expect(
    page.getByRole("button", { name: "Start private discovery" }),
  ).toBeEnabled();
  await expect(deed).toHaveCount(0);
  expect(searches).toBe(1);
});
