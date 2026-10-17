import type { ReactNode } from "react";
import { useLocale } from "../../shared/locale";
import { CaseWorkspace } from "./CaseWorkspace";
import { Publication } from "./Publication";
import { RecordedGraph } from "./RecordedGraph";
import { ResearchArchitecture } from "./ResearchArchitecture";
import { Provenance, RunComparison } from "./RunComparison";
import { Usage } from "./Usage";
import type { PublicResearchSnapshot } from "./types";

function Chapter({ id, title, children, band = false }: { id: string; title: string; children: ReactNode; band?: boolean }) {
  const { t } = useLocale();
  const content = <><h2>{t(title)}</h2>{children}</>;
  return <section id={id} className={`research-section research-chapter ${band ? "research-evidence-band" : ""}`}>
    {band ? <div className="research-band-content">{content}</div> : content}
  </section>;
}
export function ResearchStory({ snapshot }: { snapshot: PublicResearchSnapshot }) {
  const { t } = useLocale();
  const resolver = snapshot.runs.find(run => run.label === "B")!;
  const correction = snapshot.cases.find(sample => sample.case_id === "heldout_03");
  return <>
    <Chapter id="question" title="Can the graph survive the evidence?">
      <p>{t("Private-client analysis depends on who is connected to whom, in what capacity, and on which documentary words. A plausible graph is not enough: its relationships must remain traceable to the Sources.")}</p>
      <p>{t("Can one full-context extraction call reconstruct a provenance-aware current relationship graph from multiple documents? Can a separate generative resolver improve relationship accuracy? And what additional cost and complexity does it introduce?")}</p>
    </Chapter>
    <Chapter id="architecture" title="Interpretation, then construction." band>
      <p>{t("Ordered Sources enter semantic extraction together. The model proposes Source-attributed candidates; deterministic validation and construction produce CanonicalState. The optional resolver sits between extraction and construction, correcting supported endpoint names while leaving Evidence quotations unchanged.")}</p>
      <ResearchArchitecture runs={snapshot.runs} />
    </Chapter>
    <Chapter id="methodology" title="A small test, with a replay control.">
      <p>{t("Five development cases informed the system. This completed evaluation used {cases} project-authored held-out synthetic cases, {sources} Sources and {relationships} expected relationships. The answer key was checked using separate AI validators as an internal development tool; this was not external human or institutional validation.", { cases: snapshot.benchmark.case_count, sources: snapshot.benchmark.source_count, relationships: snapshot.benchmark.expected_relationships })}</p>
      <p>{t("Run A made one fresh extraction per held-out case. A′ replayed those frozen extraction outputs with no resolver and zero provider calls. Run B reused the same outputs with generative resolution. A′ reproduces A’s outcomes, helping isolate the resolver’s effect from variation in fresh extraction; it is not an independent replication.")}</p>
      <p>{t("The comparison was post-hoc and exploratory. These are project-created cases, not an external benchmark. Publishing their Sources and answer key means they can no longer serve as unseen cases for subsequent work informed by this publication.")}</p>
    </Chapter>
    <RunComparison runs={snapshot.runs} />
    <Chapter id="failure-analysis" title="Two names changed the score.">
      <p>{t("In Case 03, the Source explicitly establishes that Bea refers to Beatrice Ng. The baseline nevertheless used Bea as the endpoint of two relationships. Resolution changed those endpoints to Beatrice Ng, moving both relationships from false-positive / false-negative pairs to true positives. The supporting documentary quotations did not change.")}</p>
      <p>{t("Switch between the recorded graphs, select a relationship, then open its expected or predicted Evidence in the original Source. The graph shows retained canonical state; missing expected relationships remain inspectable in the case comparison below.")}</p>
      {correction && <RecordedGraph sample={correction} />}
    </Chapter>
    <Chapter id="findings" title="What held up elsewhere?">
      <p>{t("Within these tested examples, explicit temporal trustee replacement was handled correctly; reversing document chronology did not produce a last-document-wins failure. Multi-document Evidence aggregation succeeded, and distinct Sources with identical display titles remained distinguishable. These observations describe this dataset only.")}</p>
      <p>{t("The other nine cases had no relationship-score regressions after resolution. Inspect every case below, including unchanged outcomes and the two separate provenance diagnostics.")}</p>
      <CaseWorkspace cases={snapshot.cases} />
    </Chapter>
    <Chapter id="limitations" title="Accuracy has a cost. So does certainty.">
      <p>{t("This is a small synthetic benchmark with no real client documents, one model, one extraction per case and one resolver execution per case. There are no repeated trials or uncertainty estimates. Exact-name scoring makes endpoint spelling consequential; strict approved-quote matching can reject a supporting passage with a different quotation boundary.")}</p>
      <p>{t("The Source/quote-pair diagnostic checks a different denominator and does not classify the cause of each mismatch. Higher relationship F1 does not mean quotation or Source attribution was repaired, nor does it establish production reliability or general superiority.")}</p>
      <p>{t("Resolution added {calls} provider calls and {tokens} tokens, with {seconds} seconds of summed provider time. This is summed call latency, not end-to-end elapsed time. Verified USD costs are unavailable and remain Unpriced. Higher F1 does not automatically justify additional calls in every application.", { calls: resolver.usage.attempts, tokens: (resolver.usage.total_tokens ?? 0).toLocaleString("en-US"), seconds: resolver.usage.provider_seconds?.toFixed(2) ?? t("Unavailable") })}</p>
      <Provenance runs={snapshot.runs} />
      <Usage runs={snapshot.runs} />
    </Chapter>
    <Chapter id="reproducibility" title="Reproduce the published record.">
      <p>{t("Micro F1 pools true positives, false positives and false negatives across cases; macro F1 averages case-level F1. Neither defines true negatives. Approved-quote provenance checks exact approved text on matched relationships; Source-pair attribution additionally checks the recorded Source identity.")}</p>
      <p>{t("Original case names, Sources, entity names and Evidence remain in their original language. Interface translation does not alter the published artifacts.")}</p>
      <Publication snapshot={snapshot} />
      <a href="https://github.com/alistairkung/private-client-graph">{t("View the repository")} →</a>
    </Chapter>
  </>;
}
