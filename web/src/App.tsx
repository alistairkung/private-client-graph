import { useEffect } from "react";
import { PractitionerApp } from "./PractitionerApp";
import { ShowcaseApp } from "./ShowcaseApp";

export function App() {
  const practitioner = ["/app", "/app/"].includes(window.location.pathname);
  useEffect(() => {
    document.title = practitioner
      ? "Matters · Private Client Graph"
      : "Public showcase · Private Client Graph";
  }, [practitioner]);
  return practitioner ? <PractitionerApp /> : <ShowcaseApp />;
}
