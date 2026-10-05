import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import "./styles/global.css";
import "./styles/fonts.css";

createRoot(document.getElementById("root")!).render(<App />);
