import type { Ref } from "react";
import { Icon } from "../../../shared/Icon";
import { useLocale } from "../../../shared/locale";
import { candidateKey, type Candidate } from "./api";

export function SourceSelection({
  headingRef,
  options,
  selected,
  change,
  bulkSeen,
  onBulk,
  openEmail,
  read,
}: {
  headingRef: Ref<HTMLHeadingElement>;
  options: Candidate[];
  selected: Candidate[];
  change: (items: Candidate[]) => void;
  bulkSeen?: Set<string>;
  onBulk: (items: Candidate[]) => void;
  openEmail: (candidate: Candidate) => void;
  read: () => void;
}) {
  const { t } = useLocale();
  const groups = [...new Set(options.map((item) => item.followUp))].reverse();
  const selectedKeys = new Set(selected.map(candidateKey));
  const available = new Map(options.map(item => [candidateKey(item), item]));
  const additions = options.filter(item => !selectedKeys.has(candidateKey(item)) && !bulkSeen?.has(candidateKey(item)));
  const removed = selected.filter(item => !available.has(candidateKey(item)));
  function move(index: number) {
    const next = selected.slice();
    [next[index - 1], next[index]] = [next[index], next[index - 1]];
    change(next);
  }
  return (
    <section className="discovery-panel">
      <h2 ref={headingRef} tabIndex={-1}>
        {t("Select Sources")}
      </h2>
      <div className="discovery-selection-tools">
        <span className="discovery-caption">{t("{count} selected", { count: selected.length })}</span>
        {additions.length > 0 && (
          <button onClick={() => onBulk(additions)}>
            {bulkSeen
              ? t(additions.length === 1 ? "Add 1 new result" : "Add {count} new results", { count: additions.length })
              : t(options.length === 1 ? "Select 1 result" : "Select all {count} results", { count: options.length })}
          </button>
        )}
      </div>
      {removed.map(item => (
        <button key={candidateKey(item)} onClick={() => change(selected.filter(s => s !== item))}>
          {t("Remove unavailable Source · {title}", { title: item.title })}
        </button>
      ))}
      {!options.length && <p>{t("No Sources available to select.")}</p>}
      {groups.map((group) => (
        <fieldset className="discovery-group" key={JSON.stringify([group])}>
          <legend>
            {group
              ? t("Found via {query}", { query: group })
              : t("Original search")}
          </legend>
          {options
            .filter((item) => item.followUp === group)
            .map((item) => {
              const key = candidateKey(item);
              const included = selectedKeys.has(key);
              const kind = t(item.kind === "pdf" ? "PDF" : "Email");
              return (
                <div key={item.kind + item.id} className="discovery-row">
                  <input
                    id={"source-" + item.kind + "-" + item.id}
                    type="checkbox"
                    checked={included}
                    aria-label={item.title + " · " + kind}
                    onChange={() =>
                      change(
                        included
                          ? selected.filter((s) => candidateKey(s) !== key)
                          : [...selected, item],
                      )
                    }
                  />
                  {item.kind === "email" ? (
                    <button
                      className="discovery-email-link"
                      aria-haspopup="dialog"
                      aria-label={t("Read {title}", { title: item.title })}
                      onClick={() => openEmail(item)}
                    >
                      {item.title}
                      <Icon name="chevron" />
                    </button>
                  ) : (
                    <label htmlFor={"source-pdf-" + item.id}>{item.title}</label>
                  )}
                  <small>{kind}</small>
                </div>
              );
            })}
        </fieldset>
      ))}
      {selected.length > 1 && (
        <details className="discovery-order">
          <summary>{t("Preview order")}</summary>
          <ol>
            {selected.map((item, index) => (
              <li key={item.kind + item.id}>
                <span>
                  {index + 1}.{" "}
                  {available.get(candidateKey(item))?.title ?? item.title}
                </span>
                {index > 0 && (
                  <button
                    onClick={() => move(index)}
                    aria-label={t("Move {title} up", { title: item.title })}
                  >
                    {t("Move up")}
                  </button>
                )}
              </li>
            ))}
          </ol>
        </details>
      )}
      <button
        className="button primary discovery-next"
        disabled={!selected.length || removed.length > 0}
        onClick={read}
      >
        {t("Preview exact Sources")} <Icon name="arrow" />
      </button>
    </section>
  );
}
