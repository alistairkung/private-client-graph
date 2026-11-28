import { useLayoutEffect, useRef, useState, type MouseEventHandler, type ReactNode, type Ref } from "react";
import { Icon } from "../../../shared/Icon";
import { useLocale } from "../../../shared/locale";
import { candidateKey, type Candidate, type FollowUp, type View } from "./api";
import { DiscoveryResults } from "./DiscoveryResults";
import { useSourceDrag } from "./useSourceDrag";

export function SourceSelection({
  headingRef,
  options,
  selected,
  change,
  bulkSeen,
  onBulk,
  openEmail,
  read,
  view,
  followups,
  approve,
}: {
  headingRef: Ref<HTMLHeadingElement>;
  options: Candidate[];
  selected: Candidate[];
  change: (items: Candidate[]) => void;
  bulkSeen?: Set<string>;
  onBulk: (items: Candidate[]) => void;
  openEmail: (candidate: Candidate) => void;
  read: () => void;
  view: View;
  followups: FollowUp[];
  approve: (revision: number, query: string) => void;
}) {
  const { t } = useLocale();
  const [onlySelected, setOnlySelected] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const [jump, setJump] = useState<{ query: string }>();
  const groups = [...new Set(options.map((item) => item.followUp))].reverse();
  const available = new Map(options.map(item => [candidateKey(item), item]));
  const selectedKeys = new Set(selected.map(candidateKey));
  const additions = options.filter(item => !selectedKeys.has(candidateKey(item)) && !bulkSeen?.has(candidateKey(item)));
  const removed = selected.filter(item => !available.has(candidateKey(item)));
  const groupHeadings = useRef(new Map<string | undefined, HTMLHeadingElement>());
  const selectedView = useRef<HTMLButtonElement>(null);
  const orderControl = useRef<HTMLButtonElement | null>(null);
  const { drag, scroller, handle } = useSourceDrag(move);

  useLayoutEffect(() => {
    if (jump) groupHeadings.current.get(jump.query)?.focus();
  }, [jump]);

  useLayoutEffect(() => {
    orderControl.current?.focus({ preventScroll: true });
    orderControl.current?.scrollIntoView?.({ block: "nearest" });
    orderControl.current = null;
  }, [selected]);

  function include(item: Candidate) {
    const key = candidateKey(item);
    const included = selectedKeys.has(key);
    if (included && onlySelected) selectedView.current?.focus();
    change(included ? selected.filter(source => candidateKey(source) !== key) : [...selected, item]);
  }

  function move(from: number, to: number, control?: HTMLButtonElement) {
    if (from === to || to < 0 || to >= selected.length) return;
    const next = selected.slice();
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    orderControl.current = control ?? null;
    change(next);
    setAnnouncement(t("{title} moved to position {number} of {total}.", {
      title: available.get(candidateKey(moved))?.title ?? moved.title,
      number: to + 1,
      total: selected.length,
    }));
  }

  return (
    <div className="discovery-columns discovery-find">
      <section className="discovery-panel discovery-selection">
        <h2 className="intake-section-title" ref={headingRef} tabIndex={-1}>
          {t("Select Sources")}
        </h2>
        <div className="discovery-selection-tools">
          <div className="discovery-result-views" role="group" aria-label={t("Source views")}>
            <button aria-pressed={!onlySelected} onClick={() => setOnlySelected(false)}>
              {t("All results")}
            </button>
            <button ref={selectedView} aria-pressed={onlySelected} onClick={() => setOnlySelected(true)}>
              {t("Selected ({count})", { count: selected.length })}
            </button>
          </div>
          {!onlySelected && additions.length > 0 && (
            <button className="discovery-text-action" onClick={() => onBulk(additions)}>
              {bulkSeen
                ? t(additions.length === 1 ? "Add 1 new result" : "Add {count} new results", { count: additions.length })
                : t(options.length === 1 ? "Select 1 result" : "Select all {count} results", { count: options.length })}
            </button>
          )}
        </div>
        <div className="discovery-preview-action">
          <p className="discovery-caption" role="status">
            {t("{count} selected", { count: selected.length })}
          </p>
          <button
            className="button primary"
            disabled={!selected.length || removed.length > 0}
            onClick={read}
          >
            {t(selected.length === 1 ? "Preview 1 Source" : "Preview {count} Sources", { count: selected.length })}
            <Icon name="arrow" />
          </button>
        </div>
        <div className="discovery-result-list" ref={scroller}>
          {removed.map(item => (
            <button key={candidateKey(item)} onClick={() => include(item)}>
              {t("Remove unavailable Source · {title}", { title: item.title })}
            </button>
          ))}
          {onlySelected ? (
            <>
              <p className="discovery-list-hint">
                {t(selected.length ? "Drag Sources or use the arrows to set publication order." : "Choose Sources from All results to preview them here.")}
              </p>
              <ul className="discovery-source-list" aria-label={t("Publication order")}>
                {selected.map((source, index) => {
                  const key = candidateKey(source);
                  const item = available.get(key);
                  if (!item) return null;
                  const sorting = drag?.from === index;
                  const dropEdge = drag?.to === index && !sorting
                    ? drag.from < index ? "after" : "before"
                    : undefined;
                  return (
                    <SourceRow
                      key={key}
                      item={item}
                      included
                      include={() => include(item)}
                      openEmail={openEmail}
                      position={index}
                      sorting={sorting}
                      dropEdge={dropEdge}
                    >
                      {selected.length > 1 && (
                        <div className="discovery-order-controls">
                          <span className="discovery-grip" aria-hidden="true" {...handle(index)}>
                            <Icon name="grip" />
                          </span>
                          <OrderArrow title={item.title} direction="up" disabled={index === 0}
                            onClick={event => move(index, index - 1, event.currentTarget)} />
                          <OrderArrow title={item.title} direction="down" disabled={index === selected.length - 1}
                            onClick={event => move(index, index + 1, event.currentTarget)} />
                        </div>
                      )}
                    </SourceRow>
                  );
                })}
              </ul>
            </>
          ) : (
            <>
              {options.length ? (
                <p className="discovery-list-hint">
                  {t("Use the checkboxes to include Sources in your proposal.")}
                </p>
              ) : <p className="discovery-list-hint">{t("No Sources available to select.")}</p>}
              {groups.map(group => {
                const name = group ? t("Found via {query}", { query: group }) : t("Original search");
                return (
                  <section className="discovery-group" key={group ?? ""} role="group" aria-label={name}>
                    <h3 tabIndex={-1} ref={node => {
                      if (node) groupHeadings.current.set(group, node);
                      else groupHeadings.current.delete(group);
                    }}>
                      {name}
                    </h3>
                    <ul className="discovery-source-list">
                      {options.filter(item => item.followUp === group).map(item => (
                        <SourceRow
                          key={candidateKey(item)}
                          item={item}
                          included={selectedKeys.has(candidateKey(item))}
                          include={() => include(item)}
                          openEmail={openEmail}
                        />
                      ))}
                    </ul>
                  </section>
                );
              })}
            </>
          )}
        </div>
        <p className="discovery-sr" role="status">{announcement}</p>
      </section>
      <DiscoveryResults
        view={view}
        followups={followups}
        options={options}
        approve={approve}
        show={(query) => {
          setOnlySelected(false);
          setJump({ query });
        }}
      />
    </div>
  );
}

