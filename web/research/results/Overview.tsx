import type { ExperimentDetail } from "../shared/contracts";
import { number, RecordedDetails } from "../shared/presentation";

type Link = (changes: Record<string, string>) => string;
export function Overview({
  data,
  link,
}: {
  data: ExperimentDetail;
  link: Link;
}) {
  return (
    <section>
      <h2>Paired results</h2>
      <p>
        Each treatment repetition shares its frozen extraction with the
        baseline. Cohort means give each scored input equal weight. Failures
        remain visible in coverage.
      </p>
      <div className="cohort-tables">
        {data.cohort_summaries.map((cohort) => (
          <section key={cohort.cohort}>
            <h3>{cohort.cohort} cohort</h3>
            <p>
              {cohort.samples} inputs · {cohort.scored_repetitions} scored
              treatment repetitions · {cohort.failed_repetitions} failed or
              unavailable · {cohort.not_attempted_repetitions} without a
              recorded result
            </p>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th className="numeric">Baseline mean</th>
                    <th className="numeric">Treatment mean</th>
                    <th className="numeric">Scored inputs B / T</th>
                  </tr>
                </thead>
                <tbody>
                  {cohort.metrics.map((metric) => (
                    <tr key={metric.name}>
                      <th>
                        <a
                          href={link({
                            view: "investigate",
                            sample:
                              data.samples.find(
                                (sample) => sample.cohort === cohort.cohort,
                              )?.id ?? "",
                            outcome: "all",
                            relationship: "",
                          })}
                        >
                          {metric.name.replaceAll("_", " ")}
                        </a>
                      </th>
                      <td className="numeric">
                        {number(metric.baseline_mean)}
                      </td>
                      <td className="numeric">
                        {number(metric.treatment_mean)}
                      </td>
                      <td className="numeric">
                        {metric.baseline_scored} / {metric.treatment_scored}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))}
      </div>
      <h3>Extraction samples and repetitions</h3>
      <div className="table-scroll">
        <table>
          <caption>
            F1 by extraction sample. Delta is treatment minus baseline.
          </caption>
          <thead>
            <tr>
              <th>Case / sample</th>
              <th>Cohort</th>
              <th>Baseline F1</th>
              <th>Treatment mean F1</th>
              <th>Mean delta</th>
              <th>Treatment scored / planned</th>
            </tr>
          </thead>
          <tbody>
            {data.samples.map((sample) => (
              <tr key={sample.id}>
                <td>
                  <a
                    href={link({
                      view: "investigate",
                      sample: sample.id,
                      observation: "noop-0",
                      outcome: "all",
                      relationship: "",
                    })}
                  >
                    {sample.case_id}
                    <small>{sample.id}</small>
                  </a>
                </td>
                <td>{sample.cohort}</td>
                <td className="numeric">
                  {number(sample.observations[0]?.evaluation?.f1)}
                </td>
                <td className="numeric">{number(sample.resolver_mean_f1)}</td>
                <td className="numeric">{number(sample.mean_delta_f1)}</td>
                <td className="numeric">
                  {sample.scored} / {sample.planned}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <RecordedDetails
        title="Cohort distributions and within-sample variability"
        value={data.cohorts}
      />
    </section>
  );
}
