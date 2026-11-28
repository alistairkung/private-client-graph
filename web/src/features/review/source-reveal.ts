import { animate } from "motion";

/** Move only this reader; user input and a newer request always take control. */
export function revealSource(
  reader: HTMLElement,
  target: HTMLElement,
  reduced: boolean,
  focus: boolean,
  remember: (position: number) => void = () => {},
  onInterrupt: () => void = () => {},
) {
  const firstLine = target.getClientRects()[0] ?? target.getBoundingClientRect();
  const destination = Math.max(
    0,
    Math.min(
      Math.max(0, reader.scrollHeight - reader.clientHeight),
      reader.scrollTop +
        firstLine.top -
        reader.getBoundingClientRect().top -
        contextOffset(reader, target, firstLine.height),
    ),
  );
  let stopped = false;
  const animation = reduced
    ? undefined
    : animate(reader.scrollTop, destination, {
        duration: 0.28,
        ease: [0.22, 1, 0.36, 1],
        onUpdate: (value) => {
          if (!stopped) {
            reader.scrollTop = value;
            remember(reader.scrollTop);
          }
        },
      });
  if (reduced) {
    reader.scrollTop = destination;
    remember(reader.scrollTop);
  }
  if (focus) target.focus({ preventScroll: true });
  const cancel = () => {
    stopped = true;
    animation?.stop();
  };
  const interrupt = () => {
    cancel();
    onInterrupt();
  };
  const key = (event: KeyboardEvent) => {
    if (
      [
        "ArrowUp",
        "ArrowDown",
        "PageUp",
        "PageDown",
        "Home",
        "End",
        " ",
      ].includes(event.key)
    )
      interrupt();
  };
  const visibility = () => {
    if (document.hidden) interrupt();
  };
  reader.addEventListener("wheel", interrupt, { passive: true });
  reader.addEventListener("touchstart", interrupt, { passive: true });
  reader.addEventListener("pointerdown", interrupt);
  reader.addEventListener("keydown", key);
  document.addEventListener("visibilitychange", visibility);
  return () => {
    cancel();
    reader.removeEventListener("wheel", interrupt);
    reader.removeEventListener("touchstart", interrupt);
    reader.removeEventListener("pointerdown", interrupt);
    reader.removeEventListener("keydown", key);
    document.removeEventListener("visibilitychange", visibility);
  };
}

function contextOffset(reader: HTMLElement, target: HTMLElement, firstLineHeight: number) {
  const available = Math.min(72, reader.clientHeight * 0.2);
  const lineHeight = Number.parseFloat(getComputedStyle(target.parentElement ?? target).lineHeight);
  if (!Number.isFinite(lineHeight) || lineHeight <= 0) return available;

  // Start before a complete context line, allowing for the leading around the inline mark.
  const leading = Math.max(0, (lineHeight - firstLineHeight) / 2);
  return Math.floor(available / lineHeight) * lineHeight + leading + 2;
}
