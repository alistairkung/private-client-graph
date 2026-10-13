import { useCallback } from "react";
import { comparison } from "../shared/api";
import { useRead } from "../shared/useRead";
import { configuration, number, ReadState } from "../shared/presentation";

export function HistoricalComparison({
  left,
  right,
  historyLink,
}: {
  left: string;
  right: string;
  historyLink: string;
}) {
  const load = useCallback(
    (signal: AbortSignal) => comparison(left, right, signal),
    [left, right],
  );
  const { data, error, retry } = useRead(load);
  const inspect = (id: string, sample: string) =>
    `${historyLink}&${new URLSearchParams({ experiment: id, view: "investigate", sample })}`;
  return (
    <>
      <a href={historyLink}>Back to experiments</a>
      <h1>Historical comparison</h1>
      {!data ? (
        <ReadState error={error} retry={retry} />
      ) : (
        <>
          <p>
            <strong>Left:</strong> {data.left.artifact_path}
            <br />
            <strong>Right:</strong> {data.right.artifact_path}
          </p>
          <h2>Comparison coverage</h2>
          <p>
            {data.matched_inputs} matched frozen inputs · {data.scored_pairs}{" "}
            scored observation pairs
          </p>
          <p>
            Matches require the same case, cohort, Source, ground truth and
            extraction bytes. Delta is right minus left; repetitions are not
            independent extraction samples.
          </p>
          {data.differences.map((item) => (
            <p className="notice" key={item}>
              {item}
            </p>
          ))}
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Matched sample</th>
                  <th>Configuration / repetition</th>
                  <th className="numeric">Left F1</th>
                  <th className="numeric">Right F1</th>
                  <th className="numeric">Delta F1</th>
                  <th>Inspect</th>
                </tr>
              </thead>
              <tbody>
                {data.observations.map((row, index) => (
                  <tr key={index}>
                    <td>
                      {row.left_sample}
                      {row.left_sample !== row.right_sample && (
                        <small>Right: {row.right_sample}</small>
                      )}
                    </td>
                    <td>
                      {configuration(row.configuration)} ·{" "}
                      {row.repetition ?? "baseline"}
                    </td>
                    <td className="numeric">{number(row.left_f1)}</td>
                    <td className="numeric">{number(row.right_f1)}</td>
                    <td className="numeric">
                      {number(row.delta_f1)}
                      {row.reason && <small>{row.reason}</small>}
                    </td>
                    <td>
                      <a href={inspect(left, row.left_sample)}>Inspect left</a>
                      <br />
                      <a href={inspect(right, row.right_sample)}>
                        Inspect right
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h2>Unmatched or incompatible inputs</h2>
          {data.exclusions.length ? (
            <ul>
              {data.exclusions.map((item) => (
                <li key={`${item.side}-${item.sample_id}`}>
                  <a
                    href={inspect(
                      item.side === "left" ? left : right,
                      item.sample_id,
                    )}
                  >
                    {item.side}: {item.sample_id}
                  </a>{" "}
                  — {item.reason}
                </li>
              ))}
            </ul>
          ) : (
            <p>No unmatched inputs.</p>
          )}
        </>
      )}
    </>
  );
}
