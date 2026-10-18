import { useState } from "react";
import { useLocale } from "../../shared/locale";
import { EvidenceInspector } from "../../shared/research/EvidenceInspector";
import { GraphDrawing } from "../review/GraphDrawing";
import { ResearchRunSwitch } from "./ResearchRunSwitch";
import type { PublicCase, RunLabel } from "./types";
export function RecordedGraph({ sample }: { sample: PublicCase }) {
  return <RecordedGraphCase key={sample.case_id} sample={sample} />;
}

function RecordedGraphCase({ sample }: { sample: PublicCase }) {
  const { t } = useLocale();
  const [run, setRun] = useState<RunLabel>("A");
  const [selected, setSelected] = useState<number | null>(null);
  const observation = sample.observations.find(item => item.run_label === run)!;
  const graph = observation.state;
  const [entityId, setEntity] = useState<string | null>(null);
  const entity = graph.entities.find(item => item.id === entityId);
  const edge = graph.relationships[selected ?? -1];
  const sourceName = graph.entities.find(entity => entity.id === edge?.source)?.name;
  const targetName = graph.entities.find(entity => entity.id === edge?.target)?.name;
  const outcome = observation.relationships.find(item =>
    item.edge[0] === sourceName && item.edge[1] === edge?.type &&
    item.edge[2] === targetName && item.predicted.length > 0,
  );

  function selectRun(label: RunLabel) {
    const next = sample.observations.find(item => item.run_label === label)!;
    const index = edge ? next.state.relationships.findIndex(relationship =>
      relationship.type === edge.type &&
      next.state.entities.find(entity => entity.id === relationship.source)?.name === sourceName &&
      next.state.entities.find(entity => entity.id === relationship.target)?.name === targetName,
    ) : -1;
    setEntity(null);
    setRun(label);
    setSelected(index < 0 ? null : index);
  }

  return (
    <div className="research-graph-study">
      <div className="research-controls">
        <ResearchRunSwitch
          label={t("Inspect Run")}
          value={run}
          onChange={selectRun}
          options={(["A", "B"] as const).map(label => ({
            value: label,
            label: t(label === "A" ? "Original extraction · A" : "Resolved relationships · B"),
          }))}
        />
      </div>
      <div className="research-graph-evidence">
        <section aria-label={t("Recorded relationship graph")}>
          <label className="research-graph-selector">{t("Find a relationship")}
            <select value={selected ?? ""} onChange={event => { setEntity(null); setSelected(event.target.value === "" ? null : Number(event.target.value)); }}>
              <option value="">{t("Select a relationship")}</option>
              {graph.relationships.map((relationship, index) => <option key={index} value={index}>
                {graph.entities.find(item => item.id === relationship.source)?.name} — {t(relationship.type)} — {graph.entities.find(item => item.id === relationship.target)?.name}
              </option>)}
            </select>
          </label>
          <GraphDrawing state={graph} selected={selected} selectedEntity={entityId}
            memoryKey={`research:recorded:${sample.case_id}`}
            onSelect={index => { setEntity(null); setSelected(index); }}
            onEntity={id => { setSelected(null); setEntity(id); }} />
        </section>
        {entity ? <aside className="research-entity-inspector" aria-label={t("Entity relationships")}>
          <h3>{entity.name}</h3>
          <p>{t("Select a relationship to inspect its Evidence.")}</p>
          {graph.relationships.map((relationship, index) => {
            if (relationship.source !== entityId && relationship.target !== entityId) return null;
            const source = graph.entities.find(item => item.id === relationship.source)!;
            const target = graph.entities.find(item => item.id === relationship.target)!;
            return <button key={index} onClick={() => { setEntity(null); setSelected(index); }}>
              {source.name} · {t(relationship.type)} · {target.name}
            </button>;
          })}
        </aside> : <EvidenceInspector
          key={JSON.stringify(outcome ?? null)}
          relationship={outcome}
          source={null}
          sources={sample.sources}
        />}
      </div>
    </div>
  );
}
