import { useEffect, useState } from "react";
import { useLocale } from "../../shared/locale";
import { Icon } from "../../shared/Icon";
import { PublicHeader } from "../../shared/public/PublicHeader";
import { useLandingCopy } from "./copy";
import {
  getPublicExample,
  publicDestination,
  type PublicExample,
} from "./landing-api";
import { DocumentStory } from "./DocumentStory";
import "./landing.css";
export default function LandingPage() {
  return <LandingContent />;
}

export { LandingPage };
function LandingContent() {
  const copy = useLandingCopy();
  const { locale } = useLocale();
  const [example, setExample] = useState<PublicExample>();
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setFailed(false);
    getPublicExample(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setExample(data);
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [attempt]);
  useEffect(() => {
    document.title =
      locale === "en"
        ? "Build the structure. Keep the Evidence. | Private Client Graph"
        : "追溯每项关系的来源 | Private Client Graph";
  }, [locale]);
  return (
    <div className="landing">
      <a className="landing-skip" href="#landing-main">
        {locale === "en" ? "Skip to content" : "跳至内容"}
      </a>
      <PublicHeader />
      <main id="landing-main">
        <section className="landing-opening">
          <h1>{copy.headline}</h1>
          <div>
            <p className="landing-intro">{copy.intro}</p>
            <p>{copy.description}</p>
            <a className="landing-action" href="#explore-example">
              {copy.explore}
              <Icon name="arrow" />
            </a>
          </div>
        </section>
        <div className="landing-boundary">
          <span aria-hidden="true" />
          {copy.boundary}
        </div>
        <section
          id="explore-example"
          className="landing-example-shell"
          aria-label={copy.curated}
        >
          {example ? (
            <DocumentStory state={example.state} />
          ) : failed ? (
            <div className="landing-load-error" role="alert">
              <h2>{copy.error}</h2>
              <button onClick={() => setAttempt((value) => value + 1)}>
                {copy.retry}
              </button>
              <a href={publicDestination("/app")}>{copy.fullDemo}</a>
            </div>
          ) : (
            <div className="landing-loading" role="status">
              {copy.loading}
              <div />
              <div />
              <div />
            </div>
          )}
        </section>
        <section className="landing-acceptance">
          <div>
            <h2>{copy.acceptance}</h2>
            <p>{copy.acceptanceBody}</p>
            <a href="/app" className="landing-action landing-action-light">
              {copy.enter}
              <Icon name="arrow" />
            </a>
          </div>
          <div className="landing-decision-thread">
            {[
              { title: copy.read, text: copy.readText },
              { title: copy.inspect, text: copy.inspectText },
              { title: copy.decide, text: copy.decideText },
            ].map((item, index) => (
              <div key={item.title}>
                <span>{index + 1}</span>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
              </div>
            ))}
            <p>{copy.acceptanceNote}</p>
          </div>
        </section>
        <section className="landing-research">
          <h2>{copy.researchTitle}</h2>
          <div>
            <p>{copy.researchBody}</p>
            <a
              className="landing-text-link"
              href={publicDestination("/research-results")}
            >
              {copy.researchLink}
              <Icon name="arrow" />
            </a>
            <p className="landing-research-boundary">{copy.researchNote}</p>
          </div>
        </section>
        <section className="landing-close">
          <h2>{copy.closing}</h2>
          <a className="landing-action" href={publicDestination("/app")}>
            {copy.fullDemo}
            <Icon name="arrow" />
          </a>
        </section>
      </main>
      <footer>
        <a className="landing-brand" href="/">
          {copy.footer}
        </a>
        <p>{copy.footerNote}</p>
        <p>{copy.boundary}</p>
        <a href={publicDestination("/research-results")}>{copy.research}</a>
      </footer>
    </div>
  );
}
