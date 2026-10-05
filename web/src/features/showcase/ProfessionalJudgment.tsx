import type { ReactNode } from "react";
import createMatter from "./assets/create-matter.png";
import proposalReview from "./assets/proposal-review.png";
import wholeGraphConfirmation from "./assets/confirm-matter.png";
import acceptedMatter from "./assets/accepted-matter.png";
import createMatterMobile from "./assets/create-matter-mobile.png";
import proposalReviewMobile from "./assets/proposal-review-mobile.png";
import wholeGraphConfirmationMobile from "./assets/confirm-matter-mobile.png";
import acceptedMatterMobile from "./assets/accepted-matter-mobile.png";

export function ProfessionalJudgment() {
  return (
    <section className="professional-judgment" aria-labelledby="professional-judgment-title">
      <header className="judgment-introduction">
        <h2 id="professional-judgment-title">A proposed graph still needs professional judgment.</h2>
        <p>
          The practitioner workflow separates a machine proposal from the decision
          to accept it. These static captures show the existing application using
          synthetic material; the controls pictured here are not active.
        </p>
      </header>

      <div className="judgment-stage">
        <div className="judgment-copy">
          <h3>Begin with a synthetic source.</h3>
          <p>
            Create Matter starts with one synthetic text-layer PDF. Its extracted,
            finalized text becomes the Authoritative Source used for analysis and
            review. The PDF is an acquisition format and is not retained.
          </p>
          <p className="judgment-annotation">
            <strong>Interpretation.</strong> The model proposes relationships from
            the source language. This interpretation is probabilistic: it can
            miss or misinterpret relationships. Deterministic code then constructs
            the graph and checks its structure.
          </p>
        </div>
        <ProductCapture
          source={createMatter} mobileSource={createMatterMobile}
          width={2072} height={1764} mobileHeight={1902}
          title="Create Matter"
          alt="Create Matter screen with synthetic Matter identity, a text-layer PDF, and the synthetic-material confirmation.">
          One synthetic PDF begins the practitioner workflow. This is separate
          from the public sample analysis, which is never saved as a Matter.
        </ProductCapture>
      </div>

      <div className="judgment-stage">
        <div className="judgment-copy">
          <h3>Inspect the proposal and its Evidence.</h3>
          <p>
            Successful analysis creates a durable Matter Proposal: mechanically
            valid proposed state awaiting professional review. A practitioner can
            select relationships, inspect their exact Evidence,
            and read the highlighted passages in the Authoritative Source text.
          </p>
          <p className="judgment-annotation">
            <strong>Mechanical checks.</strong> Deterministic code handles identifiers,
            normalization, references, structural validation, graph construction,
            and exact quote occurrence. Finding a quote in the source does not
            prove that it supports the relationship claimed.
          </p>
        </div>
        <ProductCapture
          source={proposalReview} mobileSource={proposalReviewMobile}
          width={2072} height={1672} mobileHeight={1840}
          title="Matter Proposal review"
          alt="Matter Proposal: Alice Example is parent of Ben Example. The same sentence appears as Evidence and is highlighted in the Authoritative Source.">
          Evidence is highlighted in extracted text, not on the original PDF
          page. This workflow does not provide OCR or PDF-coordinate highlighting.
        </ProductCapture>
      </div>

      <div className="judgment-stage">
        <div className="judgment-copy">
          <h3>Accept the whole graph.</h3>
          <p>
            The practitioner explicitly confirms the whole proposal. Confirmation
            creates the Matter and copies the proposed graph unchanged into its
            professionally accepted current state, together with its source and
            Matter identity.
          </p>
          <p className="judgment-annotation">
            <strong>Professional judgment.</strong> Acceptance records the
            practitioner’s decision. It does not guarantee legal or semantic
            correctness. The current workflow has no relationship editing,
            correction, or partial acceptance.
          </p>
        </div>
        <div className="judgment-confirmation-captures">
          <ProductCapture
            source={wholeGraphConfirmation} mobileSource={wholeGraphConfirmationMobile}
            width={1320} height={214} mobileHeight={306}
            title="Whole-graph confirmation"
            alt="Matter Proposal decision explaining whole-graph acceptance and the Confirm whole graph and create Matter action.">
            The confirmation action applies to the entire proposed graph.
          </ProductCapture>
          <ProductCapture
            source={acceptedMatter} mobileSource={acceptedMatterMobile}
            width={2072} height={1672} mobileHeight={1840}
            title="Accepted Matter review"
            alt="Accepted Matter: Alice Example remains parent of Ben Example, with the same Evidence and highlighted source passage as the proposal.">
            The same graph after confirmation. Its status has changed; its
            relationships have not.
          </ProductCapture>
        </div>
      </div>
    </section>
  );
}

function ProductCapture({ source, mobileSource, width, height, mobileHeight, title, alt, children }: {
  source: string;
  mobileSource: string;
  width: number;
  height: number;
  mobileHeight: number;
  title: string;
  alt: string;
  children: ReactNode;
}) {
  return (
    <figure className="practitioner-capture">
      <picture className="practitioner-capture-image">
        <source media="(max-width: 600px)" srcSet={mobileSource} width={700} height={mobileHeight} />
        <img src={source} width={width} height={height} alt={alt} loading="lazy" />
      </picture>
      <figcaption>
        <strong>{title}.</strong> {children}
        <a href={source} target="_blank" rel="noreferrer">View full-size capture<span className="visually-hidden">: {title} (opens in a new tab)</span></a>
      </figcaption>
    </figure>
  );
}
