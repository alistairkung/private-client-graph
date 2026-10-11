import { useEffect, useState } from "react";
import type { Capabilities, Proposal } from "../shared/contracts";
import { capabilities } from "../configuration/api";
import { Configuration } from "../configuration/Configuration";
import { Run } from "../configuration/Run";
import { History } from "../history/History";
import { Results } from "../results/Results";
import { HistoricalComparison } from "../results/HistoricalComparison";

export function App() {
  const [available, setAvailable] = useState<Capabilities | null | undefined>(
    undefined,
  );
  const [capabilityError, setCapabilityError] = useState("");
  const [capabilityRetry, setCapabilityRetry] = useState(0);
  const [proposal, setProposal] = useState<Proposal | undefined>();
  useEffect(() => {
    const controller = new AbortController();
    setCapabilityError("");
    capabilities(controller.signal)
      .then(setAvailable)
      .catch((error) => {
        if (!controller.signal.aborted) setCapabilityError(error.message);
      });
    return () => controller.abort();
  }, [capabilityRetry]);
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
    "plan",
    "new",
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
        <span>
          Local · Synthetic ·{" "}
          {available
            ? available.live_enabled
              ? "Live approval available"
              : "Offline execution"
            : available === null
              ? "Read-only"
              : "Checking capabilities"}
        </span>
        {available && (
          <nav aria-label="Research navigation">
            <a href="#">Experiments</a>
            <a href="#new=1" onClick={() => setProposal(undefined)}>
              New experiment
            </a>
          </nav>
        )}
      </header>
      <main>
        {capabilityError && (
          <p role="alert">
            {capabilityError}{" "}
            <button onClick={() => setCapabilityRetry((value) => value + 1)}>
              Retry capabilities
            </button>
          </p>
        )}
        {(params.has("new") || params.has("plan")) && !available ? (
          <p role="status">
            {available === null
              ? "This composition is read-only. Open experiment history to inspect retained results."
              : "Loading execution capabilities…"}
          </p>
        ) : available && params.has("new") ? (
          <Configuration
            key={location}
            capabilities={available}
            initial={proposal}
          />
        ) : available && params.has("plan") ? (
          <Run
            key={params.get("plan")}
            id={params.get("plan")!}
            edit={(value) => {
              setProposal(value);
              window.location.hash = "new=1";
            }}
          />
        ) : id ? (
          <Results
            key={id}
            id={id}
            params={params}
            historyLink={historyLink}
            executable={!!available}
          />
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
