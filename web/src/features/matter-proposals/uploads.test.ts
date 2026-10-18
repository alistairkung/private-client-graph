import { describe, expect, it } from "vitest";
import { addSources, admissionError } from "./uploads";
const file = (name = "note.pdf") =>
  new File(["synthetic"], name, { type: "application/pdf" });
describe("synthetic source admission", () => {
  it("keeps stable IDs and titles when appending/removing sources", () => {
    const first = addSources([], [file()]);
    first[0].title = "Edited source";
    const next = addSources(first, [file("second.pdf")]);
    expect(next[0]).toBe(first[0]);
    expect(next[1].id).not.toBe(first[0].id);
    expect(next.filter((item) => item.id !== first[0].id)[0].id).toBe(
      next[1].id,
    );
  });
  it("enforces source count and combined size before analysis", () => {
    expect(
      admissionError(
        addSources(
          [],
          Array.from({ length: 6 }, () => file()),
        ),
      ),
    ).toBe("Select no more than five PDF documents.");
    expect(
      admissionError([
        {
          id: "s",
          title: "Big",
          pdf: new File([new Uint8Array(10 * 1024 * 1024 + 1)], "big.pdf"),
        },
      ]),
    ).toBe("Select PDFs totalling no more than 10 MiB.");
  });
  it("rejects obvious non-PDF files without asserting backend PDF validity", () => {
    expect(admissionError(addSources([], [file("image.png")]))).toBe(
      "Select a valid text-layer PDF.",
    );
    expect(admissionError(addSources([], [file()]))).toBeUndefined();
  });
});
