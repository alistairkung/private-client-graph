import { useMemo, useState } from "react";
import { useLocale } from "../../shared/locale";
import { EvidenceInspector } from "../../shared/research/EvidenceInspector";
import type { CanonicalGraph } from "../../shared/canonical-graph";
import { GraphView } from "../review/GraphView";
import type { PublicCase, PublicObservation } from "./types";
import "../review/review.css";

// Project retained canonical state into the existing renderer; never construct or score it.
export function recordedGraph(observation: PublicObservation): CanonicalGraph {
  return {
    entities: observation.state.entities,
    relationships: observation.state.relationships,
    evidence: observation.state.evidence,
  };
}

export function RecordedGraph({ sample }: { sample: PublicCase }) {
  const { t } = useLocale();
  const [run, setRun] = useState("A");
  const [selected, setSelected] = useState<number | null>(null);
  const observation = sample.observations.find(item => item.run_label === run)!;
  const graph = useMemo(() => recordedGraph(observation), [observation]);
  const edge = graph.relationships[selected ?? -1];
  const sourceName = graph.entities.find(entity => entity.id === edge?.source)?.name;
  const targetName = graph.entities.find(entity => entity.id === edge?.target)?.name;
  const outcome = observation.relationships.find(item =>
    item.edge[0] === sourceName && item.edge[1] === edge?.type &&
    item.edge[2] === targetName && item.predicted.length > 0,
  );

  return (
    <div className="research-graph-study">
      <div className="research-controls">
        {(["A", "B"] as const).map(label => (
          <button
            key={label}
            aria-pressed={run === label}
            onClick={() => { setRun(label); setSelected(null); }}
          >
            {t(label === "A" ? "Original extraction · A" : "Resolved relationships · B")}
          </button>
        ))}
      </div>
      <div className="research-graph-evidence">
        <section aria-label={t("Recorded relationship graph")}>
          <GraphView preserveContext graph={graph} selected={selected} onSelect={setSelected} />
        </section>
        <EvidenceInspector
          key={`${run}-${selected}`}
          relationship={outcome}
          source={null}
          sources={sample.sources}
        />
      </div>
    </div>
  );
}
