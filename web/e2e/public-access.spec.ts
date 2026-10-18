import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

const evergreen = "/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369";
const pdf = readFileSync(new URL("../../tests/fixtures/synthetic-proposal.pdf", import.meta.url));

test("first anonymous visit has persisted sample content and exact Evidence without sign-in", async ({ page, context }) => {
  const googleRequests: string[] = [];
  page.on("request", request => {
    if (new URL(request.url()).pathname === "/_test/google") googleRequests.push(request.url());
  });
  const access = await context.request.get("/api/access");
  expect(await access.json()).toEqual({ can_write: false, sign_in_available: true });
  await page.goto("/app");
  await expect(page.getByRole("link", { name: /PC\/2026\/0142/ })).toBeVisible();
  await expect(page.locator('.page-heading a[href="/app/matter-proposals/new"]')).toBeVisible();
  await page.getByRole("link", { name: /PC\/2026\/0142/ }).click();
  await page.reload();
  await expect(page).toHaveURL(evergreen);
  await expect(page.getByRole("heading", { name: "Evergreen Family Trust", exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "List", exact: true }).click();
  await page.locator("#relationship-0").click();
  await expect(page.locator(".source-text mark")).toContainText("Alice Chen and David Chen are the parents of Bob Chen");
  expect(googleRequests).toHaveLength(0);
  const csrf = (await context.cookies()).find(cookie => cookie.name === "__Host-pcg-csrf")?.value ?? "";
  expect((await context.request.post("/api/matters", {
    data: {}, headers: { origin: "https://127.0.0.1:4173", "x-csrftoken": csrf },
  })).status()).toBe(401);
});

test("anonymous visitors can open intake, see its requirements and sign in before uploading", async ({ page }) => {
  const writes: string[] = [];
  page.on("request", request => {
    if (request.method() !== "GET" && new URL(request.url()).pathname.startsWith("/api/")) writes.push(request.url());
  });
  await page.goto("/app");
  await page.locator('.page-heading a[href="/app/matter-proposals/new"]').click();
  await expect(page).toHaveURL(/\/app\/matter-proposals\/new$/);
  await page.reload();
  await expect(page.getByRole("heading", { name: "New proposal", exact: true })).toBeVisible();
  await expect(page.getByLabel("External Matter reference", { exact: true })).toBeDisabled();
  await expect(page.getByLabel("PDF sources", { exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Upload and analyse", exact: true })).toBeDisabled();
  await expect(page.getByText(/Saving a proposal publishes every Source title/)).toBeVisible();
  expect(writes).toEqual([]);
  await page.getByRole("link", { name: "Sign in to make changes", exact: true }).click();
  await expect(page).toHaveURL(/\/app\/matter-proposals\/new$/);
  await expect(page.getByLabel("External Matter reference", { exact: true })).toBeEnabled();
  await expect(page.getByLabel("PDF sources", { exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Upload and analyse", exact: true })).toBeDisabled();
});

test("a real pending proposal exposes its full Source publicly while decisions stay protected", async ({ page, context }) => {
  await context.request.get("/auth/login?next=/app");
  const csrf = (await context.cookies()).find(cookie => cookie.name === "__Host-pcg-csrf")!.value;
  const created = await context.request.post("/api/matter-proposals", {
    headers: { origin: "https://127.0.0.1:4173", "x-csrftoken": csrf },
    multipart: {
      external_reference: `PUBLIC/${crypto.randomUUID()}`,
      matter_title: "Fictional public proposal",
      source_title: "Fictional source",
      synthetic_confirmation: "true",
      pdf: { name: "synthetic.pdf", mimeType: "application/pdf", buffer: pdf },
    },
  });
  expect(created.status(), await created.text()).toBe(201);
  const proposal = await created.json();
  await context.clearCookies();
  expect((await context.request.get(`/api/matter-proposals/${proposal.id}`)).status()).toBe(200);
  await page.goto(`/app/matter-proposals/${proposal.id}`);
  await expect(page.getByRole("heading", { name: "Fictional public proposal", exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "List", exact: true }).click();
  await page.locator("#relationship-0").click();
  await expect(page.locator(".source-text")).toHaveText(proposal.state.sources[0].text);
  await expect(page.getByRole("button", { name: "Confirm proposal", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Discard proposal", exact: true })).toHaveCount(0);
  const anonymousCsrf = (await context.cookies()).find(cookie => cookie.name === "__Host-pcg-csrf")?.value ?? "";
  expect((await context.request.delete(`/api/matter-proposals/${proposal.id}`, {
    headers: { origin: "https://127.0.0.1:4173", "x-csrftoken": anonymousCsrf },
  })).status()).toBe(401);
});

test("failed then delayed access checks preserve reading and restore signed-in creation on retry", async ({ page }) => {
  await page.goto("/auth/login?next=/app");
  await expect(page.locator('.page-heading a[href="/app/matter-proposals/new"]')).toBeVisible();
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  let attempts = 0;
  await page.route("**/api/access", async route => {
    attempts += 1;
    if (attempts === 1) return route.abort();
    if (attempts === 2) await pending;
    await route.continue();
  });
  await page.goto("/app");
  await expect(page.getByRole("alert")).toContainText("Sign-in and editing access could not be checked.");
  await expect(page.getByRole("link", { name: /PC\/2026\/0142/ })).toBeVisible();
  await page.getByRole("button", { name: "Retry access check", exact: true }).click();
  await expect(page.getByText("Checking sign-in and editing access…")).toBeVisible();
  await expect(page.getByText(/Sign-in is currently unavailable/)).toHaveCount(0);
  release();
  await expect(page.locator('.page-heading a[href="/app/matter-proposals/new"]')).toBeVisible();
  await page.locator('.page-heading a[href="/app/matter-proposals/new"]').click();
  await expect(page.getByRole("checkbox")).toBeVisible();
});
