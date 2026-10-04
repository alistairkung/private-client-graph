import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const sourcePdf = fileURLToPath(new URL("../../tests/fixtures/synthetic-proposal.pdf", import.meta.url));

test("synthetic PDF becomes a persisted proposal with exact Evidence and can be explicitly discarded", async ({ page, context }, testInfo) => {
  const reference = `E2E/${testInfo.project.name}/${randomUUID()}`;
  const title = "Fictional Example family";
  const creationRequests: string[] = [];
  page.on("request", request => {
    if (request.method() === "POST" && new URL(request.url()).pathname === "/api/matter-proposals") creationRequests.push(request.url());
  });
  await page.goto("/app");
  await page.getByRole("link", { name: "Create Matter", exact: true }).click();
  await expect(page).toHaveURL("/app/matter-proposals/new");
  await expect(page.getByText(/not suitable for real confidential client information/)).toBeVisible();
  await page.getByRole("textbox", { name: "External Matter reference" }).fill(reference);
  await page.getByRole("textbox", { name: "Matter title", exact: true }).fill(title);
  await page.getByRole("textbox", { name: "Authoritative Source title" }).fill("Fictional attendance note");
  await page.getByLabel("PDF", { exact: true }).setInputFiles(sourcePdf);
  const upload = page.getByRole("button", { name: "Upload and analyse" });
  await expect(upload).toBeDisabled();
  await page.getByRole("checkbox", { name: /synthetic or fictional/ }).check();
  await page.screenshot({ path: testInfo.outputPath("create-matter.png"), fullPage: true });
  await upload.click();
  await expect(page).toHaveURL(/\/app\/matter-proposals\/[a-f0-9-]{36}$/);
  const proposalPath = new URL(page.url()).pathname;
  await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Proposed relationships" })).toBeVisible();
  await expect(page.getByText(/no Matter has been created/)).toBeVisible();
  await page.reload();
  await expect(page).toHaveTitle(`${title} · Private Client Graph`);
  const parent = page.getByRole("button", { name: "Alice Example — Parent of — Ben Example", exact: true });
  await parent.focus();
  await parent.press("Enter");
  const highlight = page.locator("mark");
  await expect(highlight).toHaveText("Alice Example is the parent of Ben Example.");
  await expect(highlight).toBeInViewport();
  expect(creationRequests).toHaveLength(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("proposal-workspace.png"), fullPage: true });
  await page.getByRole("link", { name: "Back to Matters" }).click();
  const pending = page.getByRole("region", { name: "Awaiting confirmation" });
  const proposal = pending.getByRole("link", { name: `${reference} ${title}` });
  await expect(proposal).toHaveAttribute("href", proposalPath);
  await expect(page.getByRole("table", { name: "Matters", exact: true })).not.toContainText(reference);
  await proposal.click();
  await page.getByRole("button", { name: "Discard intake", exact: true }).click();
  await page.getByRole("button", { name: "Keep intake" }).click();
  expect((await context.request.get(proposalPath.replace("/app/", "/api/"))).status()).toBe(200);
  await page.getByRole("button", { name: "Discard intake", exact: true }).click();
  await page.getByRole("button", { name: "Permanently discard intake" }).click();
  await expect(page).toHaveURL("/app");
  await expect(pending.getByRole("link", { name: `${reference} ${title}` })).toHaveCount(0);
  expect((await context.request.get(proposalPath.replace("/app/", "/api/"))).status()).toBe(404);
  const matters = await (await context.request.get("/api/matters")).json();
  expect(matters.some((matter: { external_reference: string }) => matter.external_reference === reference)).toBe(false);
  await page.goto(proposalPath);
  await expect(page.getByRole("alert")).toContainText("Matter Proposal not found");
});


test("multiple Trust roles remain independently selectable in the real review canvas", async ({ page }, testInfo) => {
  await page.goto("/app");
  await page.getByRole("link", { name: "Create Matter", exact: true }).click();
  await page.getByRole("textbox", { name: "External Matter reference" }).fill(`Roles/${randomUUID()}`);
  await page.getByRole("textbox", { name: "Matter title", exact: true }).fill("Fictional multiple roles");
  await page.getByRole("textbox", { name: "Authoritative Source title" }).fill("Fictional role note");
  await page.getByLabel("PDF", { exact: true }).setInputFiles(
    fileURLToPath(new URL("../../tests/fixtures/multiple-role-proposal.pdf", import.meta.url)),
  );
  await page.getByRole("checkbox", { name: /synthetic or fictional/ }).check();
  await page.getByRole("button", { name: "Upload and analyse" }).click();
  await expect(page).toHaveURL(/\/app\/matter-proposals\/[a-f0-9-]{36}$/);
  await expect(page.locator(".react-flow__node", { hasText: "Morgan Example" })).toHaveCount(1);
  for (const role of ["Settlor", "Beneficiary", "Trustee"]) {
    const connector = page.getByRole("button", {
      name: `Morgan Example — ${role} of — Fictional Trust`, exact: true,
    });
    await connector.getByText(role, { exact: true }).click();
    await expect(connector).toHaveClass(/selected/);
    await expect(page.locator("mark")).toHaveText(`Morgan Example is ${role.toLowerCase()} of the Fictional Trust.`);
    await connector.focus();
    await connector.press("Enter");
    await expect(page.locator("mark")).toBeInViewport();
  }
  await page.screenshot({ path: testInfo.outputPath("multiple-roles.png"), fullPage: true });
  await page.getByRole("button", { name: "Discard intake", exact: true }).click();
  await page.getByRole("button", { name: "Permanently discard intake" }).click();
  await expect(page).toHaveURL("/app");
});
