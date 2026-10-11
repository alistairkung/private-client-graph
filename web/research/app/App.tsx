import { useEffect, useState } from "react";
import type { Capabilities, Proposal } from "../shared/contracts";
import { capabilities } from "../configuration/api";
import { Configuration } from "../configuration/Configuration";
import { Run } from "../configuration/Run";
import { History } from "../history/History";
import { Results } from "../results/Results";
import { HistoricalComparison } from "../results/HistoricalComparison";

import { Sidebar } from "./Sidebar";
import { LegacyMetadata } from "../workspace/LegacyMetadata";
import { Workspace } from "../workspace/Workspace";
import { CreateExperiment } from "../workspace/CreateExperiment";
import "./workspace.css";
import "../workspace/persistent.css";

export function App() {
  const [available, setAvailable] = useState<Capabilities | null | undefined>(
    undefined,
  );
  const [capabilityError, setCapabilityError] = useState("");
  const [capabilityRetry, setCapabilityRetry] = useState(0);
  const [draftSaving, setDraftSaving] = useState(false);
  const [sidebarRevision, setSidebarRevision] = useState(0);
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem("research-sidebar-collapsed") === "true",
  );
  const [draftRevision] = useState(0);
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
  const workspaceId = params.get("workspace");
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
        selected={workspaceId}
        executable={!!available}
        revision={sidebarRevision}
        saving={draftSaving}
        collapsed={collapsed}
        toggle={() =>
          setCollapsed((value) => {
            localStorage.setItem("research-sidebar-collapsed", String(!value));
            return !value;
          })
        }
      />
      <main
        className={`continuous-workspace ${collapsed ? "sidebar-collapsed" : ""}`}
        id="workspace"
        tabIndex={-1}
      >
        {capabilityError && (
          <p role="alert">
            {capabilityError}{" "}
            <button onClick={() => setCapabilityRetry((value) => value + 1)}>
              Retry capabilities
            </button>
          </p>
        )}
        {workspaceId ? (
          <Workspace
            key={workspaceId}
            id={workspaceId}
            selected={params.get("run")}
            select={(run) => {
              window.location.hash = `workspace=${workspaceId}&run=${run}`;
            }}
            capabilities={available ?? null}
            saving={setDraftSaving}
            changed={() => setSidebarRevision((value) => value + 1)}
          />
        ) : (params.has("new") ||
            params.has("plan") ||
            params.has("legacy-new")) &&
          !available ? (
          <p role="status">
            {available === null
              ? "This composition is read-only. Open experiment history to inspect retained results."
              : "Loading execution capabilities…"}
          </p>
        ) : available && showNew ? (
          <CreateExperiment
            created={(id) => {
              setSidebarRevision((value) => value + 1);
              window.location.hash = `workspace=${id}`;
            }}
          />
        ) : available && params.has("legacy-new") ? (
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
              window.location.hash = "legacy-new=1";
            }}
          />
        ) : id ? (
          <>
            <LegacyMetadata id={id} />
            <Results
              key={id}
              id={id}
              params={params}
              historyLink={historyLink}
              executable={!!available}
            />
          </>
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
