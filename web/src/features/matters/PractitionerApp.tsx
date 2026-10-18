import { useEffect, useState } from "react";
import { getAccess, publicAccess, type Access } from "./access";
import { useLocale } from "../../shared/locale";
import { LanguageControl } from "../../shared/LanguageControl";
import "./practitioner.css";
import { AccountMenu } from "./AccountMenu";
import { MatterWorkspace } from "./MatterWorkspace";
import { MatterLedger } from "./MatterLedger";
import { ProposalCollection } from "../matter-proposals/ProposalCollection";
import { CreateMatter } from "../matter-proposals/CreateMatter";
import { ProposalWorkspace } from "../matter-proposals/ProposalWorkspace";
import "../matter-proposals/proposals.css";
import { BrandMark } from "../../shared/brand/BrandMark";

export function PractitionerApp({ matterId, proposalId }: { matterId?: string; proposalId?: string }) {
  const { t } = useLocale();
  const [access, setAccess] = useState<Access>(publicAccess);
  useEffect(() => {
    let active = true;
    getAccess().then(value => { if (active) setAccess(value); }, () => {});
    return () => { active = false; };
  }, []);
  return (
    <div className="practitioner-shell">
      <header className="ledger-header">
        <div className="ledger-header-inner ledger-width">
          <a href="/app" className="ledger-brand">
            <BrandMark />
            Private Client Graph
          </a>
          <nav aria-label={t("Practitioner application")}>
            <a href="/app" aria-current="page">{t("Matters")}</a>
          </nav>
          <div className="app-header-utilities">
            <LanguageControl compact />
            <AccountMenu access={access} />
          </div>
        </div>
      </header>
      <main className="ledger-content ledger-width">
        <div className="practitioner-access">
          <p>{t("This prototype accepts synthetic or fictional material only. It is not suitable for real confidential client information.")}</p>
          <p>{t("Sources, Matter Proposals and Matters are publicly readable, including proposals awaiting confirmation.")}</p>
        </div>
        <PractitionerPage matterId={matterId} proposalId={proposalId} access={access} />
      </main>
      <footer className="ledger-footer ledger-width">
        <span>Private Client Graph</span>
        <span>{t("Synthetic material only")}</span>
      </footer>
    </div>
  );
}

function PractitionerPage({ matterId, proposalId, access }: { matterId?: string; proposalId?: string; access: Access }) {
  const { t } = useLocale();
  const navigate = (path: string) => window.location.assign(path);
  if (matterId) return <MatterWorkspace key={matterId} id={matterId} />;
  if (proposalId === "new") {
    if (access.can_write) return <CreateMatter onNavigate={navigate} />;
    return <p>{access.sign_in_available
      ? <a href="/auth/login?next=/app/matter-proposals/new">{t("Sign in to make changes")}</a>
      : t("Sign-in is currently unavailable. You can still read Matters and proposals.")}</p>;
  }
  if (proposalId) return <ProposalWorkspace key={proposalId} id={proposalId} onNavigate={navigate} canWrite={access.can_write} />;
  return <>
    <div className="ledger-title-row">
      <h1>{t("Matters")}</h1>
      <MatterCreationLink access={access} />
    </div>
    <p className="ledger-intro">{t("Open a Matter or return to a proposal awaiting confirmation.")}</p>
    <ProposalCollection />
    <section className="matter-collection" aria-labelledby="accepted-matters">
      <h2 id="accepted-matters">{t("Accepted Matters")}</h2>
      <p>{t("Return to accepted relationships and their source evidence.")}</p>
      <MatterLedger />
    </section>
  </>;
}


function MatterCreationLink({ access }: { access: Access }) {
  const { t } = useLocale();
  if (access.can_write) return <a className="intake-button" href="/app/matter-proposals/new">{t("Create Matter")}</a>;
  if (access.sign_in_available) return <a href="/auth/login?next=/app">{t("Sign in to make changes")}</a>;
  return null;
}
