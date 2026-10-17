import { useEffect, useState } from "react";
import { getShowcaseCase, getShowcaseCases } from "./api";
import type { ShowcaseCase, ShowcaseCaseSummary } from "./types";

export function useShowcaseCases() {
  const [cases, setCases] = useState<ShowcaseCaseSummary[]>([]);
  const [caseId, setCaseId] = useState("case-01");
  const [detail, setDetail] = useState<ShowcaseCase>();
  const [catalogueFailed, setCatalogueFailed] = useState(false);
  const [detailFailed, setDetailFailed] = useState(false);
  const failed = catalogueFailed || detailFailed;
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setCatalogueFailed(false);
    getShowcaseCases().then(value => { if (active) setCases(value); }, () => { if (active) setCatalogueFailed(true); });
    return () => { active = false; };
  }, [retry]);
  useEffect(() => {
    let active = true;
    setDetail(undefined); setDetailFailed(false);
    getShowcaseCase(caseId).then(value => { if (active) setDetail(value); }, () => { if (active) setDetailFailed(true); });
    return () => { active = false; };
  }, [caseId, retry]);
  return { cases, caseId, setCaseId, detail, failed, reload: () => setRetry(value => value + 1) };
}
