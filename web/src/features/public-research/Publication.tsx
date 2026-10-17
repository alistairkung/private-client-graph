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
