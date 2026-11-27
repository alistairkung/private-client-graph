import { useRef, useState } from "react";
import type { RunDetail } from "../shared/contracts";
import { archiveRun } from "./api";
import { ReviewDialog } from "./ReviewDialog";

export function ArchiveRun({ run, number, disabled, archived }: {
  run: RunDetail;
  number: number;
  disabled: boolean;
  archived: () => void;
}) {
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const lock = useRef(false);

  async function remove() {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await archiveRun(run.experiment_id, run.id);
      archived();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setConfirm(false);
      setBusy(false);
      lock.current = false;
    }
  }

  return (
    <>
      <button className="secondary" disabled={disabled || busy} onClick={() => setConfirm(true)}>
        Remove from history
      </button>
      {error && <p role="alert">Run could not be removed. {error}</p>}
      {confirm && (
        <ReviewDialog title={`Remove Run ${number} from history?`} close={() => setConfirm(false)} busy={busy}
          actions={
            <>
              <button className="secondary" disabled={busy} onClick={() => setConfirm(false)}>Cancel</button>
              <button disabled={busy || disabled} onClick={() => void remove()}>
                {busy ? "Removing…" : "Remove Run"}
              </button>
            </>
          }>
          <p>The Run will disappear from the Experiment. Its files and any paid attempts will be retained.</p>
        </ReviewDialog>
      )}
    </>
  );
}
