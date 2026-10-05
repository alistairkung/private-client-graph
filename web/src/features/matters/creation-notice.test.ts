import { expect, test, vi } from "vitest";
import { consumeMatterCreation, rememberMatterCreation } from "./creation-notice";

test("creation feedback is scoped to the confirmed Matter and consumed only once", () => {
  rememberMatterCreation("/app/matters/created");
  expect(consumeMatterCreation("other")).toBe(false);
  expect(consumeMatterCreation("created")).toBe(true);
  expect(consumeMatterCreation("created")).toBe(false);
});

test("blocked storage cannot prevent confirmation navigation", () => {
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Storage disabled"); });
  expect(() => rememberMatterCreation("/app/matters/created")).not.toThrow();
});
