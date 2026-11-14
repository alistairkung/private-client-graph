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
    await page
      .getByRole("button", { name: "Discover Workspace Sources" })
      .click();
    await page.getByRole("button", { name: "Start private discovery" }).click();
    await expect(page.getByRole("status")).toContainText("5 inspected");
    await page.getByRole("button", { name: "Search for Alice Reed" }).click();
    await page
      .getByRole("button", { name: "Inspect more original results" })
      .click();
    await expect(page.getByRole("blockquote").first()).toHaveText(
      "Mara Voss will circulate the executed appointment separately.",
    );
    await page.getByRole("button", { name: "Search for Mara Voss" }).click();
    await page.getByLabel("Mara Voss appointment · PDF").check();
    await page.getByLabel("Alder Trust correspondence 06 · Email").check();
    await page.getByRole("button", { name: "Move up" }).last().click();
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
