import {
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";

// Presentation state stays in this tab's memory and is cleared at sign-out.
const values = new Map<string, unknown>();
export const sessionClearedEvent = "pcg:session-cleared";

export function useSessionState<T>(
  key: string,
  initial: T | (() => T),
): [T, Dispatch<SetStateAction<T>>] {
  const initialValue = useRef(initial);
  const [value, setValue] = useState<T>(() =>
    values.has(key)
      ? (values.get(key) as T)
      : typeof initial === "function"
        ? (initial as () => T)()
        : initial,
  );
  useEffect(() => {
    values.set(key, value);
  }, [key, value]);
  useEffect(() => {
    const reset = () =>
      setValue(() =>
        typeof initialValue.current === "function"
          ? (initialValue.current as () => T)()
          : initialValue.current,
      );
    window.addEventListener(sessionClearedEvent, reset);
    return () => window.removeEventListener(sessionClearedEvent, reset);
  }, []);
  return [value, setValue];
}

export function clearSessionState() {
  values.clear();
  window.dispatchEvent(new Event(sessionClearedEvent));
}

export function forgetSessionState(key: string) {
  values.delete(key);
}
