import { useEffect, useState } from "react";
import { History } from "../history/History";
import { Results } from "../results/Results";
import { HistoricalComparison } from "../results/HistoricalComparison";

export function App() {
  const [location, setLocation] = useState(window.location.hash);
  useEffect(() => {
    const update = () => setLocation(window.location.hash);
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  const params = new URLSearchParams(location.replace(/^#/, ""));
  const id = params.get("experiment");
  const left = params.get("left"),
    right = params.get("right");
  const historyParams = new URLSearchParams(params);
  [
    "experiment",
    "left",
    "right",
    "view",
    "sample",
    "observation",
    "relationship",
    "outcome",
    "case_outcome",
  ].forEach((key) => historyParams.delete(key));
  const historyLink = `#${historyParams}`;
  return (
    <>
      <header className="research-header">
        <a href="#">
          Private Client Graph <span>/ Research</span>
        </a>
        <span>Local · Synthetic · Read-only</span>
      </header>
      <main>
        {id ? (
          <Results key={id} id={id} params={params} historyLink={historyLink} />
        ) : left && right ? (
          <HistoricalComparison
            left={left}
            right={right}
            historyLink={historyLink}
          />
        ) : (
          <History params={params} />
        )}
      </main>
    </>
  );
}
