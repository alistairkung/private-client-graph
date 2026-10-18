import { createRoot } from "react-dom/client";
import { MotionConfig } from "motion/react";
import { LocaleProvider } from "./shared/locale";
import { App } from "./app/App";

createRoot(document.getElementById("root")!).render(
  <MotionConfig reducedMotion="user"><LocaleProvider><App /></LocaleProvider></MotionConfig>,
);
