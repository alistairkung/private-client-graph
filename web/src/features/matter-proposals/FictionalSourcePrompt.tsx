import { useEffect, useRef, useState } from "react";

const fictionalSourcePrompt = `Create a realistic but completely fictional private-client source document in the genre of an attendance note, client email, or letter.

Use only fictional people and trusts. Express supported family and trust relationships naturally in prose, including relationships such as parent, child, spouse, sibling, settlor, trustee, beneficiary, or protector where they fit the document.

Do not include any real personal, client, legal, or confidential information.

Return the source document only. Export it as a text-layer PDF, then upload that PDF through ordinary Matter Intake. I will separately confirm that the uploaded material is synthetic or fictional.`;

export function FictionalSourcePrompt({ onClose }: { onClose: () => void }) {
  const closeButton = useRef<HTMLButtonElement>(null);
  const copyButton = useRef<HTMLButtonElement>(null);
  const [copyStatus, setCopyStatus] = useState<"copied" | "failed">();

  useEffect(() => {
    const previousFocus = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButton.current?.focus();
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
      if (event.key !== "Tab") return;
      if (event.shiftKey && document.activeElement === closeButton.current) {
        event.preventDefault();
        copyButton.current?.focus();
      } else if (!event.shiftKey && document.activeElement === copyButton.current) {
        event.preventDefault();
        closeButton.current?.focus();
      }
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("keydown", closeOnEscape);
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus();
    };
  }, [onClose]);

  async function copyPrompt() {
    try {
      await navigator.clipboard.writeText(fictionalSourcePrompt);
      setCopyStatus("copied");
    } catch {
      setCopyStatus("failed");
    }
  }

  return <div className="prompt-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="fictional-source-prompt" role="dialog" aria-modal="true" aria-labelledby="fictional-source-heading">
      <header className="prompt-heading">
        <div>
          <h2 id="fictional-source-heading">Create a fictional source</h2>
          <p>Copy this prompt into an external AI assistant.</p>
        </div>
        <button ref={closeButton} className="prompt-close" type="button" onClick={onClose} aria-label="Close prompt">×</button>
      </header>
      <pre className="prompt-copy">{fictionalSourcePrompt}</pre>
      <div className="prompt-actions">
        <button ref={copyButton} className="intake-button secondary" type="button" onClick={copyPrompt}>Copy prompt</button>
        {copyStatus && <p role="status">{copyStatus === "copied" ? "Prompt copied." : "Prompt could not be copied. Select and copy the text manually."}</p>}
      </div>
    </section>
  </div>;
}
