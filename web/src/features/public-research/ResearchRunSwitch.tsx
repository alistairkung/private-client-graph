import { useId } from "react";
import { LayoutGroup, motion, useReducedMotion } from "motion/react";
import type { RunLabel } from "./types";
import "./research-interactions.css";

interface ResearchRunOption {
  value: RunLabel;
  label: string;
}

export function ResearchRunSwitch({ label, value, options, onChange }: {
  label: string;
  value: RunLabel;
  options: ResearchRunOption[];
  onChange: (value: RunLabel) => void;
}) {
  const id = useId();
  const reducedMotion = useReducedMotion();
  return (
    <LayoutGroup id={id}>
      <div className="research-run-switch" role="group" aria-label={label}>
        {options.map(option => (
          <motion.button
            key={option.value}
            type="button"
            className="research-run-option"
            aria-pressed={value === option.value}
            onClick={() => { if (value !== option.value) onChange(option.value); }}
            whileTap={reducedMotion ? undefined : { scale: 0.985 }}
            transition={{ type: "spring", stiffness: 1218, damping: 70 }}
          >
            {value === option.value && (reducedMotion
              ? <span className="research-run-surface" aria-hidden="true" />
              : <motion.span
                  className="research-run-surface"
                  aria-hidden="true"
                  layoutId="active-run"
                  initial={false}
                  transition={{ type: "spring", stiffness: 1218, damping: 70 }}
                  style={{ borderRadius: 8 }}
                />)}
            <span className="research-run-label">{option.label}</span>
          </motion.button>
        ))}
      </div>
    </LayoutGroup>
  );
}
