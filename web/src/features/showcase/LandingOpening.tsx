import evergreenSample from "./assets/evergreen-sample.png";

export function LandingOpening() {
  return (
    <section className="landing-opening" aria-labelledby="landing-title">
      <div className="opening-copy">
        <h1 id="landing-title">See the relationships. Read the evidence.</h1>
        <p className="opening-description">
          Follow family and trust relationships from synthetic source material
          to the exact passages that support them.
        </p>
        <a className="showcase-action" href="#demonstration">Explore the demonstration</a>
        <p className="prototype-notice">
          Synthetic research prototype. Do not use real client information.
        </p>
      </div>
      <figure className="sample-capture">
        <div className="sample-image" tabIndex={0} role="region" aria-label="Static sample graph capture">
        <img
          src={evergreenSample}
          width="1584"
          height="1022"
          alt="Evergreen sample graph: Alice Chen is settlor of the Trust and spouse of David Chen. Both are parents of Bob Chen. Bob Chen and Carol Wong are beneficiaries."
        />
        </div>
        <figcaption>
          Evergreen Family Trust · Static capture of sample analysis.
          Load the demonstration below to inspect relationships and Evidence.
          <span className="capture-scroll-hint"> Scroll the image sideways to see the complete graph.</span>
        </figcaption>
      </figure>
    </section>
  );
}
