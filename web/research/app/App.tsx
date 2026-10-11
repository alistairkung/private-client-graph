import { useEffect, useState } from "react";
import type { Capabilities, Proposal } from "../shared/contracts";
import { capabilities } from "../configuration/api";
import { Configuration } from "../configuration/Configuration";
import { Run } from "../configuration/Run";
import { History } from "../history/History";
import { Results } from "../results/Results";
import { HistoricalComparison } from "../results/HistoricalComparison";

import { Sidebar } from "./Sidebar";
import "./workspace.css";

export function App() {
  const [available, setAvailable] = useState<Capabilities | null | undefined>(
    undefined,
  );
  const [capabilityError, setCapabilityError] = useState("");
  const [capabilityRetry, setCapabilityRetry] = useState(0);
  const [draftRevision, setDraftRevision] = useState(0);
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
    "treatment",
    "relationship",
    "outcome",
    "case_outcome",
  ].forEach((key) => historyParams.delete(key));
  historyParams.set("browse", "1");
  const historyLink = `#${historyParams}`;
  const showNew =
    params.has("new") || ((!location || location === "#") && !!available);
  return (
    <>
      <a
        className="skip-workspace"
        href="#workspace"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("workspace")?.focus();
        }}
      >
        Skip to workspace
      </a>
      <Sidebar
        selected={id ?? params.get("plan")}
        executable={!!available}
        refreshKey={id ?? params.get("plan") ?? ""}
        newExperiment={() => {
          setProposal(undefined);
          setDraftRevision((value) => value + 1);
        }}
      />
      <main className="continuous-workspace" id="workspace" tabIndex={-1}>
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
        ) : available && showNew ? (
          <Configuration
            key={`${location}-${draftRevision}`}
            capabilities={available}
            initial={proposal}
            onProposalChange={setProposal}
          />
        ) : available && params.has("plan") ? (
          <Run
            key={params.get("plan")}
            id={params.get("plan")!}
            params={params}
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
