import "./practitioner.css";
import { SignOut } from "./SignOut";
import { MatterWorkspace } from "./MatterWorkspace";
import { MatterLedger } from "./MatterLedger";
import { ProposalCollection } from "../matter-proposals/ProposalCollection";
import { CreateMatter } from "../matter-proposals/CreateMatter";
import { ProposalWorkspace } from "../matter-proposals/ProposalWorkspace";
import "../matter-proposals/proposals.css";

export function PractitionerApp({ matterId, proposalId }: { matterId?: string; proposalId?: string }) {
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
        <div className="practitioner-access">
          <p>This prototype accepts synthetic or fictional material only. It is not suitable for real confidential client information.</p>
          <SignOut />
        </div>
        <PractitionerPage matterId={matterId} proposalId={proposalId} />
      </main>
      <footer className="ledger-footer ledger-width">
        <span>Private Client Graph</span>
        <span>Synthetic material only</span>
      </footer>
    </div>
  );
}

function PractitionerPage({ matterId, proposalId }: { matterId?: string; proposalId?: string }) {
  const navigate = (path: string) => window.location.assign(path);
  if (matterId) return <MatterWorkspace key={matterId} id={matterId} />;
  if (proposalId === "new") return <CreateMatter onNavigate={navigate} />;
  if (proposalId) return <ProposalWorkspace key={proposalId} id={proposalId} onNavigate={navigate} />;
  return <>
    <div className="ledger-title-row"><h1>Matters</h1><a className="intake-button" href="/app/matter-proposals/new">Create Matter</a></div>
    <p className="ledger-intro">Open a Matter to review relationships and the source evidence supporting them.</p>
    <MatterLedger />
    <ProposalCollection />
  </>;
}
