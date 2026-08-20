# Politics in 60

A daily 30–60 second South African political briefing for 16–35 year-olds,
auto-generated every day at **17:00 SAST** and published to a hosted page.

- `scripts/generate_script.py` — calls the Claude API (with the web_search
  tool switched on) to research today's news from a fixed list of credible
  SA sources and write today's script as JSON.
- `.github/workflows/daily-script.yml` — GitHub Action that runs the script
  daily and commits the result.
- `docs/` — the static hosted page (GitHub Pages serves this folder). It reads
  `docs/data/latest.json` and `docs/data/archive/` — no rebuild needed, it's
  plain fetch() calls against JSON files.

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

That's it — from tomorrow, it runs itself every day at 17:00 SAST
(15:00 UTC, set in the workflow's cron schedule) with zero further action
from you.

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
