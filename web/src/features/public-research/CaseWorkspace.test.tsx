import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import { LocaleProvider, useLocale } from "../../shared/locale";
import { CaseWorkspace } from "./CaseWorkspace";
import type { PublicResearchSnapshot } from "./types";
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
function LocaleSwitch() {
  const { setLocale } = useLocale();
  return <button onClick={() => setLocale("zh-CN")}>Switch locale</button>;
}
