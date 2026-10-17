import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";
import { LocaleProvider } from "../../shared/locale";
import { LanguageControl } from "../../shared/LanguageControl";
import { CreateMatter } from "./CreateMatter";
import { ProposalFailureNotice } from "./ProposalFailureNotice";

beforeEach(() => {
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    clear: () => values.clear(),
  });
});

test("switching language preserves entered identity, Source titles and selected PDFs without requests", async () => {
  window.localStorage.clear();
  const fetcher = vi.spyOn(globalThis, "fetch");
  render(<LocaleProvider><LanguageControl /><CreateMatter onNavigate={vi.fn()} /></LocaleProvider>);
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("External Matter reference"), "Demo/42");
  await user.type(screen.getByLabelText("Matter title"), "Fictional family");
  const files = [new File(["%PDF-test"], "First.pdf", { type: "application/pdf" }), new File(["%PDF-test"], "Second.pdf", { type: "application/pdf" })];
  const picker = screen.getByLabelText<HTMLInputElement>("PDF");
  await user.upload(picker, files);
  await user.clear(screen.getByLabelText("Source 2 title"));
  await user.type(screen.getByLabelText("Source 2 title"), "Unchanged Source title");
  await user.click(screen.getByRole("checkbox"));
  await user.click(screen.getByRole("button", { name: "简体中文" }));
  expect(screen.getByLabelText("外部事项编号")).toHaveValue("Demo/42");
  expect(screen.getByLabelText("事项标题")).toHaveValue("Fictional family");
  expect(screen.getByLabelText("来源 2 标题")).toHaveValue("Unchanged Source title");
  expect(screen.getByLabelText("PDF")).toBe(picker);
  expect(Array.from(picker.files!)).toEqual(files);
  expect(screen.getByRole("button", { name: "上传并分析" })).toBeEnabled();
  await user.click(screen.getByRole("button", { name: "EN" }));
  expect(screen.getByLabelText("Source 2 title")).toHaveValue("Unchanged Source title");
  expect(Array.from(picker.files!)).toEqual(files);
  expect(fetcher).not.toHaveBeenCalled();
});

test("errors use translated safe messages and preserve no server diagnostics", async () => {
  window.localStorage.clear();
  render(<LocaleProvider><LanguageControl /><ProposalFailureNotice error={{ code: "provider_authorization_unavailable", message: "DO NOT DISPLAY INTERNAL DIAGNOSTICS", retryable: false }} /></LocaleProvider>);
  await userEvent.click(screen.getByRole("button", { name: "简体中文" }));
  expect(screen.getByRole("alert")).toHaveTextContent("共享服务调用授权不可用，未启动分析。");
  expect(screen.queryByText(/INTERNAL DIAGNOSTICS/)).not.toBeInTheDocument();
});
