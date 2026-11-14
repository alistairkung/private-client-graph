import { Icon } from "../../shared/Icon";
import { useLocale } from "../../shared/locale";

const methods = [
  {
    workspace: false,
    icon: "file",
    title: "Upload PDFs",
    detail: "Choose files from your device.",
  },
  {
    workspace: true,
    icon: "search",
    title: "Search Workspace",
    detail: "Find Sources in Gmail and Google Drive.",
  },
] as const;

export function SourceMethod({
  discover,
  disabled,
  change,
}: {
  discover: boolean;
  disabled: boolean;
  change: (discover: boolean) => void;
}) {
  const { t } = useLocale();
  return (
    <fieldset className="source-method" disabled={disabled}>
      <legend>{t("How would you like to add Sources?")}</legend>
      <div className="source-method-options">
        {methods.map(({ workspace, icon, title, detail }) => (
          <label key={title} className="source-method-option">
            <span className="source-method-icon">
              <Icon name={icon} />
            </span>
            <span className="source-method-copy">
              <strong>{t(title)}</strong>
              <span id={`method-help-${icon}`}>{t(detail)}</span>
            </span>
            <input
              type="radio"
              name="source-method"
              aria-label={t(title)}
              aria-describedby={`method-help-${icon}`}
              checked={discover === workspace}
              onChange={() => change(workspace)}
            />
          </label>
        ))}
      </div>
    </fieldset>
  );
}
