import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import "./styles/global.css";
import "./features/showcase/showcase.css";
import "./features/review/review.css";
import "./features/matters/practitioner.css";

createRoot(document.getElementById("root")!).render(<App />);
