import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { request } from "./api";
import { clearSessionState } from "./session-state";
import { useLocale } from "./locale";

export interface Access {
  can_write: boolean;
  sign_in_available: boolean;
}
type AccessState =
  | { status: "loading" | "error" }
  | { status: "ready"; access: Access };
const Context = createContext<{
  state: AccessState;
  access?: Access;
  refresh: () => void;
}>({ state: { status: "loading" }, refresh: () => {} });
export const accessDeniedEvent = "pcg:access-denied";

export function AccessProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AccessState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const wasWriter = useRef(false);
  function refresh() {
    setState({ status: "loading" });
    setAttempt(value => value + 1);
  }
  useEffect(() => {
    let active = true;
    request("/api/access")
      .then(response => response.json())
      .then((access: Access) => {
        if (!active) return;
        if (wasWriter.current && !access.can_write) clearSessionState();
        wasWriter.current = access.can_write;
        setState({ status: "ready", access });
      })
      .catch(() => {
        if (active) setState({ status: "error" });
      });
    return () => { active = false; };
  }, [attempt]);
  useEffect(() => {
    const denied = () => {
      clearSessionState();
      wasWriter.current = false;
      refresh();
    };
    window.addEventListener(accessDeniedEvent, denied);
    return () => window.removeEventListener(accessDeniedEvent, denied);
  }, []);
  return (
    <Context.Provider value={{
      state,
      access: state.status === "ready" ? state.access : undefined,
      refresh,
    }}>
      {children}
    </Context.Provider>
  );
}
export const useAccess = () => useContext(Context);

export function AccessNotice() {
  const { state, refresh } = useAccess();
  const { t } = useLocale();
  if (state.status === "loading") {
    return <p className="access-notice" role="status">{t("Checking sign-in and editing access…")}</p>;
  }
  if (state.status === "error") {
    return (
      <div className="access-notice" role="alert">
        <p>{t("Sign-in and editing access could not be checked. You can still read Matters and proposals.")}</p>
        <button onClick={refresh}>{t("Retry access check")}</button>
      </div>
    );
  }
  return null;
}

export function WriteGate({ children }: { children?: ReactNode }) {
  const { access } = useAccess();
  const { t } = useLocale();
  if (!access) return null;
  if (access.can_write) return children;
  if (access.sign_in_available) {
    return (
      <a href={"/auth/login?next=" + encodeURIComponent(window.location.pathname)}>
        {t("Sign in to make changes")}
      </a>
    );
  }
  return <p>{t("Sign-in is currently unavailable. You can still read Matters and proposals.")}</p>;
}
