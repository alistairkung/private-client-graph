import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ViewSwitch } from "../shared/ViewSwitch";
import { useSessionState } from "../shared/session-state";
import { getReview, RequestFailure } from "../shared/api";
import type { ReviewRecord } from "../shared/contracts";
import { ErrorNotice, Loading, NotFound } from "../shared/Feedback";
import { useLocale } from "../shared/locale";
import { Icon } from "../shared/Icon";
import { GraphDrawing } from "./GraphDrawing";
import { relationshipStatement, reviewState } from "./presentation";
import { SourceReader } from "./SourceReader";
import { RelationshipList } from "./RelationshipList";
import { EvidenceList } from "./EvidenceList";
import { decisionIsBlocked, ProposalDecision } from "./ProposalDecision";
import "./review.css";

export function ReviewPage({
  kind,
  id,
}: {
  kind: "matters" | "matter-proposals";
  id: string;
}) {
  const [record, setRecord] = useState<ReviewRecord>();
  const [error, setError] = useState<unknown>();
  const [attempt, setAttempt] = useState(0);
  const { t } = useLocale();
  useEffect(() => {
    let active = true;
    setRecord(undefined);
    setError(undefined);
    getReview(kind, id)
      .then((data) => {
        if (active) setRecord(data);
      })
      .catch((failure) => {
        if (active) setError(failure);
      });
    return () => {
      active = false;
    };
  }, [kind, id, attempt]);
  useEffect(() => {
    if (record)
      document.title =
        (record.matter_title ?? record.title) +
        " | " +
        t(kind === "matters" ? "Current Matter" : "Matter Proposal") +
        " | Private Client Graph";
  }, [record, kind, t]);
  if (error instanceof RequestFailure && error.status === 404)
    return <NotFound proposal={kind === "matter-proposals"} />;
  if (error)
    return (
      <div className="page">
        <ErrorNotice error={error} retry={() => setAttempt(attempt + 1)} />
      </div>
    );
  if (!record)
    return (
      <div className="page">
        <Loading />
      </div>
    );
  return (
    <Workspace
      key={id}
      record={record}
      proposal={kind === "matter-proposals"}
    />
  );
}
function Workspace({
  record,
  proposal,
}: {
  record: ReviewRecord;
  proposal: boolean;
}) {
  const { t } = useLocale();
  const reduced = useReducedMotion();
  const state = useRef(reviewState(record)).current;
  const memoryKey =
    "review:" + (proposal ? "proposal:" : "matter:") + record.id;
  const [narrow, setNarrow] = useState(() => window.innerWidth <= 900);
  useEffect(() => {
    if (!window.matchMedia) return;
    const media = window.matchMedia("(max-width: 900px)");
    const update = () => setNarrow(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  const [sourceJump, setSourceJump] = useState(0);
  const [selected, setSelected] = useSessionState<number | null>(
    memoryKey + ":selected",
    null,
  );
  const [entity, setEntity] = useSessionState<string | null>(
    memoryKey + ":entity",
    null,
  );
  const [evidenceId, setEvidenceId] = useSessionState<string | null>(
    memoryKey + ":evidence",
    null,
  );
  const [sourceId, setSourceId] = useSessionState<string | null>(
    memoryKey + ":source",
    state.sources[0]?.id ?? null,
  );
  const [tab, setTab] = useSessionState<"relationships" | "sources">(
    memoryKey + ":tab",
    "relationships",
  );
  const [view, setView] = useSessionState<"graph" | "list">(
    memoryKey + ":view",
    () => (window.innerWidth <= 900 ? "list" : "graph"),
  );
  const [decision, setDecision] = useState<"confirm" | "discard">();
  const [decisionError, setDecisionError] = useState<unknown>();
  const decisionBlocked = decisionIsBlocked(decisionError);
  const [selectionView, setSelectionView] = useSessionState<"graph" | "list">(
    memoryKey + ":selection-view",
    view,
  );
  const [focusRequest, setFocusRequest] = useState<{
    index: number;
    view: "graph" | "list";
  }>();
  const relationship =
    selected === null ? undefined : state.relationships[selected];
  const evidence = evidenceId
    ? state.evidence.find((item) => item.id === evidenceId)
    : undefined;
  const statement = relationship
    ? relationshipStatement(state, relationship, t)
    : undefined;
  useEffect(() => {
    if (!focusRequest || tab !== "relationships") return;
    return restoreRelationshipFocus(focusRequest);
  }, [focusRequest, tab]);
  function selectRelationship(index: number) {
    const edge = state.relationships[index];
    const item = state.evidence.find(
      (item) => item.id === edge.evidence_ids[0],
    );
    setSelected(index);
    setEntity(null);
    setEvidenceId(item?.id ?? null);
    setSourceId(item?.source_id ?? null);
    setSelectionView(view);
    setFocusRequest(undefined);
  }
  function selectEvidence(id: string, jump: boolean) {
    const item = state.evidence.find((item) => item.id === id);
    setEvidenceId(id);
    setSourceId(item?.source_id ?? null);
    if (jump) openSource();
  }
  function openSource() {
    setTab("sources");
    setSourceJump((previous) => previous + 1);
  }
  function returnToRelationship() {
    setTab("relationships");
    if (selected === null) return;
    setView(selectionView);
    setFocusRequest({ index: selected, view: selectionView });
  }
  return (
    <div className="review-page">
      <header className="matter-heading">
        <div className="matter-identity">
          <a className="back-link" href="/app">
            {t("Back to Matters")}
          </a>
          <div className="matter-reference">
            {record.external_reference}
            <span className={"status " + (!proposal ? "current" : "")}>
              {t(proposal ? "Proposal" : "Current")}
            </span>
          </div>
          <h1>{record.matter_title ?? record.title}</h1>
        </div>
        {proposal && (
          <div className="proposal-actions">
            <button
              className="button"
              disabled={decisionBlocked}
              onClick={() => setDecision("discard")}
            >
              {t("Discard proposal")}
            </button>
            <button
              className="button primary"
              disabled={decisionBlocked}
              onClick={() => setDecision("confirm")}
            >
              {t("Confirm proposal")}
            </button>
          </div>
        )}
      </header>
      {proposal && (
        <div className="proposal-notice">
          {t(
            "Machine-proposed relationships. Review the Evidence before confirming the complete proposal.",
          )}
        </div>
      )}
      {decisionError !== undefined && !decision && (
        <div className="proposal-decision-error">
          <ErrorNotice error={decisionError} />
          {decisionBlocked &&
            !(
              decisionError instanceof RequestFailure &&
              decisionError.detail?.outcome_unknown
            ) && (
              <a className="back-link" href="/app">
                {t("Check Matters")}
              </a>
            )}
        </div>
      )}
      <div
        className="mobile-workspace-tabs"
        role="navigation"
        aria-label={t("Review workspace")}
      >
        <button
          aria-pressed={tab === "relationships"}
          aria-controls="relationships-panel"
          onClick={() => setTab("relationships")}
        >
          {t("Relationships")}
        </button>
        <button
          aria-pressed={tab === "sources"}
          aria-controls="source-panel"
          onClick={() => setTab("sources")}
        >
          {t("Sources")}
        </button>
      </div>
      <div className={"review-grid active-" + tab}>
        <section
          className="relationships-panel"
          id="relationships-panel"
          aria-hidden={narrow && tab !== "relationships"}
          inert={narrow && tab !== "relationships"}
        >
          <header className="panel-toolbar">
            <div>
              <h2>{t("Relationships")}</h2>
              <span>
                {t("{entities} entities · {relationships} relationships", {
                  entities: state.entities.length,
                  relationships: state.relationships.length,
                })}
              </span>
            </div>
            <ViewSwitch
              value={view}
              onChange={setView}
              id="review-view"
              label={t("Relationship view")}
              options={[
                {
                  value: "graph",
                  label: t("Graph"),
                  controls: "graph-view-panel",
                },
                {
                  value: "list",
                  label: t("List"),
                  controls: "list-view-panel",
                },
              ]}
            />
          </header>
          <div className="review-view-stack">
            {!state.relationships.length ? (
              <div className="empty graph-empty">
                <h3>{t("No relationships returned")}</h3>
                <p>
                  {t(
                    "The returned graph contains no relationships to inspect.",
                  )}
                </p>
              </div>
            ) : (
              <>
                <div
                  id="graph-view-panel"
                  role="tabpanel"
                  aria-labelledby="review-view-graph"
                  aria-hidden={view !== "graph"}
                  inert={view !== "graph"}
                  className={
                    "review-mode " + (view === "graph" ? "active" : "")
                  }
                >
                  <GraphDrawing
                    state={state}
                    selected={selected}
                    selectedEntity={entity}
                    onSelect={selectRelationship}
                    onEntity={(id) => {
                      setEntity(id);
                      setSelected(null);
                      setEvidenceId(null);
                    }}
                    memoryKey={memoryKey}
                  />
                </div>
                <div
                  id="list-view-panel"
                  role="tabpanel"
                  aria-labelledby="review-view-list"
                  aria-hidden={view !== "list"}
                  inert={view !== "list"}
                  className={"review-mode " + (view === "list" ? "active" : "")}
                >
                  <RelationshipList
                    state={state}
                    selected={selected}
                    entity={entity}
                    onSelect={selectRelationship}
                    onClear={() => setEntity(null)}
                    memoryKey={memoryKey}
                  />
                </div>
              </>
            )}
          </div>
          {entity && (
            <div className="entity-inspector">
              <h3>{state.entities.find((item) => item.id === entity)?.name}</h3>
              <p>{t("Explore the returned relationships for this entity.")}</p>
              <button onClick={() => setView("list")}>
                {t("View connected relationships")}
              </button>
            </div>
          )}
          <section
            className="evidence-inspector"
            aria-labelledby="evidence-heading"
          >
            <div className="inspector-title">
              <h2 id="evidence-heading" tabIndex={-1}>
                {t("Evidence")}
              </h2>
              {relationship && (
                <button className="text-button" onClick={openSource}>
                  {t("Inspect in source")}
                </button>
              )}
            </div>
            <motion.div
              className="inspector-body"
              key={selected ?? "empty"}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: reduced ? 0.06 : 0.12 }}
            >
              {relationship ? (
                <>
                  <h3 className="relationship-statement">{statement}</h3>
                  <EvidenceList
                    state={state}
                    relationship={relationship}
                    evidenceId={evidenceId}
                    onSelect={(id) => selectEvidence(id, true)}
                  />
                  {relationship.evidence_ids.length === 0 && (
                    <p>
                      {t("No Evidence was returned for this relationship.")}
                    </p>
                  )}
                </>
              ) : (
                <div className="inspector-empty">
                  <Icon name="file" />
                  <p>
                    {t(
                      "Select a relationship to read its supporting Evidence.",
                    )}
                  </p>
                  <button
                    className="text-button"
                    onClick={() => setView("list")}
                  >
                    {t("Browse relationship list")}
                  </button>
                </div>
              )}
            </motion.div>
          </section>
        </section>
        <div
          id="source-panel"
          className="source-column"
          aria-hidden={narrow && tab !== "sources"}
          inert={narrow && tab !== "sources"}
        >
          <SourceReader
            sources={state.sources}
            sourceId={sourceId}
            evidence={evidence}
            onSource={setSourceId}
            onReturn={returnToRelationship}
            jumpRequest={sourceJump}
            statement={statement}
            active={tab === "sources" || !narrow}
            memoryKey={memoryKey}
          />
        </div>
      </div>
      <AnimatePresence>
        {decision && (
          <ProposalDecision
            decision={decision}
            record={record}
            state={state}
            error={decisionError}
            blocked={decisionBlocked}
            onError={setDecisionError}
            onClose={() => setDecision(undefined)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function restoreRelationshipFocus(request: {
  index: number;
  view: "graph" | "list";
}) {
  const panel = document.getElementById("relationships-panel");
  if (!panel) return;
  const selector =
    request.view === "graph"
      ? `.edge-label[data-edge-id="${request.index}"]`
      : `#relationship-${request.index}`;
  // React Flow may recreate its label portal while the phone source view is open.
  // Resolve the canonical relationship's current button once it mounts.
  let frame: number;
  const scheduleFocus = () => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(focus);
  };
  const observer = new MutationObserver(scheduleFocus);
  function focus() {
    const target = panel!.querySelector<HTMLElement>(selector);
    if (!target) return;
    target.focus({ preventScroll: true });
    observer.disconnect();
  }
  observer.observe(panel, { childList: true, subtree: true });
  scheduleFocus();
  return () => {
    observer.disconnect();
    cancelAnimationFrame(frame);
  };
}
