import {
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type PointerEvent,
} from "react";
import {
  animate,
  motion,
  useMotionValue,
  useReducedMotion,
} from "motion/react";
import "./view-switch.css";

interface ViewOption<Value extends string> {
  value: Value;
  label: string;
  controls: string;
}
interface Gesture {
  id: number;
  start: number;
  origin: number;
  dragged: boolean;
}
const spring = {
  type: "spring" as const,
  stiffness: 700,
  damping: 53,
  mass: 1,
};

export function ViewSwitch<Value extends string>({
  value,
  options,
  onChange,
  label,
  id,
}: {
  value: Value;
  options: readonly [ViewOption<Value>, ViewOption<Value>];
  onChange: (value: Value) => void;
  label: string;
  id?: string;
}) {
  const generated = useId();
  const scope = id ?? generated;
  const reduced = useReducedMotion();
  const track = useRef<HTMLDivElement>(null);
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  const gesture = useRef<Gesture | undefined>(undefined);
  const selected = useRef(value);
  selected.current = value;
  const travel = useRef(72);
  const x = useMotionValue(0);
  const animation = useRef<ReturnType<typeof animate> | null>(null);
  const suppressClick = useRef(false);
  const [dragging, setDragging] = useState(false);
  const [pillWidth, setPillWidth] = useState(72);
  const indexOf = (current: Value) =>
    options.findIndex((option) => option.value === current);
  function snap(index: number, immediate = false) {
    animation.current?.stop();
    const destination = index * travel.current;
    if (reduced || immediate) x.set(destination);
    else animation.current = animate(x, destination, spring);
  }
  function commit(index: number) {
    if (options[index].value !== selected.current)
      onChange(options[index].value);
    snap(index);
  }
  function cancel() {
    if (!gesture.current) return;
    gesture.current = undefined;
    suppressClick.current = true;
    setDragging(false);
    snap(indexOf(selected.current));
  }
  useLayoutEffect(() => {
    function measure() {
      if (gesture.current) cancel();
      const width = (track.current?.getBoundingClientRect().width || 152) - 8;
      travel.current = width / 2;
      setPillWidth(width / 2);
      snap(indexOf(selected.current), true);
    }
    measure();
    const observer =
      typeof ResizeObserver === "undefined"
        ? null
        : new ResizeObserver(measure);
    if (track.current) observer?.observe(track.current);
    return () => observer?.disconnect();
  }, [options[0].label, options[1].label]);
  useEffect(() => {
    if (!gesture.current) snap(indexOf(value));
  }, [value, reduced]);
  useEffect(
    () => () => {
      animation.current?.stop();
      gesture.current = undefined;
      x.set(indexOf(selected.current) * travel.current);
    },
    [],
  );
  function begin(event: PointerEvent<HTMLDivElement>) {
    if (event.button !== 0 || !event.isPrimary) return;
    animation.current?.stop();
    suppressClick.current = false;
    gesture.current = {
      id: event.pointerId,
      start: event.clientX,
      origin: x.get(),
      dragged: false,
    };
  }
  function move(event: PointerEvent<HTMLDivElement>) {
    const current = gesture.current;
    if (!current || current.id !== event.pointerId) return;
    const distance = event.clientX - current.start;
    if (!current.dragged && Math.abs(distance) < 4) return;
    if (!current.dragged) {
      current.dragged = true;
      setDragging(true);
      event.currentTarget.setPointerCapture(event.pointerId);
    }
    x.set(Math.max(0, Math.min(travel.current, current.origin + distance)));
  }
  function release(event: PointerEvent<HTMLDivElement>) {
    const current = gesture.current;
    if (!current || current.id !== event.pointerId) return;
    gesture.current = undefined;
    if (!current.dragged) return;
    const index = x.get() >= travel.current / 2 ? 1 : 0;
    suppressClick.current = true;
    setDragging(false);
    commit(index);
    buttons.current[index]?.focus({ preventScroll: true });
    if (event.currentTarget.hasPointerCapture(event.pointerId))
      event.currentTarget.releasePointerCapture(event.pointerId);
  }
  function keyboard(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape" && gesture.current) {
      event.preventDefault();
      cancel();
      return;
    }
    const keys = ["ArrowLeft", "ArrowRight", "Home", "End"];
    if (!keys.includes(event.key)) return;
    event.preventDefault();
    cancel();
    const index = event.key === "Home" || event.key === "ArrowLeft" ? 0 : 1;
    suppressClick.current = false;
    commit(index);
    buttons.current[index]?.focus({ preventScroll: true });
  }
  return (
    <div
      ref={track}
      className="view-switch"
      role="tablist"
      aria-label={label}
      data-dragging={dragging || undefined}
      onPointerDown={begin}
      onPointerMove={move}
      onPointerUp={release}
      onPointerCancel={cancel}
      onLostPointerCapture={() => {
        if (gesture.current?.dragged) cancel();
      }}
      onKeyDown={keyboard}
      onClickCapture={(event) => {
        if (suppressClick.current && event.detail !== 0) {
          event.preventDefault();
          event.stopPropagation();
        }
        suppressClick.current = false;
      }}
    >
      <motion.span
        aria-hidden="true"
        className="view-switch-pill"
        style={{ x, width: pillWidth }}
      />
      {options.map((option, index) => (
        <button
          type="button"
          key={option.value}
          ref={(element) => {
            buttons.current[index] = element;
          }}
          id={scope + "-" + option.value}
          role="tab"
          aria-selected={value === option.value}
          aria-controls={option.controls}
          tabIndex={value === option.value ? 0 : -1}
          onClick={() => commit(index)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
