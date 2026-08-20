# Politics in 60

A 30–60 second South African political briefing for 16–35 year-olds. A
GitHub Action checks for genuinely new political news **every 30 minutes**;
if something real has changed, it publishes a new story. If nothing new
happened, the last story just stays up — no filler, no fake "new" content.

- `scripts/generate_script.py` — every run, loads the previous story, calls
  the Claude API (web_search on) to check current SA political news from a
  fixed list of credible sources, and asks it to judge whether there's a
  genuinely new/updated story. Only writes a new file if there is one.
- `.github/workflows/daily-script.yml` — GitHub Action that runs the check
  every 30 minutes and commits only when a new story was actually written.
- `docs/` — the static hosted page (GitHub Pages serves this folder). It reads
  `docs/data/latest.json` and lists every past story from `docs/data/archive/`
  — no rebuild needed, it's plain fetch() calls against JSON files.

## One-time setup (about 10 minutes)

1. **Create a GitHub repo** and push this folder to it (e.g. `git init`,
   `git add .`, `git commit -m "init"`, then push to a new repo named
   something like `politics-in-60`).

2. **Get an Anthropic API key** at https://console.anthropic.com if you
   don't have one, under "API Keys." Note: this uses paid API credits, not
   your claude.ai subscription — each daily run costs a small fraction of a
   cent to a few cents depending on how much searching it does.

3. **Add the key as a repo secret**:
   Repo → Settings → Secrets and variables → Actions → New repository secret
   → Name: `ANTHROPIC_API_KEY` → paste your key → Add secret.

4. **Turn on GitHub Pages**:
   Repo → Settings → Pages → Source: "Deploy from a branch" → Branch:
   `main` → Folder: `/docs` → Save.
   GitHub will give you a URL like:
   `https://<your-username>.github.io/<repo-name>/`
   **That URL is the link you asked for** — bookmark it, and share it with
   your audience. It always shows the latest script.

5. **Test it manually** before waiting for 5pm:
   Repo → Actions tab → "Generate daily politics script" → Run workflow →
   Run workflow. After it finishes (~30–60 seconds), refresh your Pages URL.

That's it — from now on it checks every 30 minutes and only publishes when
something genuinely new happened, with zero further action from you.

A few things worth knowing about the 30-minute schedule:

- **GitHub doesn't guarantee exact timing.** Scheduled runs can slip by a
  few minutes (more, if GitHub's infrastructure is under load) — treat
  "every 30 min" as "roughly every 30 min," not a hard real-time guarantee.
- **GitHub auto-disables schedules after 60 days of zero commits to the
  repo.** Since this workflow only commits when there's real news, a very
  quiet 2-month stretch could pause it. If you notice it's stopped, just
  push any small commit (or re-run manually from the Actions tab) to wake
  it back up.
- **Cost scales with frequency.** 48 checks a day instead of 1 means ~48x
  the API calls — still cheap per call, but keep an occasional eye on
  Settings → Billing → Usage in the Anthropic console.

## Adjusting the sourcing rules or tone

Everything about credibility, tone, and format lives in the `SYSTEM_PROMPT`
inside `scripts/generate_script.py` — the `APPROVED_SOURCES` list controls
which domains it's allowed to cite. Add or remove outlets there if your
standards change.

## Costs and limits

- GitHub Actions: free for public repos; generous free minutes for private
  repos too (this job runs for under a minute a day).
- GitHub Pages: free static hosting.
- Anthropic API: pay-as-you-go, billed to the API key you added — this is
  separate from any Claude.ai subscription.

## If you'd rather not run your own infrastructure

You can skip all of this and just message Claude directly around 5pm each
day asking for the day's script — same sourcing rules, no setup, but no
public link and no archive.
