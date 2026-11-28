import { useCallback, useEffect, useState } from "react";
import type { Capabilities, Proposal } from "../shared/contracts";
import { capabilities } from "../configuration/api";
import { Configuration } from "../configuration/Configuration";
import { Run } from "../configuration/Run";
import { History } from "../history/History";
import { Results } from "../results/Results";
import { HistoricalComparison } from "../results/HistoricalComparison";

import { Sidebar } from "./Sidebar";
import { WorkbenchNavigation, type WorkbenchPage } from "./WorkbenchNavigation";
import { ReadState } from "../shared/presentation";
import { useRead } from "../shared/useRead";
import { exploratoryManifest } from "../exploratory/api";
import { ExploratoryWorkload } from "../exploratory/ExploratoryWorkload";
import { LegacyMetadata } from "../workspace/LegacyMetadata";
import { BenchmarkV4Catalogue } from "../workspace/BenchmarkV4Catalogue";
import { benchmarkV4Roster, listWorkspaces } from "../workspace/api";
import { Workspace } from "../workspace/Workspace";
import { CreateExperiment } from "../workspace/CreateExperiment";
import { ExperimentIndex } from "../workspace/ExperimentIndex";
import { NewRunHome } from "../workspace/NewRunHome";
import "./workspace.css";
import "./workbench-home.css";
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
  const { data: benchmark, error: benchmarkError, retry: retryBenchmark } = useRead(benchmarkV4Roster);
  const root = !location || location === "#";
  const showRunHome = params.has("new-run") || (root && !!available);
  const showIndex = params.has("experiments");
  const showBenchmark = params.has("benchmark") || params.has("library") || (root && available === null && !!benchmark);
  const page: WorkbenchPage | undefined = showRunHome ? "run"
    : showIndex ? "experiments"
    : params.has("library") ? "benchmark"
    : params.has("legacy-history") ? "history"
    : undefined;
  const showMasthead = !workspaceId && !!available && !!page;
  const listNeeded = showIndex || (!!available && showRunHome);
  const loadWorkspaces = useCallback((signal: AbortSignal) => listNeeded
    ? listWorkspaces(signal) : Promise.resolve(null), [listNeeded, sidebarRevision]);
  const index = useRead(loadWorkspaces);
  useEffect(() => {
    if (showMasthead) window.scrollTo(0, 0);
  }, [location, showMasthead]);
  const showExploratory = params.get("exploratory") === "1";
  const { data: exploratory } = useRead(exploratoryManifest);
  const id = params.get("experiment");
  const left = params.get("left"),
    right = params.get("right");
  const historyParams = new URLSearchParams(params);
  [
    "plan",
    "exploratory",
    "benchmark",
    "new",
    "new-run",
    "experiments",
    "target",
    "review",
    "library",
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
  const showNew = params.has("new");
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
      {showMasthead && page ? (
        <WorkbenchNavigation page={page} benchmark={!!benchmark} saving={draftSaving} />
      ) : <Sidebar
        selected={workspaceId}
        benchmarkAvailable={!!benchmark}
        benchmarkSelected={showBenchmark}
        exploratoryAvailable={!!exploratory}
        exploratorySelected={showExploratory}
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
      />}
      <main
        className={showMasthead ? "workbench-home" : `continuous-workspace ${collapsed ? "sidebar-collapsed" : ""}`}
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
            openFrozenReview={params.get("review") === "1"}
            select={(run) => {
              window.location.hash = run ? `workspace=${workspaceId}&run=${run}` : `workspace=${workspaceId}`;
            }}
            capabilities={available ?? null}
            benchmark={benchmark}
            saving={setDraftSaving}
            changed={() => setSidebarRevision((value) => value + 1)}
          />
        ) : available && showRunHome ? (
          index.data ? <NewRunHome
            key={params.get("target")}
            items={index.data.items}
            initialExperiment={params.get("target")}
            capabilities={available}
            benchmark={benchmark}
            benchmarkLoading={benchmark === undefined && !benchmarkError}
            saving={setDraftSaving}
            frozen={(experiment, run) => {
              setSidebarRevision(value => value + 1);
              window.location.hash = new URLSearchParams({ workspace: experiment, run, review: "1" }).toString();
            }}
          /> : <ReadState error={index.error} retry={index.retry} />
        ) : showIndex ? (
          index.data ? <ExperimentIndex items={index.data.items} executable={!!available} />
            : <ReadState error={index.error} retry={index.retry} />
        ) : root && available === undefined ? (
          capabilityError ? null : <p role="status">Loading Workbench…</p>
        ) : showBenchmark ? (
          benchmark ? <BenchmarkV4Catalogue roster={benchmark} executable={!!available} /> :
            <p role="status">
              {benchmarkError ?? "Benchmark v4 custody is unavailable."}{" "}
              <button onClick={retryBenchmark}>Retry roster</button>
            </p>
        ) : showExploratory ? (
          <ExploratoryWorkload />
        ) : (params.has("new-run") ||
            params.has("new") ||
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
