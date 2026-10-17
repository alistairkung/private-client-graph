import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { LocaleProvider, useLocale } from "./locale";
import { LanguageControl } from "./LanguageControl";
function Example() { const { t } = useLocale(); return <><LanguageControl /><input defaultValue="kept" /><p>{t("Supporting evidence")}</p></>; }
beforeEach(() => {
 const values = new Map<string,string>();
 vi.stubGlobal("localStorage", {getItem:(key:string)=>values.get(key) ?? null,setItem:(key:string,value:string)=>values.set(key,value),clear:()=>values.clear()});
});
it("switches interface language without losing entered state and restores preference", () => {
 const view = render(<LocaleProvider><Example /></LocaleProvider>);
 fireEvent.change(screen.getByRole("textbox"), {target:{value:"review in progress"}});
 fireEvent.click(screen.getByRole("button", {name:"简体中文"}));
 expect(screen.getByText("支持证据")).toBeInTheDocument();
 expect(screen.getByRole("textbox")).toHaveValue("review in progress");
 expect(document.documentElement.lang).toBe("zh-CN");
 view.unmount(); render(<LocaleProvider><Example /></LocaleProvider>);
 expect(screen.getByRole("button", {name:"简体中文"})).toHaveAttribute("aria-pressed","true");
});
it("defaults invalid preferences to English",()=>{window.localStorage.setItem("pcg-locale","fr");render(<LocaleProvider><Example /></LocaleProvider>);expect(screen.getByRole("button", {name:"EN"})).toHaveAttribute("aria-pressed","true");});
it("keeps language switching usable when preference storage is unavailable", () => {
 vi.stubGlobal("localStorage", {getItem:()=>{throw new Error("blocked")},setItem:()=>{throw new Error("blocked")}});
 render(<LocaleProvider><Example /></LocaleProvider>);
 expect(screen.getByRole("button", {name:"EN"})).toHaveAttribute("aria-pressed","true");
 fireEvent.click(screen.getByRole("button", {name:"简体中文"}));
 expect(screen.getByText("支持证据")).toBeInTheDocument();
});
