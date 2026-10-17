import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { LocaleProvider, useLocale } from "../../shared/locale";
import { CaseWorkspace } from "./CaseWorkspace";
import type { PublicResearchSnapshot } from "./types";
// Persist preference within a journey, but never inherit another test's locale.
beforeEach(() => {
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
  });
});
afterEach(() => vi.unstubAllGlobals());

const snapshot: PublicResearchSnapshot = JSON.parse(
  readFileSync(
    resolve(
      import.meta.dirname,
      "../../../../private_client_graph/published/research-results.v1.json",
    ),
    "utf8",
  ),
);
it("opens a recorded correction and links its retained relationship to exact original Source evidence", () => {
  render(
    <LocaleProvider>
      <CaseWorkspace cases={snapshot.cases} />
    </LocaleProvider>,
  );
  expect(
    screen.queryByRole("article", { name: "Source document" }),
  ).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Inspect the two corrections" }),
  );
  fireEvent.click(
    screen.getAllByRole("button", { name: /Bea → Beatrice Ng/ })[0],
  );
  expect(
    screen
      .getByRole("article", { name: "Source document" })
      .querySelector("mark"),
  ).toHaveTextContent("Bea is the settlor of the Larch Family Trust.");
  expect(screen.getByText("Factual interview note")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Recorded outcome filter"), {
    target: { value: "errors" },
  });
  expect(
    within(
      screen.getByRole("region", { name: "Run B relationships" }),
    ).getByText("No recorded relationship errors."),
  ).toBeInTheDocument();
});
it("keeps the selected case, relationship and exact Source highlight when the locale changes", () => {
  render(
    <LocaleProvider>
      <LocaleSwitch />
      <CaseWorkspace cases={snapshot.cases} />
    </LocaleProvider>,
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Inspect the two corrections" }),
  );
  fireEvent.click(
    screen.getAllByRole("button", { name: /Bea → Beatrice Ng/ })[1],
  );
  fireEvent.click(screen.getByRole("button", { name: "Switch locale" }));
  expect(screen.getByRole("article").querySelector("mark")).toHaveTextContent(
    "Bea is the parent of Isaac Ng.",
  );
  expect(screen.getByRole("button", { name: /heldout_03/ })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  expect(document.documentElement.lang).toBe("zh-CN");
});
it("inspects retained Source-pair failures even when approved-quote provenance passed", () => {
  render(
    <LocaleProvider>
      <CaseWorkspace cases={snapshot.cases} />
    </LocaleProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: /heldout_04/ }));
  fireEvent.change(screen.getByLabelText("Recorded outcome filter"), {
    target: { value: "source_attribution_failure" },
  });
  const replay = screen.getByRole("region", { name: "Run A′ relationships" });
  expect(within(replay).getAllByRole("button")).toHaveLength(1);
  fireEvent.click(within(replay).getByRole("button", { name: /Keira Chan/ }));
  expect(
    screen.getByText("Matched relationship; approved-quote check passed", {
      selector: "p",
    }),
  ).toBeInTheDocument();
  const failures = screen.getByRole("region", {
    name: "Recorded Source-pair failures",
  });
  expect(failures).toHaveTextContent("followup");
  expect(failures).toHaveTextContent(
    "The beneficiary position was checked again: Keira Chan is a beneficiary of the Maple Family Trust.",
  );
  fireEvent.click(within(failures).getByRole("button"));
  expect(screen.getByRole("article").querySelector("mark")).toHaveTextContent(
    "The beneficiary position was checked again: Keira Chan is a beneficiary of the Maple Family Trust.",
  );
  expect(screen.getByLabelText("Original Source", { exact: true })).toHaveValue(
    "followup",
  );
  fireEvent.click(screen.getByRole("button", { name: /heldout_02/ }));
  expect(within(replay).getAllByRole("button")).toHaveLength(3);
  fireEvent.click(
    within(replay).getByRole("button", { name: /Grace Wong · beneficiary_of/ }),
  );
  expect(
    screen.getByText("Matched relationship; approved-quote mismatch", {
      selector: "p",
    }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("region", { name: "Recorded Source-pair failures" }),
  ).toHaveTextContent(
    "Grace Wong and Hugo Wong are siblings and are both beneficiaries of the Amber Family Trust.",
  );
});
it("moves deliberate case navigation to the selected heading without stealing focus on locale changes", () => {
  render(
    <LocaleProvider>
      <LocaleSwitch />
      <CaseWorkspace cases={snapshot.cases} />
    </LocaleProvider>,
  );
  expect(
    screen.queryByRole("heading", { name: snapshot.cases[2].name }),
  ).toBeNull();
  const corrections = screen.getByRole("button", {
    name: "Inspect the two corrections",
  });
  fireEvent.click(corrections);
  const heading = screen.getByRole("heading", { name: snapshot.cases[2].name });
  expect(heading).toHaveFocus();
  corrections.focus();
  fireEvent.click(corrections);
  expect(heading).toHaveFocus();
  const localeSwitch = screen.getByRole("button", { name: "Switch locale" });
  localeSwitch.focus();
  fireEvent.click(localeSwitch);
  expect(localeSwitch).toHaveFocus();
  fireEvent.click(screen.getByRole("button", { name: /heldout_01/ }));
  expect(
    screen.getByRole("heading", { name: snapshot.cases[0].name }),
  ).toHaveFocus();
});
function LocaleSwitch() {
  const { setLocale } = useLocale();
  return <button onClick={() => setLocale("zh-CN")}>Switch locale</button>;
}
