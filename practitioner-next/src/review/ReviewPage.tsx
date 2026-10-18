import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
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
  const [selected, setSelected] = useState<number | null>(null);
  const [entity, setEntity] = useState<string | null>(null);
  const [evidenceId, setEvidenceId] = useState<string | null>(null);
  const [sourceId, setSourceId] = useState<string | null>(
    state.sources[0]?.id ?? null,
  );
  const [tab, setTab] = useState<"relationships" | "sources">("relationships");
  const [view, setView] = useState<"graph" | "list">(() =>
    window.innerWidth <= 900 ? "list" : "graph",
  );
  const [decision, setDecision] = useState<"confirm" | "discard">();
  const [decisionError, setDecisionError] = useState<unknown>();
  const decisionBlocked = decisionIsBlocked(decisionError);
  const selectionView = useRef<"graph" | "list">("graph");
  const [focusRequest, setFocusRequest] = useState<{
    index: number;
    view: "graph" | "list";
  }>();
  const inspector = useRef<HTMLHeadingElement>(null);
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
    selectionView.current = view;
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
    requestAnimationFrame(() => {
      const destination =
        document.querySelector<HTMLElement>(".source-text mark") ??
        document.getElementById("sources-heading");
      destination?.focus();
    });
  }
  function returnToRelationship() {
    setTab("relationships");
    if (selected === null) return;
    setView(selectionView.current);
    setFocusRequest({ index: selected, view: selectionView.current });
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
        <section className="relationships-panel" id="relationships-panel">
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
            <div className="view-toggle" aria-label={t("Relationship view")}>
              <button
                aria-pressed={view === "graph"}
                onClick={() => setView("graph")}
              >
                {t("Graph")}
              </button>
              <button
                aria-pressed={view === "list"}
                onClick={() => setView("list")}
              >
                {t("List")}
              </button>
            </div>
          </header>
          {!state.relationships.length ? (
            <div className="empty graph-empty">
              <h3>{t("No relationships returned")}</h3>
              <p>
                {t("The returned graph contains no relationships to inspect.")}
              </p>
            </div>
          ) : view === "graph" ? (
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
            />
          ) : (
            <RelationshipList
              state={state}
              selected={selected}
              entity={entity}
              onSelect={selectRelationship}
              onClear={() => setEntity(null)}
            />
          )}
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
              <h2 id="evidence-heading" tabIndex={-1} ref={inspector}>
                {t("Evidence")}
              </h2>
              {relationship && (
                <button className="text-button" onClick={openSource}>
                  {t("Inspect in source")}
                </button>
              )}
            </div>
            <motion.div
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
        <div id="source-panel" className="source-column">
          <SourceReader
            sources={state.sources}
            sourceId={sourceId}
            evidence={evidence}
            onSource={setSourceId}
            onReturn={returnToRelationship}
          />
        </div>
      </div>
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
    target.focus();
    observer.disconnect();
  }
  observer.observe(panel, { childList: true, subtree: true });
  scheduleFocus();
  return () => {
    observer.disconnect();
    cancelAnimationFrame(frame);
  };
}
