import type { AnalysisError } from "./types";

export function analysisFailureMessage(error: AnalysisError): string {
  switch (error.stage) {
    case "graph": return "Relationship validation failed. Load the sample analysis to continue.";
    case "connection": return "The application could not be reached. Check the local server and try again.";
    case "client": return "The analysis could not be displayed. Reload the case.";
    default: return "Analysis is unavailable. Load the sample analysis to continue.";
  }
}
