import { useLocale } from "../../shared/locale";
import type { PublicResearchSnapshot } from "./types";
import { PUBLIC_RESEARCH_DOWNLOAD } from "./api";
export function Publication({
  snapshot,
}: {
  snapshot: PublicResearchSnapshot;
}) {
  const { t } = useLocale();
  return (
    <>
      <section id="methodology" className="research-section research-reading">
        <h2>{t("Methodology and limitations")}</h2>
        <p>
          {t(
            "The question was whether constrained alias resolution improved retained relationship results when the extraction inputs were held fixed. A′ is the no-resolver replay control; B uses the same frozen extractions with resolution. This publication reports stored results without new execution or rescoring.",
          )}
        </p>
        <p>
          {t(
            "The ten held-out cases were authored by this project and checked with separate AI validators as an internal development tool. This was not independent human or institutional validation. The resolver comparison was post-hoc and exploratory. There are no repeated trials, uncertainty estimates or evidence of production generalisation.",
          )}
        </p>
        <p>
          {t(
            "All relationship improvement came from two Bea → Beatrice Ng endpoint-name corrections in one case. Nine cases were unchanged and no relationship regressions were observed in this dataset. This does not establish broader identity-disambiguation performance.",
          )}
        </p>
        <p>
          {t(
            "These cases were held out for this completed experiment. The full synthetic Sources and expected answers are now published; subsequent work informed by them cannot treat them as unseen evaluation data. Fresh undisclosed cases are needed for a future independent evaluation.",
          )}
        </p>
        <p>
          {t(
            "Original case names, Sources, entity names and Evidence remain in their original language. Interface translation does not alter the published artifacts.",
          )}
        </p>
      </section>
      <section id="publication" className="research-section">
        <h2>{t("Published artifact")}</h2>
        <a
          className="research-download"
          href={PUBLIC_RESEARCH_DOWNLOAD}
          download
        >
          {t("Download results")}
        </a>
        <dl className="research-metadata">
          <dt>{t("Schema version")}</dt>
          <dd>{snapshot.schema_version}</dd>
          <dt>{t("Snapshot identity")}</dt>
          <dd>{snapshot.snapshot_id}</dd>
          <dt>{t("Experiment identity")}</dt>
          <dd>{snapshot.experiment_id}</dd>
          <dt>{t("Integrity digest")}</dt>
          <dd>
            {snapshot.integrity.algorithm}: {snapshot.integrity.digest}
          </dd>
          <dt>{t("Digest scope")}</dt>
          <dd>{snapshot.integrity.scope}</dd>
        </dl>
        <p>
          {t(
            "The download is the same curated JSON artifact displayed here. Its digest covers canonical JSON excluding the integrity field. Source Run identities are listed in the comparison above. Raw provider communications and operational records are excluded.",
          )}
        </p>
      </section>
    </>
  );
}
