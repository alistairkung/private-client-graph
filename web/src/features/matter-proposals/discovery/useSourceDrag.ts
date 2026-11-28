import { useEffect, useRef, useState, type PointerEvent } from "react";

type SourceDrag = { from: number; to: number };
type SourcePointer = { id: number; y: number; startY: number; from: number; to: number | null };

export function useSourceDrag(move: (from: number, to: number) => void) {
  const scroller = useRef<HTMLDivElement>(null);
  const pointer = useRef<SourcePointer | null>(null);
  const frame = useRef(0);
  const [drag, setDrag] = useState<SourceDrag>();

  useEffect(() => () => cancelAnimationFrame(frame.current), []);

  function cancel() {
    cancelAnimationFrame(frame.current);
    pointer.current = null;
    setDrag(undefined);
  }

  function targetAt(container: HTMLElement, y: number) {
    const rows = Array.from(container.querySelectorAll<HTMLElement>("[data-source-position]"));
    const target = rows.find(row => row.getBoundingClientRect().bottom > y) ?? rows.at(-1);
    return target ? Number(target.dataset.sourcePosition) : null;
  }

  function updateTarget() {
    const active = pointer.current;
    const container = scroller.current;
    if (active?.to == null || !container) return;
    const bounds = container.getBoundingClientRect();
    const edge = 32;
    const before = container.scrollTop;
    if (active.y < bounds.top + edge) container.scrollTop -= 10;
    else if (active.y > bounds.bottom - edge) container.scrollTop += 10;

    const y = Math.max(bounds.top, Math.min(active.y, bounds.bottom - 1));
    const to = targetAt(container, y);
    if (to !== null && to !== active.to) {
      active.to = to;
      setDrag({ from: active.from, to });
    }
    if (before !== container.scrollTop) frame.current = requestAnimationFrame(updateTarget);
  }

  function start(event: PointerEvent<HTMLElement>, from: number) {
    if (!event.isPrimary || event.button !== 0) return;
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    pointer.current = { id: event.pointerId, y: event.clientY, startY: event.clientY, from, to: null };
  }

  function track(event: PointerEvent<HTMLElement>) {
    const active = pointer.current;
    if (!active || active.id !== event.pointerId) return;
    active.y = event.clientY;
    if (active.to === null && Math.abs(active.y - active.startY) >= 5) {
      active.to = active.from;
      setDrag({ from: active.from, to: active.from });
    }
    if (active.to !== null) {
      cancelAnimationFrame(frame.current);
      updateTarget();
    }
  }

  function drop(event: PointerEvent<HTMLElement>) {
    const active = pointer.current;
    if (!active || active.id !== event.pointerId) return;
    const container = scroller.current;
    cancel();
    if (!container || active.to === null) return;

    const bounds = container.getBoundingClientRect();
    const { clientX: x, clientY: y } = event;
    if (x < bounds.left || x > bounds.right || y < bounds.top || y >= bounds.bottom) return;

    const to = targetAt(container, y);
    if (to !== null) move(active.from, to);
  }

  function handle(from: number) {
    return {
      onPointerDown: (event: PointerEvent<HTMLElement>) => start(event, from),
      onPointerMove: track,
      onPointerUp: drop,
      onPointerCancel: cancel,
      onLostPointerCapture: cancel,
    };
  }

  return { drag, scroller, handle };
}
