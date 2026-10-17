import type { CanonicalGraph } from "../../shared/canonical-graph";
import type { CanonicalState } from "../../shared/canonical-state";

export interface MatterSummary {
  id: string;
  external_reference: string;
  title: string;
}

export interface MatterDetail extends MatterSummary {
  authoritative_source: { title: string; text: string } | null;
  state?: CanonicalState;
  current_graph: CanonicalGraph;
}
