import type { ChangeEvent } from "react";

export function sourceAdmissionError(files: File[]): string | undefined {
  if (files.length > 5) return "Select no more than five PDF documents.";
  if (files.reduce((total, file) => total + file.size, 0) > 10 * 1024 * 1024) {
    return "Select PDFs totalling no more than 10 MiB.";
  }
}

export function SourceDocuments({ files, titles, onFiles, onTitle }: {
  files: File[]; titles: string[];
  onFiles: (files: File[]) => void;
  onTitle: (index: number, title: string) => void;
}) {
  function selectFiles(event: ChangeEvent<HTMLInputElement>) {
    onFiles(Array.from(event.target.files ?? []));
  }
  const error = sourceAdmissionError(files);
  return <>
    <label>PDF<input required multiple type="file" name="pdf" accept=".pdf,application/pdf"
      onChange={selectFiles} aria-describedby="pdf-admission" /></label>
    <p id="pdf-admission" className="field-guidance">One to five text-layer PDFs, up to 10 MiB combined and 50 pages per PDF. Scanned and encrypted PDFs are unsupported. Combined extracted text may contain up to 100,000 characters.</p>
    {error && <p className="intake-error" role="alert">{error}</p>}
    <ol className="intake-sources" aria-label="Selected Sources">
      {(files.length ? files : [undefined]).map((file, index) => <li key={index}>
        {file && <p className="source-filename">Source {index + 1}: {file.name}</p>}
        <label>{index === 0 ? "Authoritative Source title" : `Source ${index + 1} title`}
          <input required maxLength={200} name={`source_title_${index}`} value={titles[index] ?? ""}
            onChange={event => onTitle(index, event.target.value)} /></label>
      </li>)}
    </ol>
    <p className="field-guidance">Each document keeps its own title and evidence. Documents are analysed together in the order shown. Matching titles are allowed.</p>
  </>;
}
