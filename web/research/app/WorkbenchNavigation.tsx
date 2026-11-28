export type WorkbenchPage = "run" | "experiments" | "benchmark" | "history";

export function WorkbenchNavigation({ page, benchmark, saving }: {
  page: WorkbenchPage;
  benchmark: boolean;
  saving: boolean;
}) {
  const links = [
    ["run", "#new-run=1", "New run"],
    ["experiments", "#experiments=1", "Experiments"],
    ...(benchmark ? [["benchmark", "#library=1", "Benchmark library"]] : []),
    ["history", "#legacy-history=1", "Legacy history"],
  ];
  return <header className="workbench-masthead">
    <div className="workbench-masthead-inner">
      <div className="workbench-identity">
        <strong>Private Client Graph</strong>
        <span>Research Workbench</span>
      </div>
      <nav aria-label="Workbench navigation">
        {links.map(([key, location, label]) => <a key={key} href={location} aria-current={page === key ? "page" : undefined}
          onClick={event => { if (saving) event.preventDefault(); }}>{label}</a>)}
      </nav>
    </div>
  </header>;
}
