import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen, within, waitFor } from "@testing-library/react";
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
  expect(screen.queryByRole("article")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "View in original Source" }));
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
  fireEvent.click(screen.getByRole("button", { name: "View in original Source" }));
  fireEvent.click(screen.getByRole("button", { name: "Switch locale" }));
  expect(screen.getByRole("article").querySelector("mark")).toHaveTextContent(
    "Bea is the parent of Isaac Ng.",
  );
  expect(screen.getByRole("combobox", { name: "基准案例" })).toHaveValue("heldout_03");
  expect(document.documentElement.lang).toBe("zh-CN");
});
it("inspects retained Source-pair failures even when approved-quote provenance passed", () => {
  render(
    <LocaleProvider>
      <CaseWorkspace cases={snapshot.cases} />
    </LocaleProvider>,
  );
  fireEvent.change(screen.getByLabelText("Benchmark case"), { target: { value: "heldout_04" } });
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
  fireEvent.click(screen.getByRole("button", { name: "View in original Source" }));
  expect(screen.getByRole("article").querySelector("mark")).toHaveTextContent(
    "The beneficiary position was checked again: Keira Chan is a beneficiary of the Maple Family Trust.",
  );
  expect(screen.getByRole("combobox", { name: "Original Source" })).toHaveValue(
    "followup",
  );
  fireEvent.change(screen.getByLabelText("Benchmark case"), { target: { value: "heldout_02" } });
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
  const picker = screen.getByRole("combobox", { name: "基准案例" });
  picker.focus();
  fireEvent.change(picker, { target: { value: "heldout_01" } });
  expect(picker).toHaveFocus();
  expect(screen.getByRole("heading", { name: snapshot.cases[0].name })).not.toHaveFocus();
});
function LocaleSwitch() {
  const { setLocale } = useLocale();
  return <button onClick={() => setLocale("zh-CN")}>Switch locale</button>;
}

it("clears hidden relationship Evidence when the filter or Run changes and returns from Source explicitly", () => {
  render(<LocaleProvider><CaseWorkspace cases={snapshot.cases} /></LocaleProvider>);
  fireEvent.click(screen.getByRole("button", { name: "Inspect the two corrections" }));
  fireEvent.click(screen.getAllByRole("button", { name: /Bea → Beatrice Ng/ })[0]);
  const openSource = screen.getByRole("button", { name: "View in original Source" });
  fireEvent.click(openSource);
  fireEvent.click(screen.getByRole("button", { name: "Back to selected relationship" }));
  expect(openSource).toHaveFocus();
  expect(screen.queryByRole("article")).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Recorded outcome filter"), { target: { value: "errors" } });
  expect(screen.queryByText("Beatrice Ng · settlor_of · Larch Family Trust")).not.toBeInTheDocument();
  expect(screen.getByText("Select a relationship to inspect its Evidence.")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Run A′" }));
  expect(screen.getByRole("region", { name: "Run A′ relationships" })).toHaveTextContent("False negative");
  expect(screen.queryByRole("region", { name: "Run B relationships" })).not.toBeInTheDocument();
});

it("keeps hashes out of quote cards while retaining every exact identifier in a collapsed record disclosure", async () => {
  const { container } = render(<LocaleProvider><CaseWorkspace cases={snapshot.cases} /></LocaleProvider>);
  fireEvent.click(screen.getByRole("button", { name: "Inspect the two corrections" }));
  fireEvent.click(screen.getAllByRole("button", { name: /Bea → Beatrice Ng/ })[0]);
  const resolved = snapshot.cases[2].observations.find(item => item.run_label === "B")!;
  const outcome = resolved.relationships.find(item => item.id === resolved.edits[0].outcome_id)!;
  expect(screen.queryByText(outcome.id)).not.toBeInTheDocument();
  for (const quote of [...outcome.expected, ...outcome.predicted]) {
    expect(container.querySelector(".research-quotes")).not.toHaveTextContent(quote.id);
  }
  fireEvent.click(screen.getByRole("button", { name: "Record identifiers" }));
  const record = screen.getByRole("region", { name: "Record identifiers" });
  await waitFor(() => expect(within(record).getByText(outcome.id)).toBeVisible());
  for (const quote of [...outcome.expected, ...outcome.predicted]) expect(record).toHaveTextContent(quote.id);
});
