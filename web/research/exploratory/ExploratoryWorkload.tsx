import { useState } from "react";
import { ReadState } from "../shared/presentation";
import { useRead } from "../shared/useRead";
import { exploratorySources } from "./api";
import "./exploratory.css";

export function ExploratoryWorkload() {
  const { data, error, retry } = useRead(exploratorySources);
  const [selectedId, setSelectedId] = useState<string>();
  const source =
    data?.sources.find((item) => item.id === selectedId) ?? data?.sources[0];

  return (
    <section className="exploratory-workload">
      <header>
        <h1>Exploratory Scale Workload</h1>
        <p>65 Sources · Unqualified · Unscored · Read-only</p>
        <p className="muted">
          This rehearsal is separate from the admitted Benchmark v3 cohort.
          Inspect the documents in their original order.
        </p>
      </header>
      {data && source ? (
        <>
          <label className="exploratory-source-picker">
            Frozen Source
            <select
              value={source.id}
              onChange={(event) => setSelectedId(event.target.value)}
            >
              {data.sources.map((item, index) => (
                <option key={item.id} value={item.id}>
                  {index + 1}. {item.title}
                </option>
              ))}
            </select>
          </label>
          <article aria-labelledby="exploratory-source-title">
            <h2 id="exploratory-source-title">{source.title}</h2>
            <p className="muted">Source ID {source.id}</p>
            <div className="exploratory-source-text">{source.text}</div>
          </article>
          <details>
            <summary>Workload integrity</summary>
            <dl>
              <dt>Workload ID</dt>
              <dd>{data.manifest.workload_id}</dd>
              <dt>Source file SHA-256</dt>
              <dd>{data.manifest.source_file_sha256}</dd>
            </dl>
          </details>
        </>
      ) : (
        <ReadState error={error} retry={retry} />
      )}
    </section>
  );
}
