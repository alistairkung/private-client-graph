import { expect, test } from "@playwright/test";
import { openPublicMenu } from "./public-navigation";

const matterPath = "/app/matters/ff985caf-60c5-4e65-a238-f3c26381c369";

test("persisted Matter opens from ledger and highlights exact Evidence after direct entry and refresh", async ({ page }, testInfo) => {
  const apiRequests: string[] = [];
  page.on("request", request => {
    const path = new URL(request.url()).pathname;
    if (path.startsWith("/api/")) apiRequests.push(path);
  });
  await page.goto("/app");
  await expect(page).toHaveTitle("Matters · Private Client Graph");
  const matter = page.getByRole("link", { name: "PC/2026/0142 Evergreen Family Trust" });
  await expect(matter).toHaveAttribute("href", matterPath);
  await page.screenshot({ path: testInfo.outputPath("matters-register.png"), fullPage: true });
  await matter.focus();
  await matter.press("Enter");
  await expect(page).toHaveURL(matterPath);
  await expect(page.getByRole("heading", { name: "Evergreen Family Trust", exact: true })).toBeVisible();
  await expect(page.getByText("Matter reference: PC/2026/0142")).toBeVisible();
  await page.goto(matterPath);
  await page.reload();
  await expect(page).toHaveTitle("Evergreen Family Trust · Private Client Graph");
  await expect(page.getByRole("img", { name: "Triangular Trust node" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Matters", exact: true })).toHaveAttribute("aria-current", "page");
  const edge = page.getByRole("button", { name: "Alice Chen — Spouse of — David Chen", exact: true });
  await page.getByLabel("Find a relationship").selectOption({ label: "Alice Chen — Spouse of — David Chen" });
  await edge.getByText("Spouse of", { exact: true }).click();
  await expect(edge).toHaveClass(/selected/);
  if (testInfo.project.name === "narrow") {
    const scale = await page.locator(".react-flow__viewport").evaluate(element => new DOMMatrix(getComputedStyle(element).transform).a);
    expect(scale).toBeGreaterThanOrEqual(1);
    const canvas = await page.getByLabel("Relationship graph").boundingBox();
    const label = await edge.boundingBox();
    expect(label!.x).toBeGreaterThanOrEqual(canvas!.x);
    expect(label!.x + label!.width).toBeLessThanOrEqual(canvas!.x + canvas!.width);
  }
  const highlight = page.locator("mark");
  await expect(highlight).toHaveText("Alice Chen confirmed that she and David Chen are spouses.");
  await expect(highlight).toBeInViewport();
  await expect(page.getByRole("button", { name: /Evidence 1/ })).toHaveAttribute("aria-pressed", "true");
  const parent = page.getByRole("button", { name: "Alice Chen — Parent of — Bob Chen", exact: true });
  await parent.focus();
  await parent.press("Enter");
  await expect(parent).toHaveClass(/selected/);
  await expect(edge).not.toHaveClass(/selected/);
  await expect(highlight).toHaveText("Alice Chen confirmed that Alice Chen and David Chen are the parents of Bob Chen.");
  await expect(highlight).toBeInViewport();
  await page.getByRole("link", { name: "View in source" }).click();
  await expect(highlight).toBeFocused();
  await page.getByRole("button", { name: "Back to selected relationship" }).click();
  await expect(parent).toBeFocused();
  await page.getByLabel("Find a relationship").selectOption({ label: "Alice Chen — Spouse of — David Chen" });
  await expect(edge).toHaveClass(/selected/);
  expect(apiRequests).toContain(matterPath.replace("/app/", "/api/"));
  expect(apiRequests.every(path => path.startsWith("/api/matters") || path === "/api/matter-proposals" || path === "/api/access")).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("matter-workspace.png"), fullPage: true });
  const mattersNavigation = page.getByRole("link", { name: "Matters", exact: true });
  await mattersNavigation.focus();
  await mattersNavigation.press("Enter");
  await expect(matter).toBeVisible();
  const accountMenu = page.getByRole("button", { name: "Account and application menu" });
  await accountMenu.focus();
  await accountMenu.press("Enter");
  await expect(accountMenu).toHaveAttribute("aria-expanded", "true");
  const showcaseLink = page.getByRole("link", { name: "Public showcase" });
  const menuBounds = await showcaseLink.locator("..").boundingBox();
  expect(menuBounds).not.toBeNull();
  expect(menuBounds!.x).toBeGreaterThanOrEqual(20);
  expect(menuBounds!.x + menuBounds!.width).toBeLessThanOrEqual(await page.evaluate(() => window.innerWidth - 20));
  await accountMenu.press("Tab");
  await expect(showcaseLink).toBeFocused();
  await showcaseLink.press("Enter");
  await expect(page.getByLabel("Choose a synthetic case")).toBeVisible();
  await openPublicMenu(page);
  await page.getByRole("navigation", { name: "Public showcase" }).getByRole("link", { name: "Practitioner application", exact: true }).click();
  await expect(matter).toBeVisible();
});

test("unknown Matter direct route stays in the practitioner shell", async ({ page }) => {
  await page.goto("/app/matters/00000000-0000-0000-0000-000000000000");
  await expect(page.getByRole("alert")).toContainText("Matter not found");
  await page.getByRole("link", { name: "Back to Matters" }).click();
  await expect(page.getByRole("heading", { name: "Matters", exact: true })).toBeVisible();
});

test("retrying a failed access check preserves public Matter reading and restores signed-in creation", async ({ page }) => {
  await page.goto("/auth/login?next=/app");
  await expect(page.getByRole("link", { name: "Create Matter" })).toBeVisible();
  let releaseAccess!: () => void;
  const delayedAccess = new Promise<void>(resolve => { releaseAccess = resolve; });
  let checks = 0;
  await page.route("**/api/access", async route => {
    checks += 1;
    if (checks === 1) return route.abort();
    if (checks === 2) await delayedAccess;
    await route.continue();
  });
  await page.goto("/app");
  await expect(page.getByRole("alert")).toContainText("Sign-in and editing access could not be checked.");
  const evergreen = page.getByRole("link", { name: "PC/2026/0142 Evergreen Family Trust" });
  await expect(evergreen).toBeVisible();
  await expect(page.getByRole("link", { name: "Create Matter" })).toHaveCount(0);
  await page.getByRole("button", { name: "Retry access check" }).click();
  await expect(page.getByText("Checking sign-in and editing access…")).toBeVisible();
  await expect(page.getByText(/Sign-in is currently unavailable/)).toHaveCount(0);
  await expect(evergreen).toBeVisible();
  releaseAccess();
  await expect(page.getByRole("link", { name: "Create Matter" })).toBeVisible();
  await page.getByRole("link", { name: "Create Matter" }).click();
  await expect(page.getByRole("checkbox", { name: /synthetic or fictional/ })).toBeVisible();
});


test("public direct navigation needs no sign-in and logout removes only write access", async ({ page, context }) => {
  const googleRequests: string[] = [];
  page.on("request", request => {
    if (new URL(request.url()).pathname === "/_test/google") googleRequests.push(request.url());
  });
  expect((await context.request.get("/api/matters")).status()).toBe(200);
  await page.goto(matterPath);
  await expect(page.getByRole("heading", { name: "Evergreen Family Trust", exact: true })).toBeVisible();
  expect(googleRequests).toHaveLength(0);
  await page.reload();
  expect(googleRequests).toHaveLength(0);
  await page.goto("/auth/login?next=" + matterPath);
  await expect(page.getByRole("heading", { name: "Evergreen Family Trust", exact: true })).toBeVisible();
  expect(googleRequests).toHaveLength(1);
  await expect(page.getByText(/not suitable for real confidential client information/)).toBeVisible();
  const session = (await context.cookies()).find(cookie => cookie.name === "__Host-pcg-session")!;
  expect(session.httpOnly).toBe(true);
  expect(session.secure).toBe(true);
  const accountMenu = page.getByRole("button", { name: "Account and application menu" });
  await accountMenu.focus();
  await accountMenu.press("Enter");
  await accountMenu.press("Tab");
  await page.getByRole("link", { name: "Public showcase" }).press("Tab");
  const signOut = page.getByRole("button", { name: "Sign out" });
  await expect(signOut).toBeFocused();
  await signOut.press("Enter");
  await expect(page).toHaveURL("/");
  expect((await context.request.get("/api/matters")).status()).toBe(200);
  await page.goto(matterPath);
  await expect(page.getByRole("heading", { name: "Evergreen Family Trust", exact: true })).toBeVisible();
  expect(googleRequests).toHaveLength(1);
  expect((await (await context.request.get("/api/access")).json()).can_write).toBe(false);
});

for (const failure of ["network", "server"] as const) {
  test(`sign-out ${failure} failure keeps the session and permits retry`, async ({ page, context }) => {
    await page.goto("/auth/login?next=/app");
    await page.getByRole("button", { name: "Account and application menu" }).click();
    const signOut = page.getByRole("button", { name: "Sign out" });
    await expect(signOut).toBeEnabled();
    await page.route("**/auth/logout", async route => {
      if (failure === "network") await route.abort();
      else await route.fulfill({ status: 503, body: "Unavailable" });
    }, { times: 1 });
    await signOut.click();
    await expect(page.getByRole("alert")).toHaveText("Could not sign out. Please try again.");
    await expect(signOut).toBeEnabled();
    expect((await context.request.get("/api/matters")).status()).toBe(200);
    await signOut.click();
    await expect(page).toHaveURL("/");
    expect((await context.request.get("/api/matters")).status()).toBe(200);
  });
}
