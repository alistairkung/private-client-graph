# Private Google Workspace pilot

## Owner provisioning

**The pilot project, dedicated test account and three OAuth clients are provisioned. Operator consent and seeding succeeded.** The following console steps are based on Google's documentation. Record the outcome of the actual account run separately below. Use one dedicated consumer Gmail account for the signed-in practitioner, the corpus owner and the only OAuth test user. Keep the entire pilot on a private workstation.

1. In a fresh browser profile choose **Create account → For my personal use** and create a new Gmail mailbox. Complete Google's verification, terms and recovery prompts yourself. Use the account exclusively for the fictional corpus. [Create a Google Account](https://support.google.com/accounts/answer/27441)
2. Signed in as that account, open Cloud Console, select the project picker, then **New project**. Create and select a separate project such as **PCG Synthetic Pilot**. In **APIs & Services → Library**, enable **Gmail API** and **Google Drive API** for that project. [Create a project](https://developers.google.com/workspace/guides/create-project) · [Enable APIs](https://developers.google.com/workspace/guides/enable-apis)
3. In **Google Auth Platform → Branding → Get started**, enter the pilot app name, support email and developer contact. Set **Audience → External**, leave publishing status **Testing**, and add the synthetic Gmail address under **Test users**. In **Data Access** declare openid, email, gmail.readonly, drive.readonly and the operator scopes gmail.insert, gmail.labels and drive.file. The three clients request separate grants. [Configure consent](https://developers.google.com/workspace/guides/configure-oauth-consent)
4. In **Google Auth Platform → Clients → Create client**, register the three clients below. Download each client JSON when Google offers the secret, and move the files into the private directory created below. Use the exact HTTPS redirect for each web client. The desktop client's loopback redirect is managed by the operator consent helper. [Create credentials](https://developers.google.com/workspace/guides/create-credentials)

| Client | Type | Authorized redirect | Local filename |
| --- | --- | --- | --- |
| PCG pilot sign-in | Web application | `https://localhost:8444/auth/callback` | `signin.json` |
| PCG pilot discovery | Web application | `https://localhost:8444/auth/workspace/callback` | `discovery.json` |
| Alder v1 seed operator | Desktop app | Desktop loopback | `operator.json` |

Use a terminal in the clean pilot checkout. The host commands below use a POSIX shell, [Google Cloud CLI](https://cloud.google.com/sdk/docs/install), PostgreSQL client/server tools, Node/npm and uv. On macOS use a short private directory path so the Unix socket fits its path-length limit.

```sh
umask 077
export PILOT_DIR="$HOME/.pcg-alder-v1"
mkdir -p "$PILOT_DIR/gcloud" "$PILOT_DIR/socket"
chmod 700 "$PILOT_DIR" "$PILOT_DIR/gcloud" "$PILOT_DIR/socket"
# Move the three downloaded files here using the names in the table.
chmod 600 "$PILOT_DIR/"*.json
export PILOT_ACCOUNT='replace-with-dedicated-address@gmail.com'
export CLOUDSDK_CONFIG="$PILOT_DIR/gcloud"
unset GOOGLE_APPLICATION_CREDENTIALS PGHOSTADDR PGSERVICE
uv sync --locked
```

## Operator consent and seeding

Run the following in the dedicated profile and select the synthetic account on Google's consent screen. The operator grant can insert messages, manage labels and create Drive files. The operator directory holds local refresh credentials. The practitioner web clients use separate credentials and online grants. The operator helper uses Google's desktop loopback OAuth flow because the installed Google CLI requires an additional Cloud Platform scope for its login command. The helper requests only the identity and corpus scopes and saves the refresh grant in the isolated CLI directory. If Google shows `403 access_denied` with “developer-approved testers”, verify the pilot project's **Audience → Test users** entry and select that same dedicated account during consent. [Google desktop OAuth flow](https://google-auth-oauthlib.readthedocs.io/en/latest/reference/google_auth_oauthlib.flow.html) · [Testing audience](https://support.google.com/cloud/answer/15549945)

```sh
uv run --script local_development/workspace_pilot/authorize.py "$PILOT_DIR" "$PILOT_ACCOUNT"
uv run python -m local_development.workspace_pilot.seed "$PILOT_DIR" "$PILOT_ACCOUNT"
uv run python -m local_development.workspace_pilot.seed "$PILOT_DIR" "$PILOT_ACCOUNT"
uv run python -m local_development.workspace_pilot.check "$PILOT_DIR" "$PILOT_ACCOUNT"
```

The operator checks Google's UserInfo response for the expected verified email before any Workspace request. It pins the Google subject and logical-to-provider IDs in private `manifest.json`. The launcher derives both allowlisted subjects from that manifest. Keep the directory outside the repository, sync services, CI artifacts and tickets. A repeat seed verifies existing objects and their bytes or contents. A moved file, changed PDF, altered message or missing object stops the run. The seeder never sends mail.

Each create has a journal entry. If a write fails with an uncertain outcome, keep the manifest. In the dedicated account, inspect the pending stable key (Drive app property `pcgSeed=alder-v1-<key>`, Gmail Message-ID `<pcg-alder-v1-<key>@example.invalid>`, or exact pilot label). Wait for search indexing. Reconcile a uniquely verified object by adding its ID under the pending key in the private manifest and removing `pending`. If absence is independently established, remove only `pending` to retry. Multiple or uncertain matches require investigation. Never clear the manifest to retry against the same corpus.

The corpus uses nine messages, two folders, four PDF objects and a shortcut. Each PDF uses the original binary fixture. The seventh message retains its fictional body and uses the resignation subject, RFC reply headers and Google's parent thread ID to meet Gmail threading rules. Seed verification checks the actual thread and per-message label. Gmail insert uses the fixture Date header as internalDate. [Gmail threads](https://developers.google.com/workspace/gmail/api/guides/threads) · [Gmail insert](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/insert)

## Private deployment

Initialize a dedicated cluster once. PostgreSQL listens on a private Unix socket only. On later launches start the existing cluster and skip initdb and createdb. Use a clean checkout without a deployment .env, and a local shell without external tracing. The application logs no HTTP access lines in this pilot process.

```sh
export PGHOST="$PILOT_DIR/socket" PGPORT=55481
export DATABASE_URL='postgresql:///pcg_workspace_pilot'
initdb -D "$PILOT_DIR/postgres" --auth-local=trust --auth-host=scram-sha-256 --encoding=UTF8 --no-locale
pg_ctl -D "$PILOT_DIR/postgres" -l "$PILOT_DIR/postgres.log" \
  -o "-h '' -p 55481 -k '$PGHOST'" -w start
createdb pcg_workspace_pilot
uv run alembic upgrade head
npm ci --prefix web
npm run build --prefix web
uv run python -m local_development.workspace_pilot.server "$PILOT_DIR"
```

Open `https://localhost:8444/app` locally. Accept the development certificate for this localhost session. The launcher binds IPv4 loopback, starts one process, configures only in-scope seeded IDs and substitutes the existing deterministic extraction functions. No external model key is needed. For the authentication and Source admission rules see [application setup](application-setup.md#private-synthetic-workspace-pilot).

## Live acceptance record

The local rehearsal on 2026-11-14 applied all migrations to an isolated PostgreSQL cluster, launched the built practitioner shell with fixture OAuth configuration on loopback HTTPS, and observed healthy reads with anonymous writes disabled. The credential-free seed tests exercised 17 creates, a repeat with zero writes, drift and interrupted-write recovery.

The operator completed the first two checks on 2026-11-14 against Google. The remaining rows require the practitioner’s browser session. Record date, commit, pass/fail, counts, digest equality and a sanitized description of differences. Keep IDs, account details, raw URLs, Source content, browser traces and screenshots private.

| Check | Live observation or remaining action |
| --- | --- |
| First and repeat seed | Passed. The first seed verified 17 objects and created 17. The repeat verified the same 17 IDs and created zero. |
| Direct Google controls | Passed. The unrestricted searches found both distractors. The label retained exactly six messages and the direct-parent full-text search retained only the appointment. Jan 5 included the six messages and Jan 6 excluded them. A sorted direct-folder listing returned all three PDFs on distinct one-item pages. The downloaded appointment matched the fixture SHA-256 through PCG acquisition. |
| Sixth message | Sign in → New proposal → Discover Workspace Sources → connect the designated account → Start private discovery for Alder Trust. Record the initial inspected count, approve Alice Reed, inspect more original results and approve the lead from message 06. The six live IDs put the resignation first under PCG’s within-page sort. Mara can appear in the initial batch. Record the order shown in the practitioner UI. The sixth-position case remains an offline fixture. |
| Selection and public boundary | Select the resignation and appointment, preview exact Sources, and check from a signed-out window on the same workstation that no proposal exists yet. Approve publication separately using a unique synthetic reference. Reopen the proposal locally and check the PDF's Source attribution. |
| Access loss | With a preview open, remove this pilot's grant in the synthetic account's third-party connections and attempt another private read. Verify reconnect and fresh search; the old preview cannot publish. Revoking project access can also invalidate operator consent. Record the observed scope of revocation. |

Two provider differences surfaced during the live checks. Gmail returned a cursor after its sixth result and HTTP 204 on the subsequent empty page when the field mask requested only IDs and the cursor. Including `resultSizeEstimate` yielded an empty JSON result and retained all six IDs. Drive full-text search repeated the same PDF across six successive one-item pages with distinct cursors. At the practitioner page size both controls appeared together. The runbook checks folder pagination independently from full-text isolation. Exhaustive full-text recall across pages remains unverified.

After the smoke, stop the server and run `pg_ctl -D "$PILOT_DIR/postgres" -m fast -w stop`. Revoke remaining operator credentials with `gcloud auth application-default revoke` using the same isolated CLOUDSDK_CONFIG. Review the isolated proposal database, seeded corpus and private credential files with the owner for deletion when the pilot ends.

## Data use and later milestones

Google's Limited Use rules cover restricted Gmail and Drive data and derivatives. They constrain retention, human access and transfer and prohibit general model training. This pilot uses a dedicated fictional corpus, local extraction, local database and owner-visible review. A publicly readable route still exposes full Sources to everyone who can reach the service. Before any wider deployment, assess the proposed retention period, deletion mechanism, disclosures, recipients, user consent, and verification/security requirements against the actual use. Synthetic data and OAuth Testing status alone do not establish approval for broader distribution. [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy) · [Workspace developer policy](https://developers.google.com/workspace/workspace-api-user-data-developer-policy)

Official Google remote MCP is a separate future evaluation milestone. Check Developer Preview enrollment for the actual account/project and product-specific access before attempting that evaluation. Direct API access does not establish MCP eligibility. [Google remote MCP prerequisites](https://developers.google.com/workspace/guides/configure-mcp-servers)
