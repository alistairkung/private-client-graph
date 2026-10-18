import type { ReactNode, Ref } from "react";
import "./pipeline-node.css";

type PipelineNodeProps = {
  id: string;
  title: string;
  type: string;
  summary: string;
  open: boolean;
  onToggle: () => void;
  headerRef?: Ref<HTMLButtonElement>;
  action?: ReactNode;
  children: ReactNode;
  expandLabel?: string;
  collapseLabel?: string;
  regionLabel?: string;
};

// Execution, configuration and data access belong to callers of this shared stage.
export function PipelineNode({
  id, title, type, summary, open, onToggle, headerRef, action, children,
  expandLabel = "Expand settings",
  collapseLabel = "Collapse settings",
  regionLabel = `${title} settings`,
}: PipelineNodeProps) {
  return (
    <section className={`pipeline-node ${open ? "expanded" : ""}`}>
      <button
        ref={headerRef}
        type="button"
        className="node-header"
        aria-expanded={open}
        aria-controls={id}
        onClick={onToggle}
      >
        <strong>{title}</strong>
        <small>{type}</small>
        <span>{summary}</span>
        <u>{open ? collapseLabel : expandLabel}</u>
      </button>
      {action}
      <div id={id} role="region" aria-label={regionLabel} hidden={!open} className="node-settings">
        {children}
      </div>
    </section>
  );
}
