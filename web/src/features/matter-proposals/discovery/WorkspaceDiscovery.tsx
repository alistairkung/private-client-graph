import { useEffect, useRef, useState } from "react";
import { navigate, useNavigationLock } from "../../../app/navigation";
import { RequestFailure } from "../../../shared/api";
import { ErrorNotice } from "../../../shared/Feedback";
import { useLocale } from "../../../shared/locale";
import {
  action,
  candidates,
  mergeHits,
  type DiscoveredItem,
  candidateKey,
  type PreviewProgress,
  type View,
  type EmailMessage,
  type Hits,
  type FollowUp,
  type Preview,
  type Candidate,
} from "./api";
import { SearchSetup } from "./SearchSetup";
import { PublicationReview } from "./PublicationReview";
import { DiscoveryResults, SearchSummary } from "./DiscoveryResults";
import { EmailReader, type EmailReading } from "./EmailReader";
import { useOriginalSearch } from "./useOriginalSearch";
import { SourceSelection } from "./SourceSelection";

export function WorkspaceDiscovery({
  onBusy,
  active = true,
  scope,
  onGrantLoss,
  onStaleSearch,
}: {
  active?: boolean;
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
  const [discovered, setDiscovered] = useState<DiscoveredItem[]>([]);
  const [selected, setSelected] = useState<Candidate[]>([]);
  const [bulkSeen, setBulkSeen] = useState<Set<string>>();
  const [progress, setProgress] = useState<PreviewProgress>();
  const [preview, setPreview] = useState<Preview>();
  const [reading, setReading] = useState<EmailReading>();
  const [operationLabel, setOperationLabel] = useState("");
  const busy = Boolean(operationLabel);
  const [reference, setReference] = useState("");
  const [title, setTitle] = useState("");
  const resultsHeading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (session) resultsHeading.current?.focus();
  }, [session]);
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

  function receiveOriginal(next: View) {
    setDiscovered(items => mergeHits(items, { messages: next.returned_messages, files: next.files }));
    setView(next);
  }
  const original = useOriginalSearch(session, active ? view : undefined, receiveOriginal, recoverSession);

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
        setProgress(undefined);
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
    receiveOriginal(result.view);
  }
  async function follow(revision: number, query: string) {
    const result = await action<Hits>("follow-up", {
      session,
      revision,
      query,
    });
    setDiscovered(items => mergeHits(items, result, query));
    setFollowups((previous) => [...previous, { ...result, revision, query }]);
  }
  async function openEmail(candidate: Candidate) {
    const opening: EmailReading = { title: candidate.title, state: "loading" };
    setReading(opening);
    try {
      const email = await action<EmailMessage>("email", {
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
    let result = await action<Preview | PreviewProgress>("preview", {
      session,
      candidates: selected.map(({ kind, id }) => ({ kind, id })),
    });
    while (mounted.current && "continuation" in result) {
      setProgress(result);
      result = await action<Preview | PreviewProgress>("preview-next", {
        session, continuation: result.continuation,
      });
    }
    if (mounted.current && "token" in result) setPreview(result);
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
    ? candidates(discovered, view, (number) =>
        t("Uninspected email {number}", { number }),
      )
    : [];
  const failedNumber = error instanceof RequestFailure ? error.detail?.source_number : undefined;
  const affected = failedNumber && selected[failedNumber - 1];
  const operationStatus = progress
    ? t("Prepared {completed} of {total} Sources…", { completed: progress.completed, total: progress.total })
    : t(operationLabel);
  function changeSelection(items: Candidate[]) {
    // Manually excluded arrivals stay excluded when the next group is added.
    if (bulkSeen && items.length < selected.length) {
      setBulkSeen(new Set([...bulkSeen, ...selected.map(candidateKey)]));
    }
    setSelected(items);
    setError(undefined);
  }
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
        {busy ? operationStatus : !preview && searchStatus}
      </p>
      {error != null && <ErrorNotice error={error} />}
      {affected && failedNumber && (
        <p>{t("Check Source {number} · {title}", { number: failedNumber, title: affected.title })}</p>
      )}
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
              run("Searching emails and PDFs…", () => start(terms, first, last))
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
            <SearchSummary view={view} folder={folder} label={label} headingRef={resultsHeading} {...original} />
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
                change={changeSelection}
                bulkSeen={bulkSeen}
                onBulk={(items) => {
                  setBulkSeen(new Set(options.map(candidateKey)));
                  changeSelection([...selected, ...items]);
                }}
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
