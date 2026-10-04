import "./practitioner.css";

export function PractitionerApp() {
  return (
    <div className="practitioner-shell">
      <header className="ledger-header">
        <div className="ledger-header-inner ledger-width">
          <a href="/app" className="ledger-brand">
            <span className="brand-symbol" aria-hidden="true">⌘</span>
            Private Client Graph
          </a>
          <nav aria-label="Practitioner application">
            <a href="/app" aria-current="page">Matters</a>
          </nav>
          <a href="/" className="ledger-showcase" aria-label="Public showcase">
            <span className="ledger-wide-label">Public </span>showcase
          </a>
        </div>
      </header>
      <main className="ledger-content ledger-width">
        <h1>Matters</h1>
        <p className="ledger-intro">
          Open a Matter to review relationships and the source evidence supporting them.
        </p>
        <table className="matter-register" aria-label="Matters">
          <thead>
            <tr><th scope="col">Matter reference</th><th scope="col">Matter</th></tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={2}>
                <div className="ledger-empty">
                  <p>No Matters available</p>
                  <p>This read-only application does not currently contain any Matters.</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </main>
      <footer className="ledger-footer ledger-width">
        <span>Private Client Graph</span>
        <span>Read-only · Synthetic material only</span>
      </footer>
    </div>
  );
}
