import { useEffect, useRef, type ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";
import { useLocale } from "./locale";
import { Icon } from "./Icon";

export function Dialog({
  title,
  children,
  onClose,
  busy = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  busy?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const reduced = useReducedMotion();
  const { t } = useLocale();
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
      if (previous?.isConnected) previous.focus();
    };
  }, []);
  return (
    <dialog
      className="dialog"
      ref={ref}
      aria-labelledby="dialog-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget && !busy) onClose();
      }}
    >
      <motion.div
        className="dialog-content"
        initial={{ opacity: 0, y: reduced ? 0 : 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: reduced ? 0.06 : 0.18 }}
      >
        <div className="dialog-heading">
          <h2 id="dialog-title">{title}</h2>
          <button
            className="icon-button"
            aria-label={t("Close dialog")}
            disabled={busy}
            onClick={onClose}
          >
            <Icon name="close" />
          </button>
        </div>
        {children}
      </motion.div>
    </dialog>
  );
}
