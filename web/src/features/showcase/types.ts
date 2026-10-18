import type { CanonicalState } from "../../shared/canonical-state";

export interface ShowcaseCaseSummary {
  id: string;
  title: string;
  description: string;
}

export interface ShowcaseCase extends ShowcaseCaseSummary {
  result_kind: "curated_ideal_fixture";
  notice: string;
  state: CanonicalState;
}
