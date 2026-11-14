import type { Ref } from "react";
import { Icon } from "../../../shared/Icon";
import { useLocale } from "../../../shared/locale";
import type { Candidate } from "./api";

export function SourceSelection({
  headingRef,
  options,
  selected,
  change,
  read,
}: {
  headingRef: Ref<HTMLHeadingElement>;
  options: Candidate[];
  selected: Candidate[];
  change: (items: Candidate[]) => void;
  read: () => void;
}) {
  const { t } = useLocale();
  const groups = [...new Set(options.map((item) => item.followUp))].reverse();
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
      <p className="discovery-caption">
        {t("{count} of 5 selected", { count: selected.length })}
      </p>
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
              const match = (s: Candidate) =>
                s.kind === item.kind && s.id === item.id;
              const included = selected.some(match);
              const kind = t(item.kind === "pdf" ? "PDF" : "Email");
              return (
                <label key={item.kind + item.id} className="discovery-row">
                  <input
                    type="checkbox"
                    checked={included}
                    disabled={!included && selected.length >= 5}
                    aria-label={item.title + " · " + kind}
                    onChange={() =>
                      change(
                        included
                          ? selected.filter((s) => !match(s))
                          : [...selected, item],
                      )
                    }
                  />
                  <span>{item.title}</span>
                  <small>{kind}</small>
                </label>
              );
            })}
        </fieldset>
      ))}
      {selected.length > 1 && (
        <div className="discovery-order">
          <h3>{t("Preview order")}</h3>
          <ol>
            {selected.map((item, index) => (
              <li key={item.kind + item.id}>
                <span>
                  {index + 1}.{" "}
                  {options.find((s) => s.kind === item.kind && s.id === item.id)
                    ?.title ?? item.title}
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
        </div>
      )}
      <button
        className="button primary discovery-next"
        disabled={!selected.length}
        onClick={read}
      >
        {t("Preview exact Sources")} <Icon name="arrow" />
      </button>
    </section>
  );
}
