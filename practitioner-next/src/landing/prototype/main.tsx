import {
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { createRoot } from "react-dom/client";
import {
  MotionConfig,
  motion,
  useMotionValueEvent,
  useScroll,
  useTransform,
} from "motion/react";
import { getPublicExample, type PublicExample } from "../landing-api";
import { DocumentMontage } from "./DocumentMontage";
import { SourceReview } from "./SourceReview";
import { PrototypeGraph, type EntityOrigins } from "./PrototypeGraph";
import "./prototype.css";

const reducedQuery = "(prefers-reduced-motion: reduce)";
function subscribeMotion(callback: () => void) {
  const media = window.matchMedia(reducedQuery);
  media.addEventListener("change", callback);
  return () => media.removeEventListener("change", callback);
}

function App() {
  const [example, setExample] = useState<PublicExample>();
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    getPublicExample(controller.signal)
      .then(setExample)
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [attempt]);
  return (
    <MotionConfig reducedMotion="user">
      {example ? (
        <ScrollStory example={example} />
      ) : (
        <main className="prototype-loading" role="status">
          <h1>
            {failed
              ? "The example could not load."
              : "Opening the document example…"}
          </h1>
          {failed && (
            <button
              onClick={() => {
                setFailed(false);
                setAttempt(attempt + 1);
              }}
            >
              Try again
            </button>
          )}
        </main>
      )}
    </MotionConfig>
  );
}

function ScrollStory({ example }: { example: PublicExample }) {
  const track = useRef<HTMLElement>(null);
  const note = useRef<HTMLElement>(null);
  const graph = useRef<HTMLDivElement>(null);
  const graphHolder = useRef<HTMLDivElement>(null);
  const drawing = useRef<HTMLDivElement>(null);
  const reduced = useSyncExternalStore(
    subscribeMotion,
    () => window.matchMedia(reducedQuery).matches,
    () => true,
  );
  const { scrollYProgress } = useScroll({
    target: track,
    offset: ["start start", "end end"],
  });
  const [exploring, setExploring] = useState(false);
  const [selected, setSelected] = useState(0);
  const [origins, setOrigins] = useState<EntityOrigins>(new Map());
  useMotionValueEvent(scrollYProgress, "change", (value) =>
    setExploring(value >= 0.96),
  );
  const headingOpacity = useTransform(scrollYProgress, [0.62, 0.69], [0, 1]);
  const graphX = useTransform(scrollYProgress, [0.86, 0.96], ["46%", "0%"]);
  const sourceOpacity = useTransform(scrollYProgress, [0.87, 0.97], [0, 1]);
  const sourceX = useTransform(scrollYProgress, [0.87, 0.97], [35, 0]);
  const source = example.state.sources[0];
  const edge = example.state.relationships[selected];
  const evidence = useMemo(
    () =>
      edge
        ? example.state.evidence.filter((item) =>
            edge.evidence_ids.includes(item.id),
          )
        : [],
    [edge, example.state.evidence],
  );
  const name = (id: string) =>
    example.state.entities.find((item) => item.id === id)?.name ?? id;
  const relationship = edge
    ? `${name(edge.source)} ${edge.type.replaceAll("_", " ")} ${name(edge.target)}`
    : "Select a relationship to inspect its Evidence.";

  useLayoutEffect(() => {
    if (!note.current || !drawing.current || !graphHolder.current || reduced)
      return;
    const measure = () => {
      const holder = graphHolder.current!;
      const mobile = window.matchMedia("(max-width: 700px)").matches;
      const transform = new DOMMatrix(getComputedStyle(holder).transform);
      const initialShift = mobile ? 0 : holder.offsetWidth * 0.46;
      const next: EntityOrigins = new Map();
      for (const entity of example.state.entities) {
        const span = [
          ...note.current!.querySelectorAll<HTMLElement>(
            "[data-source-entity-id]",
          ),
        ].find((item) => item.dataset.sourceEntityId === entity.id);
        const anchor = [
          ...drawing.current!.querySelectorAll<HTMLElement>("[data-entity-id]"),
        ].find((item) => item.dataset.entityId === entity.id);
        if (!span || !anchor) continue;
        const from = span.getBoundingClientRect();
        const to = anchor.getBoundingClientRect();
        next.set(entity.id, [
          from.left + from.width / 2 - (to.left - transform.m41 + initialShift),
          from.top + from.height / 2 - (to.top + 32),
        ]);
      }
      setOrigins(next);
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(note.current);
    observer.observe(drawing.current);
    window.addEventListener("resize", measure);
    void document.fonts.ready.then(measure);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [example.state, reduced]);

  function skipToGraph() {
    if (!track.current || !graph.current) return;
    setExploring(true);
    window.scrollTo({
      top: reduced
        ? graph.current.offsetTop
        : track.current.offsetTop +
          track.current.offsetHeight -
          window.innerHeight,
      behavior: "instant",
    });
    requestAnimationFrame(() => graph.current?.focus({ preventScroll: true }));
  }
  return (
    <div className={`prototype${reduced ? " prototype-static" : ""}`}>
      <section
        id="scroll-story"
        ref={track}
        className="prototype-track"
        aria-label="From documents to relationships and Evidence"
      >
        <div className="prototype-stage">
          <header className="prototype-header">
            <a href="/">Private Client Graph</a>
            <span>Interaction prototype</span>
            <a
              href="#graph-explorer"
              onClick={(event) => {
                event.preventDefault();
                skipToGraph();
              }}
            >
              Skip to graph
            </a>
          </header>
          <DocumentMontage
            state={example.state}
            progress={scrollYProgress}
            reduced={reduced}
            noteRef={note}
            hidden={!reduced && exploring}
          />
          <div
            id="graph-explorer"
            tabIndex={-1}
            ref={graph}
            className="prototype-graph-scene"
            inert={!reduced && !exploring}
          >
            <motion.div
              ref={graphHolder}
              className="prototype-graph-holder"
              style={reduced ? undefined : { x: graphX }}
            >
              <motion.div
                className="prototype-graph-heading"
                style={reduced ? undefined : { opacity: headingOpacity }}
              >
                <h2>Follow the relationships.</h2>
                <p>Working synthetic example · Select a relationship</p>
              </motion.div>
              <PrototypeGraph
                state={example.state}
                progress={scrollYProgress}
                reduced={reduced}
                selected={selected}
                onSelect={setSelected}
                origins={origins}
                drawingRef={drawing}
              />
            </motion.div>
            {source && (
              <motion.div
                className="prototype-source-holder"
                style={
                  reduced ? undefined : { opacity: sourceOpacity, x: sourceX }
                }
              >
                <SourceReview
                  source={source}
                  evidence={evidence}
                  relationship={relationship}
                  reduced={reduced}
                  active={reduced || exploring}
                />
              </motion.div>
            )}
          </div>
          <p className="prototype-stage-footer">
            Synthetic material. Curated graph. No live extraction.
          </p>
        </div>
      </section>
      <footer className="prototype-end">
        <p>Scroll back through the documents.</p>
        <a href="/">Back to the current landing page</a>
      </footer>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
