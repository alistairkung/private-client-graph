import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "motion/react";
import { useLandingCopy } from "./copy";
export function TraceWalkthrough() {
  const copy = useLandingCopy();
  const reduced = useReducedMotion();
  const [active, setActive] = useState(0);
  const sections = useRef<(HTMLElement | null)[]>([]);
  const manual = useRef(false);
  const steps = [
    { title: copy.words, body: copy.wordsBody },
    { title: copy.claim, body: copy.claimBody },
    { title: copy.return, body: copy.returnBody },
  ];
  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (manual.current) return;
        const entered = entries.find((entry) => entry.isIntersecting);
        if (entered)
          setActive(sections.current.indexOf(entered.target as HTMLElement));
      },
      { rootMargin: "-35% 0px -35% 0px", threshold: 0 },
    );
    sections.current.forEach((section) => {
      if (section) observer.observe(section);
    });
    const release = () => {
      manual.current = false;
    };
    window.addEventListener("wheel", release, { passive: true });
    window.addEventListener("touchmove", release, { passive: true });
    const key = (event: KeyboardEvent) => {
      if (
        [
          "PageDown",
          "PageUp",
          "ArrowDown",
          "ArrowUp",
          "Home",
          "End",
          " ",
        ].includes(event.key)
      )
        release();
    };
    window.addEventListener("keydown", key);
    return () => {
      observer.disconnect();
      window.removeEventListener("wheel", release);
      window.removeEventListener("touchmove", release);
      window.removeEventListener("keydown", key);
    };
  }, []);
  function choose(index: number) {
    manual.current = true;
    setActive(index);
    sections.current[index]?.scrollIntoView({
      behavior: reduced ? "instant" : "smooth",
      block: "center",
    });
  }
  return (
    <section className="landing-trace" aria-labelledby="landing-trace-title">
      <header>
        <h2 id="landing-trace-title">{copy.traceTitle}</h2>
        <p>{copy.traceIntro}</p>
      </header>
      <div className="landing-trace-layout">
        <div className="landing-trace-stage">
          <div className="landing-thread" aria-hidden="true">
            <div className={active === 0 ? "active" : ""}>
              <span>“</span>
              <i />
              <i />
              <i />
            </div>
            <svg viewBox="0 0 300 70">
              <path d="M40 5v25h220v35" />
            </svg>
            <div className={active === 1 ? "active" : ""}>
              <svg viewBox="0 0 180 70">
                <circle cx="25" cy="30" r="16" />
                <path d="M42 30h90M153 12l23 40h-46Z" />
              </svg>
            </div>
            <svg viewBox="0 0 300 70">
              <path d="M260 5v25H40v35" />
            </svg>
            <div className={active === 2 ? "active" : ""}>
              <span className="landing-thread-mark">“</span>
              <i />
              <i />
            </div>
          </div>
          <nav aria-label={copy.step}>
            {steps.map((step, index) => (
              <button
                key={index}
                aria-pressed={active === index}
                onClick={() => choose(index)}
              >
                <span>{index + 1}</span>
                {step.title}
              </button>
            ))}
          </nav>
          <p className="landing-current-step">
            {copy.currentStep}: {steps[active].title}
          </p>
        </div>
        <div className="landing-trace-copy">
          {steps.map((step, index) => (
            <article
              key={index}
              ref={(element) => {
                sections.current[index] = element;
              }}
              className={active === index ? "active" : ""}
            >
              <span className="landing-step-number">{index + 1}</span>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
              <div className="landing-inline-step" aria-hidden="true">
                <svg viewBox="0 0 180 65">
                  <g fill="none" stroke="currentColor" strokeWidth="1.5">
                    {index === 1 ? (
                      <>
                        <circle cx="25" cy="30" r="16" />
                        <path d="M42 30h85M151 12l23 40h-46Z" />
                      </>
                    ) : (
                      <>
                        <path d="M18 12h115v42H18Z M35 25h80M35 34h80M35 43h45" />
                        {index === 2 && <path d="M143 15v29h22m-7-7 7 7-7 7" />}
                      </>
                    )}
                  </g>
                </svg>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
