# leapps-website

Source for [leapps.org](https://leapps.org) — the website for the LEAPPs digital forensics tools: iLEAPP, ALEAPP, RLEAPP, VLEAPP, DLEAPP, LAVA, and Batch LEAPP.

The site is static HTML served from Cloudflare. It auto-deploys: pushing to `main` triggers a Cloudflare build that publishes the static files and the edge Worker. A second, separately deployed Worker (`leapps-api`) provides the dynamic data (GitHub stats, releases, RSS feeds, downloads).

---

## Repo structure

```
leapps-website/
├── *.html               # All site pages (one file per page)
├── css/
│   └── global.css       # Shared styles (nav, footer, dropdown, search, themes)
├── analytics.js         # GA4 consent banner + download/outbound click tracking
├── worker.js            # Edge Worker — injects per-post OG tags for /blog-post
├── wrangler.jsonc       # Cloudflare config for the leapps-website Worker
├── wrangler.leapps-api.jsonc  # Cloudflare config for the leapps-api Worker
├── _headers             # Cache-Control rules for static assets
├── .assetsignore        # Files excluded from the published asset bundle
├── leapps-worker.js     # The leapps-api Worker (its own config + build — see below)
├── search-index.json    # Static search index for all site pages
├── blog/
│   ├── posts/
│   │   ├── index.json   # Blog post manifest — GENERATED from post frontmatter (do not hand-edit)
│   │   └── *.md         # Individual blog post content in Markdown (the source of truth)
│   ├── images/<slug>/   # Images referenced by a post (via jsDelivr)
│   └── og/              # Auto-generated 1200×630 social cards (one per post)
├── scripts/             # generate_blog_index.py — builds blog/posts/index.json from frontmatter
├── tools/og-cards/      # OG-card generator (Satori + resvg); run by a GitHub Action
├── data/downloads.json  # Daily download-count snapshot (committed by an Action)
├── downloads/           # Downloadable files served via the leapps-api Worker
├── img/ images/ logos/  # Image and logo assets
├── sitemap.xml          # Sitemap for all pages
└── robots.txt           # Crawler rules
```

### Pages

| File | URL |
|---|---|
| `index.html` | leapps.org/ |
| `about.html` | leapps.org/about |
| `artifacts.html` | leapps.org/artifacts |
| `blog.html` | leapps.org/blog |
| `blog-post.html` | leapps.org/blog-post (template for all posts) |
| `changelog.html` | leapps.org/changelog |
| `designs.html` | leapps.org/designs |
| `docs.html` | leapps.org/docs |
| `mailing.html` | leapps.org/mailing |
| `releases.html` | leapps.org/releases |
| `resources.html` | leapps.org/resources |
| `scoreboard.html` | leapps.org/scoreboard |
| `stats.html` | leapps.org/stats |
| `404.html` | leapps.org/404 |

---

## Hosting & deployment

The site runs on Cloudflare as a **Worker with static assets**. There are two Workers, deployed differently:

### 1. `leapps-website` — auto-deployed from `main`

Defined by [`worker.js`](worker.js) and [`wrangler.jsonc`](wrangler.jsonc). **Every push to `main` auto-deploys** via Cloudflare Workers Builds — there is no manual step. The Worker's only job is edge OG injection: for `/blog-post?post=<slug>` it rewrites the page's Open Graph / Twitter tags (title, description, per-post social card) so links shared on LinkedIn, Facebook, etc. show the real post. Every other path serves the static asset directly.

`run_worker_first: ["/blog-post"]` in `wrangler.jsonc` is required — otherwise the static `blog-post.html` is served before the Worker runs and the OG tags are never rewritten. `.assetsignore` keeps `worker.js`, `tools/`, `node_modules/`, `.git/`, and `.github/` out of the published bundle.

### 2. `leapps-api` — auto-deployed from `main`

Defined by [`leapps-worker.js`](leapps-worker.js) and [`wrangler.leapps-api.jsonc`](wrangler.leapps-api.jsonc), served at `https://leapps-api.4n6-198.workers.dev`. It provides the live-data endpoints the pages fetch. Since 2026-08-02 it is connected to Workers Builds: **merging a change to either of those two files deploys it**, and nothing else does.

Its build configuration, all set in the Cloudflare dashboard under Workers & Pages → `leapps-api` → Settings → Build:

| Setting | Value |
|---|---|
| Repository / production branch | `abrignoni/leapps-website` / `main` |
| Build command | *(empty — no bundler step, and there is no root `package.json`)* |
| Deploy command | `npx wrangler deploy -c wrangler.leapps-api.jsonc` |
| Build watch paths (include) | `leapps-worker.js`, `wrangler.leapps-api.jsonc` |
| Builds for non-production branches | Off |

The watch paths are what keep ordinary site pushes from redeploying the API; without them every blog post would trigger a build. Non-production builds are off because the pages always call the production `workers.dev` hostname, so a preview version would have nothing exercising it.

> ⚠️ **Deploy this Worker only with `-c wrangler.leapps-api.jsonc`.** The root [`wrangler.jsonc`](wrangler.jsonc) describes the *site* Worker (`name: "leapps-website"`, `main: "worker.js"`), so a bare `wrangler deploy` from the root deploys that one instead and the API change silently does not ship. Verified with `wrangler deploy --dry-run`: the bare command bundles `worker.js`, the OG injector.

`leapps-api` depends on two bindings that must survive every deploy:

| Binding | Type | Used for |
|---|---|---|
| `CACHE` | KV namespace `LEAPPS_KV` | Download counters (`dl_count:<file>` keys) behind `/downloads/counts` and `/downloads/daily` |
| `GITHUB_TOKEN` | Secret | Authenticated GitHub API calls in the `/repos/*` proxy |

Secrets survive a redeploy on their own, which is why `GITHUB_TOKEN` is not in the config and must never be committed. A **KV binding only exists if the deploying config declares it**, which is why `wrangler.leapps-api.jsonc` declares `CACHE` explicitly. Removing that line would detach the namespace on the next build and the counters would start failing while every other route looked healthy.

Need to deploy by hand (Cloudflare outage, a build that will not run)? Either paste the file in the dashboard under Workers → `leapps-api` → Edit / Deploy, or run the deploy command above locally. Both reach the same place.

#### Verify the deploy

The endpoints answer for themselves, so check rather than assume:

```bash
# 1. The KV binding survived: counts come back as JSON, not an error
curl -s https://leapps-api.4n6-198.workers.dev/downloads/counts

# 2. A known file still downloads (302 -> raw.githubusercontent.com, then the PDF)
curl -sL -o /dev/null -w '%{http_code}\n' \
  https://leapps-api.4n6-198.workers.dev/downloads/apple-unified-logs-ileapp-field-guide.pdf

# 3. Anything newly added to ALLOWED_DOWNLOADS resolves
curl -sL -o /dev/null -w '%{http_code}\n' \
  https://leapps-api.4n6-198.workers.dev/downloads/<new-file>.pdf

# 4. Which version is live, and whether it came from the git build
npx wrangler deployments list --name leapps-api | tail -8
```

A `{"error":"Not found"}` from step 3 means the file is not in `ALLOWED_DOWNLOADS`, or the Worker running in production predates your edit. Use `GET` rather than `curl -I` for the download checks: `HEAD` on `/downloads/*` returns 405, which is long-standing behaviour of the redirect and not a sign of a bad deploy.

#### Adding a downloadable file

`/downloads/<file>` serves from an explicit allowlist, so dropping a PDF into `downloads/` is not enough on its own. Three steps, all of which ship on merge:

1. Commit the file to `downloads/` on `main` (the Worker redirects to it on `raw.githubusercontent.com`).
2. Add it to `ALLOWED_DOWNLOADS` in [`leapps-worker.js`](leapps-worker.js). This is the step that deploys the Worker, since that file is a build watch path.
3. Add a label to `GUIDE_LABELS` in [`stats.html`](stats.html) so its counter renders with a readable name, and a card in [`guides.html`](guides.html) if it is a guide.

Then run the verify checks above. Before the Worker was git-connected, step 2 also needed a manual deploy, and forgetting it is what made a published PDF 404 while the page linking to it looked fine.

#### `leapps-api` routes

| Route | Description |
|---|---|
| `/repos/:owner/:repo/*` | GitHub API proxy with caching (releases, contributors, repo contents, repo metadata) |
| `/changelog/feed` | RSS feed aggregating releases across all tools |
| `/blog/feed` | RSS feed for blog posts |
| `/downloads/counts`, `/downloads/daily` | Download-count totals and daily stats (KV-backed) |
| `/downloads/<file>` | Serves an allowed downloadable file and increments its counter |
| `/search-index` | JSON search index (legacy; the site now reads the static `/search-index.json` instead) |

Blog content is **not** served by the Worker — `index.json` and each `<slug>.md` are static files fetched same-origin (`/blog/posts/...`), as is `/search-index.json`. The Worker is only used for GitHub data, the RSS feeds, and downloads.

### Caching

[`_headers`](_headers) sets Cache-Control: images/logos 30 days, OG cards / `analytics.js` / `css/*` 1 hour. **HTML, JSON, and Markdown are left at the default (revalidate)** so content edits and deploys show immediately.

> ⚠️ Because `css/*` and `analytics.js` are cached for an hour, their `<link>`/`<script>` references carry a `?v=YYYYMMDD` version token. **Bump that token whenever you change `css/global.css` or `analytics.js`** — otherwise returning visitors load fresh HTML against an hour-stale cached asset and the page renders broken.

---

## Search

The site search box (in the nav) merges three sources at query time, each rendered as its own group:

| Group | Source | Maintenance |
|---|---|---|
| **Blog Posts** | `blog/posts/index.json`, fetched live | Automatic — every post is searchable as soon as its manifest entry merges. No separate step. |
| **Artifacts** | the tool repos' `scripts/artifacts/` via the `leapps-api` Worker, live | Automatic — pulled from GitHub. |
| **Pages** | `search-index.json`, a static curated file | Hand-maintained — see below. |

So blog posts and artifacts are **already dynamic**; nothing needs regenerating for them. `search-index.json` holds only the curated **page/section** entries — bespoke titles and excerpts (not scraped from the DOM), one per searchable page or anchor (e.g. `releases#section-ileapp`, `docs#step-3`). Edit that file by hand only when you want to add or reword a page/section result; it is not auto-generated and does **not** list individual blog posts (those come from the live manifest above — adding them here would double them).

---

## Adding a blog post

Blog posts are plain Markdown files. Adding a post is two file changes and a pull request.

### 1. Create the Markdown file

Add a Markdown file to `blog/posts/`. The filename (without `.md`) becomes the post's **slug** — its public URL — so it must be URL-safe and unique: lowercase letters, digits, and hyphens. Pick something short and descriptive:

```
your-post-title.md
```

Dating the slug (`2026-06-05-your-post-title.md`) is an **optional** convention — it keeps the folder sorted and guarantees uniqueness — but it is not required. The `date` frontmatter field below is what the site uses for ordering and display, not the filename.

Start the file with YAML frontmatter:

```markdown
---
title: Your Post Title
date: 2026-06-05
author: Your Name
tags: [iLEAPP, iOS, artifacts]
excerpt: A one or two sentence summary shown on the blog index and in search results.
---

Your content starts here...
```

**Frontmatter fields:**

| Field | Required | Notes |
|---|---|---|
| `title` | ✅ | Shown on blog index and post page |
| `date` | ✅ | Format: `YYYY-MM-DD` |
| `author` | ✅ | Your name or handle |
| `tags` | ✅ | Array of strings — used for filtering; the first tag also picks the social-card accent color |
| `excerpt` | ✅ | 1–2 sentences — shown on index card, og:description, and RSS |

### 2. The index generates itself

**Do not edit `blog/posts/index.json` by hand.** It is generated from each post's frontmatter by `scripts/generate_blog_index.py`, which a GitHub Action runs on every push to `main` (see [`.github/workflows/generate-blog.yml`](.github/workflows/generate-blog.yml) — the same job also regenerates the social cards). Your job is just to get the post's filename and frontmatter right:

- **Filename → slug** — the filename without `.md` becomes the post's slug and public URL, so it must be URL-safe (`[\w-]+`: letters, digits, hyphen, underscore; lowercase by convention) and unique. The `YYYY-MM-DD-` prefix is an optional convention, not a requirement.
- **`date`** — `YYYY-MM-DD`. This field (not the filename) drives ordering, prev/next, related posts, and the social-card cache-bust.
- **`title`, `author`, `excerpt`** — required, non-empty. **`tags`** — inline array; the first tool tag (iLEAPP/ALEAPP/RLEAPP/VLEAPP/LAVA) sets the social-card accent color.
- **`pinned: true`** — optional; maintainers can add it to keep a post at the top of the blog index.

### 3. Images (optional)

Put images in `blog/images/<slug>/` and reference them from the Markdown via the jsDelivr CDN so they load fast and cached:

```markdown
![Alt text](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/your-post-title/screenshot.png)
```

### 4. Social card — automatic

You do **not** create the 1200×630 social-share card. The same `generate-blog.yml` Action that builds the index also regenerates `blog/og/<slug>.png` (using the generator in `tools/og-cards/`) and commits it alongside the index on every post change. The edge Worker then serves it for the post's OG tags.

### 5. Open a pull request

Submit your PR against `main`. Posts are reviewed before merging. Once merged, the post is live immediately and the social card is generated on the same push.

A GitHub Action (`.github/workflows/validate-blog.yml`) validates your post's frontmatter on every PR that touches `blog/posts/` — a URL-safe slug, a valid `YYYY-MM-DD` date, and the required fields. If it fails, the PR check turns red with the exact problem. Run the same check locally before pushing:

```bash
python3 scripts/generate_blog_index.py --check
```

### Markdown support

Standard Markdown: headings, bold/italic/strikethrough, ordered/unordered lists, links and images, fenced code blocks with syntax highlighting, tables, blockquotes, and horizontal rules.

---

## Adding a design review

Design reviews are Markdown files for larger cross-LEAPP proposals. Add a file to `designs/posts/`; the filename without `.md` becomes the public slug:

```
designs/posts/your-design-slug.md
```

Start it with frontmatter:

```markdown
---
title: Your Design Title
status: Draft
date: 2026-07-20
updated: 2026-07-20
author: Your Name
scope: [iLEAPP, ALEAPP, LAVA]
discussion: pending
excerpt: One sentence summary for the design-review index and site search.
---
```

The index is generated from frontmatter by `scripts/generate_design_index.py`. A GitHub Action runs it after design docs merge to `main`, so contributors normally only edit the Markdown file. To refresh the index locally:

```bash
python3 scripts/generate_design_index.py
```

A separate PR check validates design-review frontmatter. Run the same check locally with:

```bash
python3 scripts/generate_design_index.py --check
```

---

## Development

The site is static HTML — open any `.html` file in a browser or run a local server:

```bash
python3 -m http.server 3456
```

Then open `http://localhost:3456/index.html`.

Pages that need live data (stats, releases, changelog, artifacts, blog, search) fetch from the `leapps-api` Worker and the GitHub API directly, so they work from localhost without any local backend. Edge OG injection is the one thing that only runs on Cloudflare — locally you'll see the generic OG tags, which is fine for everything except previewing share cards.

---

## Analytics

`analytics.js` loads Google Analytics 4 (`G-G6WS09KNKH`) behind a consent banner — GA only loads after the visitor clicks Accept; the choice is remembered. Cloudflare Web Analytics runs separately (cookieless, no consent needed). The same script also fires custom `download` and `outbound_click` events so release/download click-throughs and external links are measurable.

---

## Branching

| Branch | Purpose |
|---|---|
| `main` | Production — every push auto-deploys to Cloudflare |
| `brigs-working` | Active development branch — PRs merge here first |

---

## Contributing

- **Blog posts** — see [Adding a blog post](#adding-a-blog-post) above
- **Parsers and artifacts** — contribute to the individual tool repos ([iLEAPP](https://github.com/abrignoni/iLEAPP), [ALEAPP](https://github.com/abrignoni/ALEAPP), [RLEAPP](https://github.com/abrignoni/RLEAPP), [VLEAPP](https://github.com/abrignoni/VLEAPP))
- **Site bugs or improvements** — open an issue or PR against this repo
