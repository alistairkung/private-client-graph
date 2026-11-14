import { Dialog } from "../../../shared/Dialog";
import { Icon } from "../../../shared/Icon";
import { useLocale } from "../../../shared/locale";
import type { EmailMessage } from "./api";

export type EmailReading =
  | { state: "loading"; title: string }
  | ({ state: "ready" } & EmailMessage)
  | { state: "error"; title: string; limited: boolean };

export function EmailReader({ reading, close }: { reading: EmailReading; close: () => void }) {
  const { t } = useLocale();
  return (
    <Dialog title={reading.title} onClose={close} className="email-reader">
      {reading.state === "loading" && (
        <p className="discovery-working" role="status">
          <span className="discovery-spinner" aria-hidden="true" />
          {t("Opening email…")}
        </p>
      )}
      {reading.state === "ready" && (
        <>
          <MessageHeader email={reading} />
          <div className="email-reader-body">{reading.text}</div>
        </>
      )}
      {reading.state === "error" && (
        <p role="alert">{t(reading.limited ? "This search reached its limit." : "This email could not be opened.")}</p>
      )}
    </Dialog>
  );
}

function MessageHeader({ email }: { email: EmailMessage }) {
  const { t } = useLocale();
  const sent = email.sent_at ? new Date(email.sent_at) : null;
  const recorded = new Date(email.gmail_timestamp_ms);
  const hasRecordedTime = Number.isFinite(recorded.getTime());
  return (
    <header className="email-envelope">
      <div className="email-sender">
        <span className="email-envelope-icon"><Icon name="mail" /></span>
        <dl>
          <dt>{t("From")}</dt>
          <dd>{email.sender || t("Sender unavailable")}</dd>
        </dl>
      </div>
      <dl className="email-fields">
        {[[t("To"), email.to], [t("Cc"), email.cc], [t("Bcc"), email.bcc]].map(
          ([label, value]) => value && <div key={label}><dt>{label}</dt><dd>{value}</dd></div>,
        )}
        {(sent || hasRecordedTime) && (
          <div>
            <dt>{t(sent ? "Sent" : "Gmail timestamp")}</dt>
            <dd><MailTime date={sent ?? recorded} /></dd>
          </div>
        )}
      </dl>
      {sent && hasRecordedTime && sent.getTime() !== recorded.getTime() && (
        <details className="email-dates">
          <summary>{t("Gmail timestamp")}</summary>
          <MailTime date={recorded} />
        </details>
      )}
    </header>
  );
}

function MailTime({ date }: { date: Date }) {
  const { locale } = useLocale();
  return (
    <time dateTime={date.toISOString()}>
      {date.toLocaleString(locale, {
        year: "numeric", month: "short", day: "numeric",
        hour: "numeric", minute: "2-digit", timeZoneName: "short",
      })}
    </time>
  );
}
