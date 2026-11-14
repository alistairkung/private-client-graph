# Private Google Workspace pilot

## Owner provisioning

**Live status: awaiting owner provisioning and consent.** The following console steps are based on Google's documentation. Record the outcome of the actual account run separately below. Use one dedicated consumer Gmail account for the signed-in practitioner, the corpus owner and the only OAuth test user. Keep the entire pilot on a private workstation.

1. In a fresh browser profile choose **Create account → For my personal use** and create a new Gmail mailbox. Complete Google's verification, terms and recovery prompts yourself. Use the account exclusively for the fictional corpus. [Create a Google Account](https://support.google.com/accounts/answer/27441)
2. Signed in as that account, open Cloud Console, select the project picker, then **New project**. Create and select a separate project such as **PCG Synthetic Pilot**. In **APIs & Services → Library**, enable **Gmail API** and **Google Drive API** for that project. [Create a project](https://developers.google.com/workspace/guides/create-project) · [Enable APIs](https://developers.google.com/workspace/guides/enable-apis)
3. In **Google Auth Platform → Branding → Get started**, enter the pilot app name, support email and developer contact. Set **Audience → External**, leave publishing status **Testing**, and add the synthetic Gmail address under **Test users**. In **Data Access** declare openid, email, gmail.readonly, drive.readonly and the operator scopes gmail.insert, gmail.labels and drive.file. The three clients request separate grants. [Configure consent](https://developers.google.com/workspace/guides/configure-oauth-consent)
4. In **Google Auth Platform → Clients → Create client**, register the three clients below. Download each client JSON when Google offers the secret, and move the files into the private directory created below. Use the exact HTTPS redirect for each web client. The desktop client's loopback redirect is managed by the Google Cloud CLI. [Create credentials](https://developers.google.com/workspace/guides/create-credentials)

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

Run the following in the dedicated profile and select the synthetic account on Google's consent screen. The operator grant can insert messages, manage labels and create Drive files. The operator directory holds local refresh credentials. The practitioner web clients use separate credentials and online grants. [Google CLI user credentials with custom scopes](https://docs.cloud.google.com/sdk/gcloud/reference/auth/application-default/login)

```sh
gcloud auth application-default login "$PILOT_ACCOUNT" \
  --client-id-file="$PILOT_DIR/operator.json" --disable-quota-project \
  --scopes=openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.insert,https://www.googleapis.com/auth/gmail.labels,https://www.googleapis.com/auth/drive.file
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

**Live Google observations are pending** for all rows. An HTTP-fixture result or local launch cannot establish Google behavior. Record date, commit, pass/fail, counts, digest equality and a sanitized description of differences. Keep IDs, account details, raw URLs, Source content, browser traces and screenshots private.

| Check | Observation to make |
| --- | --- |
| First and repeat seed | First run creates the corpus. Repeat reports 17 verified and zero created, with the same manifest IDs. |
| Direct Google controls | Run the check command. Its unrestricted positive controls must find the unlabelled sibling and out-of-folder appointment. Its scoped searches must exclude them. It requests two messages or one file per page to exercise cursors, checks Jan 5 inclusion and Jan 6 exclusion, and compares original bytes through PCG PDF acquisition against the tracked SHA-256. Indexing lag may delay search results. Repeat the read-only check after indexing. |
| Sixth message | Sign in → New proposal → Discover Workspace Sources → connect the designated account → Start private discovery for Alder Trust. Record the initial inspected count, approve Alice Reed, inspect more original results and approve the lead from message 06. Real Gmail IDs determine inspection order. If Mara appears early, report the difference from the sixth-position fixture. |
| Selection and public boundary | Select the resignation and appointment, preview exact Sources, and check from a signed-out window on the same workstation that no proposal exists yet. Approve publication separately using a unique synthetic reference. Reopen the proposal locally and check the PDF's Source attribution. |
| Access loss | With a preview open, remove this pilot's grant in the synthetic account's third-party connections and attempt another private read. Verify reconnect and fresh search; the old preview cannot publish. Revoking project access can also invalidate operator consent. Record the observed scope of revocation. |

After the smoke, stop the server and run `pg_ctl -D "$PILOT_DIR/postgres" -m fast -w stop`. Revoke remaining operator credentials with `gcloud auth application-default revoke` using the same isolated CLOUDSDK_CONFIG. Review the isolated proposal database, seeded corpus and private credential files with the owner for deletion when the pilot ends.

## Data use and later milestones

Google's Limited Use rules cover restricted Gmail and Drive data and derivatives. They constrain retention, human access and transfer and prohibit general model training. This pilot uses a dedicated fictional corpus, local extraction, local database and owner-visible review. A publicly readable route still exposes full Sources to everyone who can reach the service. Before any wider deployment, assess the proposed retention period, deletion mechanism, disclosures, recipients, user consent, and verification/security requirements against the actual use. Synthetic data and OAuth Testing status alone do not establish approval for broader distribution. [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy) · [Workspace developer policy](https://developers.google.com/workspace/workspace-api-user-data-developer-policy)

Official Google remote MCP is a separate future evaluation milestone. Check Developer Preview enrollment for the actual account/project and product-specific access before attempting that evaluation. Direct API access does not establish MCP eligibility. [Google remote MCP prerequisites](https://developers.google.com/workspace/guides/configure-mcp-servers)
