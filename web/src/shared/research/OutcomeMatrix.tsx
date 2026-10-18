import type { ReactNode } from "react";

export interface OutcomeRow {
  id: string;
  label: ReactNode;
  values: ReactNode[];
}

// Cells retain the caller's links or controls, including Workbench outcome navigation.
export function OutcomeMatrix({ caption, headings, rows }: {
  caption: string;
  headings: string[];
  rows: OutcomeRow[];
}) {
  return (
    <table className="outcome-matrix">
      <caption>{caption}</caption>
      <thead>
        <tr>{headings.map(heading => <th key={heading} scope="col">{heading}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map(row => (
          <tr key={row.id}>
            <th scope="row">{row.label}</th>
            {row.values.map((value, index) => <td key={index}>{value}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
