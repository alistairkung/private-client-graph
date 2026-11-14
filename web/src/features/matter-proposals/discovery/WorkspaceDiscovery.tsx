import { useEffect, useRef, useState } from "react";
import { navigate, useNavigationLock } from "../../../app/navigation";
import { RequestFailure } from "../../../shared/api";
import { ErrorNotice } from "../../../shared/Feedback";
import { useLocale } from "../../../shared/locale";
import {
  action,
  candidates,
  type View,
  type Hits,
  type FollowUp,
  type Preview,
  type Candidate,
} from "./api";
import { SearchSetup } from "./SearchSetup";
import { PublicationReview } from "./PublicationReview";
import { DiscoveryResults, SearchSummary } from "./DiscoveryResults";
import { EmailReader, type EmailReading } from "./EmailReader";
import { SourceSelection } from "./SourceSelection";

export function WorkspaceDiscovery({
  onBusy,
  scope,
  onGrantLoss,
  onStaleSearch,
}: {
  scope?: {
    label: string;
    folder: string;
    label_name: string;
    folder_name: string;
  };
  onStaleSearch?: () => void;
  onGrantLoss?: () => void;
  onBusy: (busy: boolean) => void;
}) {
  const { t } = useLocale();
  const [session, setSession] = useState("");
  const [view, setView] = useState<View>();
  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [selected, setSelected] = useState<Candidate[]>([]);
  const [preview, setPreview] = useState<Preview>();
  const [reading, setReading] = useState<EmailReading>();
  const [operationLabel, setOperationLabel] = useState("");
  const busy = Boolean(operationLabel);
  const [reference, setReference] = useState("");
  const [title, setTitle] = useState("");
  const selectionHeading = useRef<HTMLHeadingElement>(null);
  const restoreSelectionFocus = useRef(false);
  useEffect(() => {
    if (!preview && !busy && restoreSelectionFocus.current) {
      selectionHeading.current?.focus();
      restoreSelectionFocus.current = false;
    }
  }, [preview, busy]);
  const [error, setError] = useState<unknown>();
  useNavigationLock(busy);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      onBusy(false);
    };
  }, [onBusy]);

  function recoverSession(failure: unknown): boolean {
    if (!(failure instanceof RequestFailure)) return false;
    if (onGrantLoss && failure.detail?.code === "workspace_reconnect") {
      onGrantLoss();
      return true;
    }
    if (onStaleSearch && failure.detail?.code === "unknown_discovery") {
      onStaleSearch();
      return true;
    }
    return false;
  }

  async function run(label: string, operation: () => Promise<void>) {
    if (busy) return;
    setOperationLabel(label);
    onBusy(true);
    setError(undefined);
    try {
      await operation();
    } catch (failure) {
      if (!mounted.current) return;
      if (!recoverSession(failure)) {
        if (preview) setPreview(undefined);
        setError(failure);
      }
    } finally {
      if (mounted.current) {
        setOperationLabel("");
        onBusy(false);
      }
    }
  }
  async function start(terms: string, first: string, last: string) {
    const result = await action<{ session: string; view: View }>("start", {
      terms,
      label: scope?.label ?? "alder-label",
      folder: scope?.folder ?? "folder-1",
      first_day: first || null,
      last_day: last || null,
    });
    setSession(result.session);
    setView(result.view);
  }
  async function follow(revision: number, query: string) {
    const result = await action<Hits>("follow-up", {
      session,
      revision,
      query,
    });
    setFollowups((previous) => [...previous, { ...result, revision, query }]);
  }
  async function openEmail(candidate: Candidate) {
    const opening: EmailReading = { title: candidate.title, state: "loading" };
    setReading(opening);
    try {
      const email = await action<{ title: string; text: string }>("email", {
        session,
        message_id: candidate.id,
      });
      setReading((current) =>
        current === opening ? { ...email, state: "ready" } : current,
      );
    } catch (failure) {
      if (!mounted.current || recoverSession(failure)) return;
      const limited = failure instanceof RequestFailure && failure.detail?.code === "discovery_limit";
      setReading((current) =>
        current === opening ? { title: candidate.title, state: "error", limited } : current,
      );
    }
  }
  async function read() {
    setPreview(undefined);
    setPreview(
      await action<Preview>("preview", {
        session,
        candidates: selected.map(({ kind, id }) => ({ kind, id })),
      }),
    );
  }
  async function publish(external_reference: string, matter_title: string) {
    if (!preview) return;
    const proposal = await action<{ id: string }>("import", {
      session,
      preview: preview.token,
      publish_synthetic: true,
      metadata: { external_reference, matter_title },
    });
    if (mounted.current)
      navigate("/app/matter-proposals/" + encodeURIComponent(proposal.id));
  }
  const folder = scope?.folder_name ?? "folder-1";
  const label = scope?.label_name ?? "alder-label";
  const options = view
    ? candidates(view, followups, (_id, number) =>
        t("Uninspected email {number}", { number }),
      )
    : [];
  const latestFollowUp = followups.at(-1);
  const searchStatus = latestFollowUp
    ? t("{query} returned {mail} email hits and {pdf} PDF hits.", {
        query: latestFollowUp.query,
        mail: latestFollowUp.messages.length,
        pdf: latestFollowUp.files.length,
      })
    : "";
  const stage = preview ? 2 : view ? 1 : 0;
  return (
    <div className="discovery">
      <ol className="discovery-stages" aria-label={t("Discovery progress")}>
        {["Search scope", "Find Sources", "Review and publish"].map(
          (step, i) => (
            <li key={step} aria-current={stage === i ? "step" : undefined}>
              <span aria-hidden="true">{i + 1}</span>
              {t(step)}
            </li>
          ),
        )}
      </ol>
      <p
        className={busy ? "discovery-working" : "discovery-sr"}
        role="status"
        aria-atomic="true"
      >
        {busy && <span className="discovery-spinner" aria-hidden="true" />}
        {busy
          ? t(operationLabel)
          : view &&
            t(
              "Original search: {mail} emails returned, {read} inspected, {pdf} PDFs listed.",
              {
                mail: view.returned_messages.length,
                read: view.inspected.length,
                pdf: view.files.length,
              },
            )}
        {!busy && view && !preview && " " + searchStatus}
      </p>
      {error != null && <ErrorNotice error={error} />}
      {scope &&
        error instanceof RequestFailure &&
        error.detail?.code === "source_unavailable" && (
          <button onClick={() => selectionHeading.current?.focus()}>
            {t("Review selection")}
          </button>
        )}
      <fieldset
        className="discovery-controls"
        disabled={busy}
        aria-label={t("Private Workspace discovery")}
      >
        {!view ? (
          <SearchSetup
            folder={folder}
            label={label}
            start={(terms, first, last) =>
              run("Searching Workspace…", () => start(terms, first, last))
            }
          />
        ) : preview ? (
          <PublicationReview
            key={preview.token}
            preview={preview}
            reference={reference}
            title={title}
            setReference={setReference}
            setTitle={setTitle}
            edit={() => {
              restoreSelectionFocus.current = true;
              setPreview(undefined);
            }}
            publish={() =>
              run("Creating proposal…", () => publish(reference, title))
            }
          />
        ) : (
          <>
            <SearchSummary
              view={view}
              inspect={() =>
                run("Inspecting original emails…", async () =>
                  setView(await action<View>("inspect", { session })),
                )
              }
            />
            <button
              className="discovery-jump"
              onClick={() => selectionHeading.current?.focus()}
            >
              {t("Jump to Source selection")}
            </button>
            <div className="discovery-columns">
              <DiscoveryResults
                view={view}
                followups={followups}
                approve={(revision, query) =>
                  run("Searching Workspace…", () => follow(revision, query))
                }
              />
              <SourceSelection
                headingRef={selectionHeading}
                options={options}
                selected={selected}
                change={setSelected}
                openEmail={openEmail}
                read={() => run("Preparing exact preview…", read)}
              />
            </div>
          </>
        )}
      </fieldset>
      {reading && (
        <EmailReader reading={reading} close={() => setReading(undefined)} />
      )}
    </div>
  );
}
