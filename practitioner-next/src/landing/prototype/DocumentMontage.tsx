import type { ReactNode, RefObject } from "react";
import { motion, useTransform, type MotionValue } from "motion/react";
import type { CanonicalState } from "../../shared/contracts";
import { canonicalSourceExcerpts, sourceEntitySpans } from "../landing-layout";

type DocumentKind = "attendance" | "email" | "timesheet" | "legal";
const formats: { kind: DocumentKind; title: string }[] = [
  { kind: "attendance", title: "Attendance notes" },
  { kind: "email", title: "Emails" },
  { kind: "timesheet", title: "Time sheets" },
  { kind: "legal", title: "Legal documents" },
];

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
      className={`prototype-document prototype-document-${kind}`}
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
  const source = state.sources[0];
  const excerpts = source ? canonicalSourceExcerpts(state, source.id) : [];
  const titleOpacity = useTransform(progress, [0, 0.35, 0.48], [1, 1, 0]);
  return (
    <article
      ref={noteRef}
      aria-hidden={hidden}
      className="prototype-note prototype-document-montage"
    >
      <motion.div
        className="prototype-montage-intro"
        style={reduced ? undefined : { opacity: titleOpacity }}
      >
        <h1>It begins with your documents</h1>
        <p className="prototype-montage-disclosure">
          Product vision · Illustrative document formats.
        </p>
        <div className="prototype-format-list">
          {formats.map((format) => (
            <span key={format.kind}>
              <DocumentIcon kind={format.kind} />
              {format.title}
            </span>
          ))}
        </div>
      </motion.div>
      <div className="prototype-document-deck">
        <DocumentSheet
          kind="attendance"
          index={0}
          progress={progress}
          reduced={reduced}
        >
          <div className="prototype-document-title">
            <DocumentIcon kind="attendance" />
            <h2>Attendance note</h2>
          </div>
          <p className="prototype-document-detail">
            Case 01 · Actual synthetic source excerpts
          </p>
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
                    className="prototype-source-name"
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
          <div className="prototype-document-title">
            <DocumentIcon kind="email" />
            <h2>Email correspondence</h2>
          </div>
          <p className="prototype-document-detail">Illustrative format</p>
          <dl className="prototype-email-header">
            <dt>Subject</dt>
            <dd>Papers for our review</dd>
            <dt>From</dt>
            <dd>Client correspondence</dd>
            <dt>To</dt>
            <dd>Private client team</dd>
          </dl>
          <div className="prototype-email-body">
            <p>Please find the documents for our next meeting.</p>
            <p>
              I have included the family papers and the latest trust documents.
              Please let me know what else would be helpful for the review.
            </p>
            <p>Kind regards</p>
          </div>
        </DocumentSheet>
        <DocumentSheet
          kind="timesheet"
          index={2}
          progress={progress}
          reduced={reduced}
        >
          <div className="prototype-document-title">
            <DocumentIcon kind="timesheet" />
            <h2>Time sheet</h2>
          </div>
          <p className="prototype-document-detail">
            Illustrative format · Matter activity
          </p>
          <table className="prototype-timesheet">
            <thead>
              <tr>
                <th>Activity</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Review family papers</td>
                <td>00:30</td>
              </tr>
              <tr>
                <td>Prepare for client meeting</td>
                <td>00:45</td>
              </tr>
              <tr>
                <td>Record attendance note</td>
                <td>00:20</td>
              </tr>
              <tr>
                <td>Review trust documents</td>
                <td>00:40</td>
              </tr>
            </tbody>
          </table>
          <p className="prototype-timesheet-note">
            A record of work, with the documents and context behind it.
          </p>
        </DocumentSheet>
        <DocumentSheet
          kind="legal"
          index={3}
          progress={progress}
          reduced={reduced}
        >
          <div className="prototype-document-title">
            <DocumentIcon kind="legal" />
            <h2>Legal document</h2>
          </div>
          <p className="prototype-document-detail">
            Illustrative format · Draft structure
          </p>
          <div className="prototype-legal-heading">Trust deed</div>
          <ol className="prototype-legal-clauses">
            <li>
              <strong>Definitions</strong>
              <p>The people, terms and instruments referred to in this deed.</p>
            </li>
            <li>
              <strong>Trustees</strong>
              <p>Appointment, powers and administration of the trust.</p>
            </li>
            <li>
              <strong>Beneficiaries</strong>
              <p>The provisions identifying the beneficiaries of the trust.</p>
            </li>
          </ol>
          <div className="prototype-signature">Signature</div>
        </DocumentSheet>
      </div>
      <motion.p
        className="prototype-scroll-hint"
        style={reduced ? undefined : { opacity: titleOpacity }}
      >
        {reduced
          ? "Then review the working synthetic graph and its full source below."
          : "Scroll through the documents, then follow the connections."}
      </motion.p>
    </article>
  );
}
