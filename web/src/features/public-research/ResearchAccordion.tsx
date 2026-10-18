import { useId, useState, type ReactNode } from "react";
import { Accordion } from "@base-ui/react/accordion";
import { AnimatePresence, motion, useIsPresent, useReducedMotion } from "motion/react";
import "./research-accordion.css";

type AccordionEntry = { id: string; title: ReactNode; content: ReactNode };

export function ResearchAccordion({ items, className = "" }: {
  items: AccordionEntry[];
  className?: string;
}) {
  const [open, setOpen] = useState<string[]>([]);
  const id = useId();
  const reduced = useReducedMotion();
  const transition = reduced
    ? { duration: 0 }
    : { type: "spring" as const, bounce: 0.1, visualDuration: 0.35 };
  return <Accordion.Root className={`research-accordion ${className}`} multiple value={open} onValueChange={setOpen}>
    {items.map(item => {
      const expanded = open.includes(item.id);
      return <Accordion.Item key={item.id} value={item.id}>
        <Accordion.Header className="research-accordion-heading">
          <Accordion.Trigger id={`${id}-${item.id}-trigger`} aria-controls={`${id}-${item.id}-panel`}
            render={<motion.button className="research-accordion-trigger" />}>
            <span>{item.title}</span>
            <motion.svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"
              animate={{ rotate: expanded ? 180 : 0 }} transition={transition}>
              <path d="m6 9 6 6 6-6" />
            </motion.svg>
          </Accordion.Trigger>
        </Accordion.Header>
        <Accordion.Panel id={`${id}-${item.id}-panel`} aria-labelledby={`${id}-${item.id}-trigger`} className="research-accordion-panel" keepMounted>
          <AnimatePresence initial={false}>
            {expanded && <AccordionContent key={item.id} reduced={!!reduced} transition={transition}>{item.content}</AccordionContent>}
          </AnimatePresence>
        </Accordion.Panel>
      </Accordion.Item>;
    })}
  </Accordion.Root>;
}

function AccordionContent({ children, reduced, transition }: {
  children: ReactNode;
  reduced: boolean;
  transition: { duration: number } | { type: "spring"; bounce: number; visualDuration: number };
}) {
  const present = useIsPresent();
  const openMask = "linear-gradient(to bottom, black 100%, transparent 100%)";
  return <motion.div inert={!present} aria-hidden={!present || undefined}
    variants={{
      open: { height: "auto", maskImage: openMask },
      closed: { height: 0, maskImage: reduced ? openMask : "linear-gradient(to bottom, black 50%, transparent 100%)" },
    }} initial="closed" animate="open" exit="closed" transition={transition}>
    <motion.div variants={{ open: { opacity: 1, filter: "blur(0px)" }, closed: { opacity: reduced ? 1 : 0, filter: reduced ? "blur(0px)" : "blur(2px)" } }} transition={transition}>
      <div className="research-accordion-content">{children}</div>
    </motion.div>
  </motion.div>;
}
