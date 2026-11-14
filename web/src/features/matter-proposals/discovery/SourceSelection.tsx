import { useState } from "react";
import { useLocale } from "../../../shared/locale";
import type { Candidate, Preview } from "./api";

type SelectionProps = {
  options: Candidate[];
  selected: Candidate[];
  change: (items: Candidate[]) => void;
  preview?: Preview;
  read: () => void;
  publish: (reference: string, title: string) => void;
};

export function SourceSelection({
  options,
  selected,
  change,
  preview,
  read,
  publish,
}: SelectionProps) {
  const { t } = useLocale();
  const [reference, setReference] = useState("");
  const [title, setTitle] = useState("");
  const [approved, setApproved] = useState<string>();
  function move(index: number) {
    const next = selected.slice();
    [next[index - 1], next[index]] = [next[index], next[index - 1]];
    change(next);
  }
  return (
    <section>
      <h2>{t("Select Sources")}</h2>
      {options.map((item) => {
        const key = item.kind + item.id;
        const included = selected.some(
          (s) => s.id === item.id && s.kind === item.kind,
        );
        return (
          <label className="discovery-choice" key={key}>
            <input
              type="checkbox"
              checked={included}
              disabled={!included && selected.length >= 5}
              onChange={() =>
                change(
                  included
                    ? selected.filter(
                        (s) => s.kind !== item.kind || s.id !== item.id,
                      )
                    : [...selected, item],
                )
              }
            />
            {item.title} · {t(item.kind === "pdf" ? "PDF" : "Email")}
          </label>
        );
      })}
      <ol>
        {selected.map((s, i) => (
          <li key={s.kind + s.id}>
            {s.title}{" "}
            <button disabled={i === 0} onClick={() => move(i)}>
              {t("Move up")}
            </button>
          </li>
        ))}
      </ol>
      <button disabled={!selected.length} onClick={read}>
        {t("Preview exact Sources")}
      </button>
      {preview && (
        <div>
          {preview.sources.map((s) => (
            <article key={s.id}>
              <h3>{s.title}</h3>
              <pre>{s.text}</pre>
            </article>
          ))}
          <label>
            {t("External Matter reference")}
            <input
              maxLength={100}
              value={reference}
              onChange={(e) => setReference(e.target.value)}
            />
          </label>
          <label>
            {t("Matter title")}
            <input
              maxLength={200}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>
          <label className="discovery-choice">
            <input
              type="checkbox"
              checked={approved === preview.token}
              onChange={(e) =>
                setApproved(e.target.checked ? preview.token : undefined)
              }
            />
            {t(
              "I approve publishing these synthetic Sources in this order. Every reader can see their full titles, texts and proposed relationships as soon as the proposal is saved, before Matter confirmation.",
            )}
          </label>
          <button
            className="button primary"
            disabled={
              approved !== preview.token || !title.trim() || !reference.trim()
            }
            onClick={() => publish(reference, title)}
          >
            {t("Create public proposal")}
          </button>
        </div>
      )}
    </section>
  );
}
