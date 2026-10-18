import { useStoryCopy } from "./story-copy";
import type { ReactNode, RefObject } from "react";
import { motion, useTransform, type MotionValue } from "motion/react";
import type { CanonicalState } from "../../shared/contracts";
import { canonicalSourceExcerpts, sourceEntitySpans } from "./landing-layout";

type DocumentKind = "attendance" | "email" | "timesheet" | "legal";
const formats: DocumentKind[] = ["attendance", "email", "timesheet", "legal"];

function DocumentIcon({ kind }: { kind: DocumentKind }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {kind === "email" ? (
        <>
          <rect x="4" y="7" width="24" height="18" rx="2" />
          <path d="m5 9 11 9L27 9" />
        </>
      ) : (
        <>
          <path d="M8 3h11l6 6v20H8Z" />
          <path d="M19 3v7h6" />
          {kind === "timesheet" ? (
            <>
              <path d="M11 15h11M11 20h11M11 25h11M15 13v14" />
            </>
          ) : kind === "legal" ? (
            <>
              <path d="M12 14h9M12 19h9M12 24h6" />
              <path d="m5 16-2 2 2 2" />
            </>
          ) : (
            <>
              <path d="M12 14h9M12 19h9M12 24h5" />
            </>
          )}
        </>
      )}
    </svg>
  );
}

function DocumentSheet({
  kind,
  index,
  progress,
  reduced,
  children,
}: {
  kind: DocumentKind;
  index: number;
  progress: MotionValue<number>;
  reduced: boolean;
  children: ReactNode;
}) {
  const active = index * 0.075;
  const restingX = [0, 62, -58, 28][index];
  const restingY = [0, -12, 14, -5][index];
  const restingRotate = [0, 8, -7, 4][index];
  const x = useTransform(
    progress,
    [0, active, active + 0.025, 0.3, 0.36],
    [restingX, restingX, 0, 0, 0],
  );
  const y = useTransform(
    progress,
    [0, active, active + 0.025, 0.3, 0.36],
    [restingY, restingY, -5, -5, 0],
  );
  const rotate = useTransform(
    progress,
    [0, active, active + 0.025, 0.3, 0.36],
    [restingRotate, restingRotate, 0, 0, 0],
  );
  const opacity = useTransform(
    progress,
    index === 0 ? [0, 0.44, 0.67] : [0, 0.3, 0.36],
    [1, 1, 0],
  );
  const zIndex = useTransform(() => {
    const time = progress.get();
    const front = time >= 0.3 ? 0 : Math.min(3, Math.floor(time / 0.075));
    return front === index ? 5 : 4 - index;
  });
  return (
    <motion.div
      data-document-kind={kind}
      className={`landing-story-document landing-story-document-${kind}`}
      style={
        reduced
          ? undefined
          : {
              x: index === 0 ? 0 : x,
              y: index === 0 ? 0 : y,
              rotate: index === 0 ? 0 : rotate,
              opacity,
              zIndex,
            }
      }
    >
      {children}
    </motion.div>
  );
}