function SourceRow({
  item,
  included,
  include,
  openEmail,
  position,
  sorting,
  dropEdge,
  children,
}: {
  item: Candidate;
  included: boolean;
  include: () => void;
  openEmail: (item: Candidate) => void;
  position?: number;
  sorting?: boolean;
  dropEdge?: "before" | "after";
  children?: ReactNode;
}) {
  const { t } = useLocale();
  const kind = t(item.kind === "pdf" ? "PDF" : "Email");
  return (
    <li className="discovery-row" data-source-position={position} data-sorting={sorting} data-drop-edge={dropEdge}>
      <label className="discovery-include">
        <input type="checkbox" checked={included} onChange={include} aria-label={item.title + " · " + kind} />
        <span>
          {position !== undefined && <span className="discovery-source-number" aria-hidden="true">{position + 1}. </span>}
          {item.title}<small>{kind}</small>
        </span>
      </label>
      <div className="discovery-row-actions">
        {item.kind === "email" ? (
          <button
            className="discovery-text-action"
            aria-haspopup="dialog"
            aria-label={t("Read {title}", { title: item.title })}
            onClick={() => openEmail(item)}
          >
            {t("Read email")} <Icon name="chevron" />
          </button>
        ) : <small>{t("Text in preview")}</small>}
      </div>
      {children}
    </li>
  );
}


function OrderArrow({ title, direction, disabled, onClick }: {
  title: string;
  direction: "up" | "down";
  disabled: boolean;
  onClick: MouseEventHandler<HTMLButtonElement>;
}) {
  const { t } = useLocale();
  const label = t(direction === "up" ? "Move {title} up" : "Move {title} down", { title });
  return (
    <button
      className="discovery-order-arrow"
      data-direction={direction}
      aria-label={label}
      title={label}
      aria-disabled={disabled}
      onClick={disabled ? undefined : onClick}
    >
      <Icon name="arrow" />
    </button>
  );
}
