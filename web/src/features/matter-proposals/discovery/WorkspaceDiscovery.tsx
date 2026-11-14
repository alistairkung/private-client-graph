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
import { DiscoveryResults } from "./DiscoveryResults";
import { SourceSelection } from "./SourceSelection";

export function WorkspaceDiscovery({
  onBusy,
  scope,
  onGrantLoss,
}: {
  scope?: {
    label: string;
    folder: string;
    label_name: string;
    folder_name: string;
  };
  onGrantLoss?: () => void;
  onBusy: (busy: boolean) => void;
}) {
  const { t } = useLocale();
  const [terms, setTerms] = useState("Alder Trust");
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [session, setSession] = useState("");
  const [view, setView] = useState<View>();
  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [selected, setSelected] = useState<Candidate[]>([]);
  const [preview, setPreview] = useState<Preview>();
  const [busy, setBusy] = useState(false);
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

  async function run(operation: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    onBusy(true);
    setError(undefined);
    try {
      await operation();
    } catch (failure) {
      if (!mounted.current) return;
      if (
        onGrantLoss &&
        failure instanceof RequestFailure &&
        failure.detail?.code === "workspace_reconnect"
      )
        onGrantLoss();
      else setError(failure);
    } finally {
      setBusy(false);
      onBusy(false);
    }
  }
  async function start() {
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
    setPreview(undefined);
    const proposal = await action<{ id: string }>("import", {
      session,
      preview: preview.token,
      publish_synthetic: true,
      metadata: { external_reference, matter_title },
    });
    if (mounted.current)
      navigate("/app/matter-proposals/" + encodeURIComponent(proposal.id));
  }
  return (
    <div className="intake-form discovery" aria-busy={busy}>
      <fieldset disabled={busy}>
        <legend>{t("Private Workspace discovery")}</legend>
        {!view ? (
          <>
            <p>
              {t(
                "Starting discovery authorizes private inspection of matching synthetic content in the selected scope. Review and publication require separate approval.",
              )}
            </p>
            <label>
              {t("Drive folder")}
              <select>
                <option>{scope?.folder_name ?? "folder-1"}</option>
              </select>
            </label>
            <label>
              {t("Gmail label")}
              <select>
                <option>{scope?.label_name ?? "alder-label"}</option>
              </select>
            </label>
            <label>
              {t("Initial search terms")}
              <input
                value={terms}
                maxLength={160}
                onChange={(e) => setTerms(e.target.value)}
              />
            </label>
            <label>
              {t("Gmail from (UTC)")}
              <input
                type="date"
                value={first}
                max={last || undefined}
                onChange={(e) => setFirst(e.target.value)}
              />
            </label>
            <label>
              {t("Gmail through (UTC)")}
              <input
                type="date"
                value={last}
                min={first || undefined}
                onChange={(e) => setLast(e.target.value)}
              />
            </label>
            <button
              className="button"
              disabled={!terms.trim() || Boolean(first && last && first > last)}
              onClick={() => run(start)}
            >
              {t("Start private discovery")}
            </button>
          </>
        ) : (
          <>
            <DiscoveryResults
              view={view}
              followups={followups}
              inspect={() =>
                run(async () =>
                  setView(await action<View>("inspect", { session })),
                )
              }
              approve={(revision, query) => run(() => follow(revision, query))}
            />
            <SourceSelection
              options={candidates(view, followups, (id) =>
                t("Email hit {id}", { id }),
              )}
              selected={selected}
              change={(items) => {
                setSelected(items);
                setPreview(undefined);
              }}
              preview={preview}
              read={() => run(read)}
              publish={(ref, title) => run(() => publish(ref, title))}
            />
          </>
        )}
      </fieldset>
      {error != null && <ErrorNotice error={error} />}
    </div>
  );
}
