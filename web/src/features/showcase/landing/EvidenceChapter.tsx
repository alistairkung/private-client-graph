import "./evidence-chapter.css";

export function EvidenceChapter() {
  return (
    <section id="approach" className="evidence-chapter" aria-labelledby="evidence-title">
      <div className="folio-width evidence-composition">
        <h2 id="evidence-title">A relationship.<br />Its exact Evidence.</h2>
        <span className="evidence-margin" aria-hidden="true">Evidence</span>
        <blockquote>
          Alice Chen confirmed that <span className="folio-highlight">she and David Chen are spouses.</span>
        </blockquote>
        <p>Follow the connection back to the words.</p>
      </div>
    </section>
  );
}
