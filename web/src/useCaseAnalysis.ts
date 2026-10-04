import { useEffect, useState } from "react";
import { analyseCase, getCase, RequestFailure } from "./api";
import type {
  AnalysisError,
  AnalysisMode,
  CaseAnalysis,
  CaseDetail,
} from "./types";

export function useCaseAnalysis() {
  const [detail, setDetail] = useState<CaseDetail>();
  const [sourceError, setSourceError] = useState<string>();
  const [analysis, setAnalysis] = useState<CaseAnalysis>();
  const [pending, setPending] = useState<AnalysisMode>();
  const [error, setError] = useState<AnalysisError>();
  const [lastMode, setLastMode] = useState<AnalysisMode>();
  useEffect(() => {
    let current = true;
    getCase()
      .then((value) => {
        if (current) setDetail(value);
      })
      .catch((failure) => {
        if (current) setSourceError((failure as Error).message);
      });
    return () => {
      current = false;
    };
  }, []);
  async function run(mode: AnalysisMode) {
    if (pending || (mode === "live" && detail?.live_analysis.state !== "available")) return;
    setPending(mode);
    setLastMode(mode);
    setError(undefined);
    setAnalysis(undefined);
    try {
      setAnalysis(await analyseCase(mode));
    } catch (failure) {
      setError(
        failure instanceof RequestFailure
          ? failure.error
          : {
              stage: "client",
              message: "The analysis could not be displayed. Reload the case.",
              retryable: false,
            },
      );
    } finally {
      if (mode === "live") {
        try {
          setDetail(await getCase());
        } catch {
          setDetail((current) => current && ({
            ...current, live_analysis: { state: "unavailable", resets_at: null },
          }));
        }
      }
      setPending(undefined);
    }
  }
  return { detail, sourceError, analysis, pending, error, lastMode, run };
}
