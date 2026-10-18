import type { SourceUpload } from "../shared/contracts";
export function admissionError(sources: SourceUpload[]): string | undefined {
  if (sources.length > 5) return "Select no more than five PDF documents.";
  if (
    sources.reduce((total, source) => total + source.pdf.size, 0) >
    10 * 1024 * 1024
  )
    return "Select PDFs totalling no more than 10 MiB.";
  if (sources.some((source) => !/\.pdf$/i.test(source.pdf.name)))
    return "Select a valid text-layer PDF.";
}
export function addSources(
  previous: SourceUpload[],
  files: File[],
): SourceUpload[] {
  return [
    ...previous,
    ...files.map((pdf) => ({
      id: "source_" + crypto.randomUUID(),
      title: pdf.name.replace(/\.pdf$/i, "").slice(0, 200),
      pdf,
    })),
  ];
}
