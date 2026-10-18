import { useState } from "react";
import { Dialog } from "../../shared/Dialog";
import { useLocale } from "../../shared/locale";
import { fictionalPrompt } from "./prompt";
export function FictionalPrompt({ onClose }: { onClose: () => void }) {
  const { t } = useLocale();
  const [status, setStatus] = useState<string>();
  async function copy() {
    try {
      await navigator.clipboard.writeText(t(fictionalPrompt));
      setStatus("Prompt copied.");
    } catch {
      setStatus("Select and copy the prompt manually.");
    }
  }
  return (
    <Dialog title={t("Create a fictional source")} onClose={onClose}>
      <p>
        {t(
          "Copy this prompt into an external AI assistant, then export its fictional document as a text-layer PDF.",
        )}
      </p>
      <pre className="prompt-text">{t(fictionalPrompt)}</pre>
      <button className="button primary" onClick={copy}>
        {t("Copy prompt")}
      </button>
      {status && <p role="status">{t(status)}</p>}
    </Dialog>
  );
}
