import type { CanonicalGraph } from "../../shared/canonical-graph";

export interface MatterSummary {
  id: string;
  external_reference: string;
  title: string;
}

export interface MatterDetail extends MatterSummary {
  authoritative_source: { title: string; text: string };
  current_graph: CanonicalGraph;
}
