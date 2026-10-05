const measures = [
  { name: "Relationship precision", explanation: "The proportion of predicted relationships that match the answer key." },
  { name: "Relationship recall", explanation: "The proportion of expected relationships recovered from the source." },
  { name: "F1", explanation: "The balance of relationship precision and recall." },
  { name: "Provenance accuracy", explanation: "Among correct relationships, the proportion with at least one attached Evidence span that exactly matches an approved span." },
  { name: "Evaluation-set size", explanation: "The number of benchmark cases included in the published evaluation." },
];

export function EvaluationChapter() {
  return (
    <section id="evaluation" className="evaluation-chapter" tabIndex={-1} aria-labelledby="evaluation-title">
      <header className="evaluation-introduction">
        <h2 id="evaluation-title">How well does it recover the relationships?</h2>
        <p>
          A reviewable graph is a starting point. Benchmark cases let us measure
          which relationships the system recovers, which it misses, and whether
          correct relationships carry approved Evidence.
        </p>
        <p className="evaluation-publication-state">
          Evaluation is in progress. Representative aggregate results are not yet available.
        </p>
      </header>

      <section className="evaluation-method" aria-labelledby="evaluation-method-title">
        <h3 id="evaluation-method-title">How the benchmark works</h3>
        <p>
          Define the complete relationship answer key first, then author synthetic
          source material that expresses it. Review the source and approve exact
          Evidence spans for each expected relationship. The answer key is never
          inferred retrospectively from model output.
        </p>
        <div className="evaluation-inputs">
          <div>
            <h4>Source given to the extractor</h4>
            <p>
              The model receives only the synthetic source, proposes relationships,
              and selects supporting text. Deterministic code validates those
              proposals and constructs the canonical graph.
            </p>
          </div>
          <div>
            <h4>Answer key kept separate</h4>
            <p>
              The expected relationships and their approved Evidence stay hidden
              from the extractor. They supply the reference for comparison after
              graph construction.
            </p>
          </div>
        </div>
        <div className="evaluation-comparison">
          <h4>Deterministic comparison</h4>
          <p>
            Compare the constructed graph with the answer key to identify correct,
            additional, and missed relationships. For correct relationships, check
            whether at least one attached Evidence span exactly matches an approved
            span. These checks produce the relationship and provenance measures below.
          </p>
        </div>
        <p className="evaluation-boundary">
          This is an offline research path. It does not score professionally
          accepted Matters or run as part of relationship review. Finding a quote
          in the source alone does not establish that it supports the relationship.
        </p>
      </section>

      <table className="evaluation-register" aria-label="Evaluation results">
        <caption>
          <strong>Evaluation results</strong>
          <span>Results will be published here with their scope and research context. The Evergreen sample is a demonstration, not a representative performance claim.</span>
        </caption>
        <thead>
          <tr><th scope="col">Measure</th><th scope="col">Result</th><th scope="col">What it tells us</th></tr>
        </thead>
        <tbody>
          {measures.map((measure) => (
            <tr key={measure.name}>
              <th scope="row">{measure.name}</th>
              <td className="evaluation-result">Not yet published</td>
              <td>{measure.explanation}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <section className="evaluation-context" aria-labelledby="evaluation-context-title">
        <div>
          <h3 id="evaluation-context-title">Context for a future publication</h3>
          <p>
            Benchmark cases define what is being tested; approved Evidence makes
            provenance checkable. Measured results will show where the system
            succeeds and where further work is needed.
          </p>
          <p>
            Publication and aggregation choices remain research work. A future
            release will describe these alongside its results so readers can judge
            what the figures cover.
          </p>
        </div>
        <dl>
          <div><dt>Publication scope</dt><dd>Not yet published</dd></div>
          <div><dt>Case coverage</dt><dd>Not yet published</dd></div>
          <div><dt>Model / run configuration</dt><dd>Not yet published</dd></div>
          <div><dt>Evaluation date</dt><dd>Not yet published</dd></div>
          <div><dt>Aggregation method</dt><dd>Not yet published</dd></div>
        </dl>
      </section>
    </section>
  );
}
