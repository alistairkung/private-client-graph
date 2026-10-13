import { useEffect, useId, useRef, type ReactNode } from "react";

/** Native modal focus isolation with a persistent action footer. */
export function ReviewDialog({
  title,
  close,
  busy = false,
  children,
  actions,
}: {
  title: string;
  close: () => void;
  busy?: boolean;
  children: ReactNode;
  actions: ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const titleId = useId();
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    dialog.current?.showModal();
    heading.current?.focus();
    return () => {
      dialog.current?.close();
      if (previous?.isConnected) previous.focus({ preventScroll: true });
    };
  }, []);
  useEffect(() => {
    heading.current?.focus();
  }, [title]);
  return (
    <dialog
      ref={dialog}
      className="run-review-dialog"
      aria-labelledby={titleId}
      onKeyDown={(event) => {
        if (event.key !== "Tab") return;
        const controls = Array.from(
          event.currentTarget.querySelectorAll<HTMLElement>(
            'button:not(:disabled), input:not(:disabled), select:not(:disabled), summary, a[href], [tabindex="0"]',
          ),
        ).filter((element) => element.getClientRects().length);
        const first = controls[0],
          last = controls.at(-1);
        if (
          event.shiftKey &&
          (document.activeElement === first ||
            document.activeElement === heading.current)
        ) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
    >
      <div className="review-shell">
        <header>
          <h2 id={titleId} ref={heading} tabIndex={-1}>
            {title}
          </h2>
          <button
            className="secondary"
            aria-label="Close review"
            disabled={busy}
            onClick={close}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              aria-hidden="true"
            >
              <path d="m3 3 10 10M13 3 3 13" />
            </svg>
          </button>
        </header>
        <div className="review-body">{children}</div>
        <footer>{actions}</footer>
      </div>
    </dialog>
  );
}
