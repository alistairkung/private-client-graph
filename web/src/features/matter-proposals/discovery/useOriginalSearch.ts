import { useEffect, useEffectEvent, useState } from "react";
import { action, type View } from "./api";

/** Schedule one continuation per rendered original-search revision. */
export function useOriginalSearch(
  session: string,
  view: View | undefined,
  receive: (next: View) => void,
  recoverSession: (failure: unknown) => boolean,
) {
  const [interrupted, setInterrupted] = useState(false);
  const receiveBatch = useEffectEvent(receive);
  const handleFailure = useEffectEvent((failure: unknown) => {
    if (!recoverSession(failure)) setInterrupted(true);
  });
  const revision = view?.revision;
  const stoppedOnError = Boolean(view?.stop_reason && view.stop_reason !== "Batch complete");
  // A retry is explicit and applies only to the revision the practitioner saw.
  const [retryRevision, setRetryRevision] = useState<number>();
  const searching = !!view?.can_inspect_more && !interrupted && (!stoppedOnError || retryRevision === revision);

  useEffect(() => {
    if (!searching || !session || revision === undefined) return;
    const controller = new AbortController();
    void action<View>("inspect", { session, revision }, controller.signal).then(
      next => { if (!controller.signal.aborted) receiveBatch(next); },
      failure => { if (!controller.signal.aborted) handleFailure(failure); },
    );
    return () => controller.abort();
  }, [session, revision, searching]);

  function retry() {
    setInterrupted(false);
    setRetryRevision(revision);
  }
  return { searching, interrupted, retry };
}