export function DocumentMontage({
  state,
  progress,
  reduced,
  noteRef,
  hidden,
}: {
  state: CanonicalState;
  progress: MotionValue<number>;
  reduced: boolean;
  noteRef: RefObject<HTMLElement | null>;
  hidden: boolean;
}) {
  const copy = useStoryCopy();
  const source = state.sources[0];
  const excerpts = source ? canonicalSourceExcerpts(state, source.id) : [];
  const titleOpacity = useTransform(progress, [0, 0.35, 0.48], [1, 1, 0]);
  return (
    <article
      ref={noteRef}
      aria-hidden={hidden}
      className="landing-story-note landing-story-document-montage"
    >
      <motion.div
        className="landing-story-montage-intro"
        style={reduced ? undefined : { opacity: titleOpacity }}
      >
        <h2>{copy.title}</h2>
        <p className="landing-story-montage-disclosure">{copy.vision}</p>
        <div className="landing-story-format-list">
          {formats.map((kind) => (
            <span key={kind}>
              <DocumentIcon kind={kind} />
              {copy[kind]}
            </span>
          ))}
        </div>
      </motion.div>
      <div className="landing-story-document-deck">
        <DocumentSheet
          kind="attendance"
          index={0}
          progress={progress}
          reduced={reduced}
        >
          <div className="landing-story-document-title">
            <DocumentIcon kind="attendance" />
            <h3>{copy.attendanceTitle}</h3>
          </div>
          <p className="landing-story-document-detail">{copy.excerpts}</p>
          {excerpts.map((text) => (
            <p key={text}>
              {sourceEntitySpans(
                text,
                state.entities.map((item) => item.name),
              ).map((part, index) => {
                const entity = part.entity
                  ? state.entities.find((item) => item.name === part.text)
                  : undefined;
                return entity ? (
                  <span
                    key={index}
                    className="landing-story-source-name"
                    data-entity-name={entity.name}
                    data-source-entity-id={entity.id}
                  >
                    {part.text}
                  </span>
                ) : (
                  part.text
                );
              })}
            </p>
          ))}
        </DocumentSheet>
        <DocumentSheet
          kind="email"
          index={1}
          progress={progress}
          reduced={reduced}
        >
          <div className="landing-story-document-title">
            <DocumentIcon kind="email" />
            <h3>{copy.emailTitle}</h3>
          </div>
          <p className="landing-story-document-detail">{copy.illustrative}</p>
          <dl className="landing-story-email-header">
            <dt>{copy.subject}</dt>
            <dd>{copy.emailSubject}</dd>
            <dt>{copy.from}</dt>
            <dd>{copy.emailFrom}</dd>
            <dt>{copy.to}</dt>
            <dd>{copy.emailTo}</dd>
          </dl>
          <div className="landing-story-email-body">
            <p>{copy.emailOpening}</p>
            <p>{copy.emailBody}</p>
            <p>{copy.emailClose}</p>
          </div>
        </DocumentSheet>
        <DocumentSheet
          kind="timesheet"
          index={2}
          progress={progress}
          reduced={reduced}
        >
          <div className="landing-story-document-title">
            <DocumentIcon kind="timesheet" />
            <h3>{copy.timesheetTitle}</h3>
          </div>
          <p className="landing-story-document-detail">{copy.activity}</p>
          <table className="landing-story-timesheet">
            <thead>
              <tr>
                <th>{copy.activityHeading}</th>
                <th>{copy.time}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{copy.reviewPapers}</td>
                <td>00:30</td>
              </tr>
              <tr>
                <td>{copy.prepare}</td>
                <td>00:45</td>
              </tr>
              <tr>
                <td>{copy.record}</td>
                <td>00:20</td>
              </tr>
              <tr>
                <td>{copy.reviewTrust}</td>
                <td>00:40</td>
              </tr>
            </tbody>
          </table>
          <p className="landing-story-timesheet-note">{copy.timeNote}</p>
        </DocumentSheet>
        <DocumentSheet
          kind="legal"
          index={3}
          progress={progress}
          reduced={reduced}
        >
          <div className="landing-story-document-title">
            <DocumentIcon kind="legal" />
            <h3>{copy.legalTitle}</h3>
          </div>
          <p className="landing-story-document-detail">{copy.draft}</p>
          <div className="landing-story-legal-heading">{copy.deed}</div>
          <ol className="landing-story-legal-clauses">
            <li>
              <strong>{copy.definitions}</strong>
              <p>{copy.definitionsBody}</p>
            </li>
            <li>
              <strong>{copy.trustees}</strong>
              <p>{copy.trusteesBody}</p>
            </li>
            <li>
              <strong>{copy.beneficiaries}</strong>
              <p>{copy.beneficiariesBody}</p>
            </li>
          </ol>
          <div className="landing-story-signature">{copy.signature}</div>
        </DocumentSheet>
      </div>
      <motion.p
        className="landing-story-scroll-hint"
        style={reduced ? undefined : { opacity: titleOpacity }}
      >
        {reduced ? copy.staticHint : copy.scroll}
      </motion.p>
    </article>
  );
}
