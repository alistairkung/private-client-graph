import { useEffect, useRef, useSyncExternalStore } from "react";

const navigationEvent = "pcg:navigate";
const navigationRequest = "pcg:request-navigation";
const scrollPositions = new Map<string, number>();
const currentLocation = () => window.location.pathname + window.location.search;
let activeLocation = currentLocation();

function mayLeave(path: string) {
  return window.dispatchEvent(
    new CustomEvent(navigationRequest, { cancelable: true, detail: path }),
  );
}

export function useNavigationLock(locked: boolean) {
  useEffect(() => {
    if (!locked) return;
    const keepOpen = (event: Event) => event.preventDefault();
    window.addEventListener(navigationRequest, keepOpen);
    return () => window.removeEventListener(navigationRequest, keepOpen);
  }, [locked]);
}

export function navigate(path: string, options: { replace?: boolean } = {}) {
  const destination = new URL(path, window.location.href);
  if (
    destination.origin !== window.location.origin ||
    !/^\/app(?:\/|$)/.test(destination.pathname)
  ) {
    throw new Error(
      "Application navigation requires a local practitioner route.",
    );
  }
  scrollPositions.set(currentLocation(), window.scrollY);
  const method = options.replace ? "replaceState" : "pushState";
  window.history[method](
    null,
    "",
    destination.pathname + destination.search + destination.hash,
  );
  activeLocation = currentLocation();
  window.dispatchEvent(new Event(navigationEvent));
}

function subscribe(onChange: () => void) {
  const backOrForward = () => {
    const destination = currentLocation();
    if (destination !== activeLocation && !mayLeave(destination)) {
      window.history.pushState(null, "", activeLocation);
      return;
    }
    scrollPositions.set(activeLocation, window.scrollY);
    activeLocation = destination;
    onChange();
  };
  window.addEventListener("popstate", backOrForward);
  window.addEventListener(navigationEvent, onChange);
  return () => {
    window.removeEventListener("popstate", backOrForward);
    window.removeEventListener(navigationEvent, onChange);
  };
}

export function useAppPath() {
  const location = useSyncExternalStore(subscribe, currentLocation);
  activeLocation = location;
  const previous = useRef(location);
  useEffect(() => {
    if (previous.current === location) return;
    previous.current = location;
    window.scrollTo({
      top: scrollPositions.get(location) ?? 0,
      behavior: "instant",
    });
    document.getElementById("main")?.focus({ preventScroll: true });
  }, [location]);
  useEffect(() => {
    const restoration = window.history.scrollRestoration;
    window.history.scrollRestoration = "manual";
    const followLink = (event: MouseEvent) => {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.altKey ||
        event.shiftKey
      )
        return;
      const anchor =
        event.target instanceof Element
          ? event.target.closest<HTMLAnchorElement>("a[href]")
          : null;
      if (
        !anchor ||
        anchor.hasAttribute("download") ||
        (anchor.target && anchor.target !== "_self")
      )
        return;
      const destination = new URL(anchor.href);
      if (
        destination.origin !== window.location.origin ||
        !/^\/app(?:\/|$)/.test(destination.pathname)
      )
        return;
      if (
        destination.pathname + destination.search === currentLocation() &&
        destination.hash
      )
        return;
      event.preventDefault();
      if (mayLeave(destination.pathname + destination.search))
        navigate(destination.pathname + destination.search + destination.hash);
    };
    document.addEventListener("click", followLink);
    return () => {
      document.removeEventListener("click", followLink);
      window.history.scrollRestoration = restoration;
    };
  }, []);
  return location.split("?")[0].replace(/\/$/, "");
}
