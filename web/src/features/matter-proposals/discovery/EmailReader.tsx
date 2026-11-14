import { Dialog } from "../../../shared/Dialog";
import { useLocale } from "../../../shared/locale";

export type EmailReading = { title: string } & (
  | { state: "loading" }
  | { state: "ready"; text: string }
  | { state: "error"; limited: boolean }
);

export function EmailReader({ reading, close }: { reading: EmailReading; close: () => void }) {
  const { t } = useLocale();
  return (
    <Dialog title={reading.title} onClose={close}>
      {reading.state === "loading" && (
        <p className="discovery-working" role="status">
          <span className="discovery-spinner" aria-hidden="true" />
          {t("Opening email…")}
        </p>
      )}
      {reading.state === "ready" && <div className="email-reader-body">{reading.text}</div>}
      {reading.state === "error" && (
        <p role="alert">{t(reading.limited ? "This search reached its limit." : "This email could not be opened.")}</p>
      )}
    </Dialog>
  );
}
