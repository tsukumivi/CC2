# No-billing public pilot deployment

This deployment keeps the existing local Python Studio intact. The public app runs as a Cloudflare Worker with Static Assets and D1 on the default Free plans. The Worker streams allowlisted source PDFs from the public `tsukumivi/CC2` GitHub repository, avoiding R2. Java code runs in SandboxAPI Basic's isolated service through RapidAPI.

## Free-plan limits and data flow

- Cloudflare Workers Free includes up to 100,000 Worker requests per day; static assets are free and unlimited. D1 Free includes up to 5 million rows read per day, 100,000 rows written per day, and 5 GB of stored data. Keep the account on Workers Free. Free-plan quota exhaustion causes requests to fail or be limited rather than automatically upgrading this app to a paid plan. Review the current [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/), [Workers limits](https://developers.cloudflare.com/workers/platform/limits/), and [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) before inviting a large audience.
- The hosted Java compiler sends source code, standard input and saved project data used by **Run** to SandboxAPI through RapidAPI. **Check** sends source and the task's declared test inputs. SandboxAPI Basic is $0, allows 500 executions per month and advertises no credit card requirement. Its Java service runs in a per-request gVisor sandbox. Failed compilations and timeouts count. When the shared allowance is exhausted, lessons, review and saved work continue, but Run/Check pauses until the monthly reset. Review [SandboxAPI plans](https://sandboxapi.dev/pricing/) and [execution documentation](https://sandboxapi.dev/docs/).
- Learner progress, drafts, attempts, submitted code, saved Java projects and project data files are stored in Cloudflare D1 under a random, HTTP-only cookie. No account, name or email is collected by the app. Guest work is private to that browser profile and does not sync between devices. Project Shelf provides JSON export and erase controls. Cookie removal loses access; guest workspaces are automatically deleted after 90 days without a visit.
- The five class-note PDFs are public files in the `tsukumivi/CC2` repository's `main` branch. The Worker streams the selected PDF from GitHub's raw file host so browsers can display it as a PDF; anyone who can open this site can also open or download those PDFs from GitHub. One PDF contains instructor contact information. Review sharing permission and personal details before sharing the public URL.
- Each guest workspace can keep up to 200 assessment attempts and 20 saved projects. Export or erase a workspace to start fresh.
- This is a pilot without an availability guarantee. Quota limits, service behavior and provider policies can change.

## One-time setup

1. Sign in to Cloudflare and use the default Workers Free plan. Set a `workers.dev` subdomain if the account asks. Do not select Workers Paid or activate R2.
2. Confirm the public `tsukumivi/CC2` repository contains all five PDFs under `notes/` on its `main` branch. The source route streams those files from the public raw-file host. The repository and PDFs are public.
3. Create or use the free SandboxAPI Basic plan through RapidAPI. Keep the API key private; do not paste it into source files or chat. The service's published Basic allowance is 500 executions per month without a credit card.
4. Install Node.js 22+ and pnpm, then from the project root run:

   ```powershell
   pnpm --dir frontend install --frozen-lockfile
   pnpm dlx wrangler@4.149.0 login
   ```

5. For a new Cloudflare account, create a D1 database and place its returned ID in `wrangler.jsonc`. The currently configured database belongs to the existing Cloudflare account, and its migrations have already been applied there.

   ```powershell
   pnpm dlx wrangler@4.149.0 d1 create java-fieldnotes
   ```

6. Validate the PDF files, build the frontend, and apply the D1 schema if it has not already been applied to this database:

   ```powershell
   node scripts/prepare_cloudflare_deploy.mjs
   pnpm --dir frontend run build
   pnpm dlx wrangler@4.149.0 d1 migrations apply java-fieldnotes --remote
   ```

7. Deploy the Worker, then add the runner key as a Cloudflare secret. Wrangler asks for the value interactively; never put it in chat or a tracked file.

   ```powershell
   pnpm dlx wrangler@4.149.0 deploy
   pnpm dlx wrangler@4.149.0 secret put SANDBOX_API_KEY
   pnpm dlx wrangler@4.149.0 deploy
   ```

Wrangler prints the public `workers.dev` URL after deployment. Keep Cloudflare on the Free plan; this configuration does not bind R2 or enable paid overages. To redeploy a later change, repeat the validation, frontend build and deploy commands.

## Local development

The existing `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000` workflow is unchanged and continues using the local JDK and SQLite. The Cloudflare Worker requires a D1 binding and SandboxAPI key; use `wrangler dev` only after setting up a local D1 database and a local `.dev.vars` file. `.dev.vars` is ignored by Git and must never be committed.

The Worker also runs a daily cleanup job. Guest workspaces with no visit for 90 days are deleted from D1.
