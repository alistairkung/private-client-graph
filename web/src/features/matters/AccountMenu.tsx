import { useEffect, useId, useRef, useState } from "react";
import { SignOut } from "./SignOut";

export function AccountMenu({
  onSignOut = () => window.location.assign("/"),
}: {
  onSignOut?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const panelId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const regionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open || signingOut) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      setOpen(false);
      triggerRef.current?.focus();
    }
    function closeOnOutsidePointer(event: PointerEvent) {
      if (!regionRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("keydown", closeOnEscape);
    document.addEventListener("pointerdown", closeOnOutsidePointer);
    return () => {
      document.removeEventListener("keydown", closeOnEscape);
      document.removeEventListener("pointerdown", closeOnOutsidePointer);
    };
  }, [open, signingOut]);

  return (
    <div
      ref={regionRef}
      className="account-menu"
      onBlur={event => {
        if (!signingOut && !event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <button
        type="button"
        ref={triggerRef}
        className="account-menu-trigger"
        aria-label="Account and application menu"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => {
          if (!signingOut) setOpen(current => !current);
        }}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="8" r="3.25" />
          <path d="M5.75 19c.55-3.5 2.63-5.25 6.25-5.25S17.7 15.5 18.25 19" />
        </svg>
      </button>
      {open && (
        <div id={panelId} className="account-menu-panel">
          <a href="/">Public showcase</a>
          <SignOut onPendingChange={setSigningOut} onSuccess={onSignOut} />
        </div>
      )}
    </div>
  );
}
