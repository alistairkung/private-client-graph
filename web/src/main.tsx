import { createRoot } from "react-dom/client";
import { LocaleProvider } from "./shared/locale";
import { App } from "./app/App";
import "./styles/global.css";

createRoot(document.getElementById("root")!).render(<LocaleProvider><App /></LocaleProvider>);
