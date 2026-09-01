// LEAPPs GitHub API Cache Worker  (Cloudflare Worker: leapps-api)
// Caches GitHub API responses at the edge for 5 minutes
//
// DEPLOYMENT: connected to Workers Builds. Merging a change to this file (or to
// wrangler.leapps-api.jsonc) on main triggers a build that runs
// `npx wrangler deploy -c wrangler.leapps-api.jsonc`. Those two paths are the
// Worker's build watch paths, so ordinary site pushes do not redeploy the API.
//
// Deploy with that config, never a bare `wrangler deploy`: the root
// wrangler.jsonc describes the *other* Worker (leapps-website / worker.js) and
// would be picked up instead. The config declares the CACHE (KV) binding
// because a KV binding exists only if the deploying config declares it;
// GITHUB_TOKEN is a secret and survives redeploys. See "leapps-api" under
// Hosting & deployment in README.md for the dashboard fallback and the curl
// checks that confirm a deploy landed.

const CACHE_TTL = 300; // seconds (5 minutes)
const BLOG_CACHE_TTL = 600; // seconds (10 minutes) for blog content
const SEARCH_CACHE_TTL = 3600; // seconds (1 hour), the max-age this route already served

const BLOG_REPO = 'abrignoni/leapps-website';
const BLOG_BRANCH = 'main';

const ALLOWED_REPOS = [
  'abrignoni/iLEAPP',
  'abrignoni/ALEAPP',
  'abrignoni/RLEAPP',
  'abrignoni/VLEAPP',
  'abrignoni/DLEAPP',
  'abrignoni/batch-leapp',
  'leapps-org/LAVA-releases',
  'leapps-org/leapps-language-resources',
];

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return corsResponse('', 204);
    }

    // Only allow GET requests
    if (request.method !== 'GET') {
      return corsResponse(JSON.stringify({ error: 'Method not allowed' }), 405);
    }

    // Search index route: /search-index
    if (url.pathname === '/search-index') {
      return handleSearchIndex(env);
    }

    // Changelog RSS feed route: /changelog/feed
    if (url.pathname === '/changelog/feed') {
      return handleChangelogFeed(env);
    }

    // Blog RSS feed route: /blog/feed
    if (url.pathname === '/blog/feed') {
      return handleBlogFeed(env);
    }

    // Daily downloads route: /downloads/daily
    if (url.pathname === '/downloads/daily') {
      return handleDownloadsDaily(env);
    }

    // File download tracking: /downloads/counts or /downloads/:filename
    if (url.pathname === '/downloads/counts') {
      return handleDownloadCounts(env);
    }
    if (url.pathname.startsWith('/downloads/') && url.pathname !== '/downloads/') {
      return handleTrackedDownload(url, env, ctx);
    }

    // Parse the path — expected format: /repos/{owner}/{repo}/...
    const path = url.pathname + url.search;

    // Extract owner/repo from path - match first two path segments after /repos/
    const repoMatch = url.pathname.match(/^\/repos\/([^\/]+)\/([^\/]+)/);
    if (!repoMatch) {
      return corsResponse(JSON.stringify({ error: 'Invalid path', path: url.pathname }), 400);
    }

    const repoFullName = `${repoMatch[1]}/${repoMatch[2]}`;

    if (!ALLOWED_REPOS.includes(repoFullName)) {
      return corsResponse(JSON.stringify({ error: 'Repo not allowed', repo: repoFullName }), 403);
    }

    // Build the GitHub API URL
    const githubUrl = `https://api.github.com${path}`;

    // Check Cloudflare cache first
    const cache = caches.default;
    const cacheKey = new Request(githubUrl);
    const cached = await cache.match(cacheKey);
    if (cached) {
      const cachedResponse = new Response(cached.body, cached);
      cachedResponse.headers.set('X-Cache', 'HIT');
      cachedResponse.headers.set('Access-Control-Allow-Origin', '*');
      return cachedResponse;
    }

    // Fetch from GitHub
    const githubResponse = await fetch(githubUrl, {
      headers: {
        'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LEAPPs-Worker/1.0',
      },
    });

    if (!githubResponse.ok) {
      return corsResponse(
        JSON.stringify({ error: `GitHub API error: ${githubResponse.status}` }),
        githubResponse.status
      );
    }

    let data = await githubResponse.text();

    // Never expose DRAFT releases. This Worker authenticates with a token that
    // can see unpublished drafts; without this filter they leak to the public
    // site (and 404 for anyone who clicks them). Strip them at the source so
    // every consumer — and the cached copy — is clean.
    if (/^\/repos\/[^\/]+\/[^\/]+\/releases/.test(url.pathname)) {
      try {
        const parsed = JSON.parse(data);
        if (Array.isArray(parsed)) {
          data = JSON.stringify(parsed.filter(r => !r.draft));
        } else if (parsed && parsed.draft) {
          return corsResponse(JSON.stringify({ error: 'Not found' }), 404);
        }
      } catch (_) { /* leave non-JSON responses untouched */ }
    }

    // Store in cache
    const responseToCache = new Response(data, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': `public, max-age=${CACHE_TTL}`,
        'Access-Control-Allow-Origin': '*',
        'X-Cache': 'MISS',
      },
    });
    await cache.put(cacheKey, responseToCache.clone());

    return responseToCache;
  },
};

async function handleSearchIndex(env) {
  // Serves search-index.json from the repository rather than holding a second
  // copy of it. The two used to be maintained by hand and drifted: the copy
  // here fell seven entries behind the static one and both described VLEAPP as
  // logical-only long after that stopped being true. The pages fetch
  // /search-index.json directly, so this route exists for anything outside the
  // site; it now answers with the same bytes those pages get.
  //
  // Same shape as handleBlogFeed: raw.githubusercontent, edge cached, and the
  // token attached when present so the fetch is not rate limited.
  const indexUrl = `https://raw.githubusercontent.com/${BLOG_REPO}/${BLOG_BRANCH}/search-index.json`;

  const cache = caches.default;
  const cacheKey = new Request(`${indexUrl}__search`);

  const cached = await cache.match(cacheKey);
  if (cached) {
    const cachedResponse = new Response(cached.body, cached);
    cachedResponse.headers.set('X-Cache', 'HIT');
    cachedResponse.headers.set('Access-Control-Allow-Origin', '*');
    return cachedResponse;
  }

  const headers = { 'User-Agent': 'LEAPPs-Worker/1.0' };
  if (env && env.GITHUB_TOKEN) headers['Authorization'] = `Bearer ${env.GITHUB_TOKEN}`;

  const upstream = await fetch(indexUrl, { headers });
  if (!upstream.ok) {
    return corsResponse(JSON.stringify({ error: 'Failed to load search index' }), 502);
  }

  const body = await upstream.text();
  const responseToCache = new Response(body, {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': `public, max-age=${SEARCH_CACHE_TTL}`,
      'Access-Control-Allow-Origin': '*',
      'X-Cache': 'MISS',
    },
  });
  await cache.put(cacheKey, responseToCache.clone());

  return responseToCache;
}

async function handleBlogFeed(env) {
  const indexUrl = `https://raw.githubusercontent.com/${BLOG_REPO}/${BLOG_BRANCH}/blog/posts/index.json`;

  const cache = caches.default;
  const cacheKey = new Request(`${indexUrl}__feed`);
  const cached = await cache.match(cacheKey);
  if (cached) {
    const cachedResponse = new Response(cached.body, cached);
    cachedResponse.headers.set('X-Cache', 'HIT');
    cachedResponse.headers.set('Access-Control-Allow-Origin', '*');
    return cachedResponse;
  }

  const headers = { 'User-Agent': 'LEAPPs-Worker/1.0' };
  if (env.GITHUB_TOKEN) headers['Authorization'] = `Bearer ${env.GITHUB_TOKEN}`;

  const upstream = await fetch(indexUrl, { headers });
  if (!upstream.ok) {
    return corsResponse(JSON.stringify({ error: 'Failed to load blog feed' }), 502);
  }

  const posts = await upstream.json();

  const items = posts.map(post => {
    const pubDate = new Date(post.date + 'T00:00:00Z').toUTCString();
    const link = `https://leapps.org/blog-post?post=${encodeURIComponent(post.slug)}`;
    const desc = (post.excerpt || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/'/g, '&apos;');
    const title = (post.title || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return `
    <item>
      <title>${title}</title>
      <link>${link}</link>
      <guid isPermaLink="true">${link}</guid>
      <pubDate>${pubDate}</pubDate>
      <author>${(post.author || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</author>
      <description>${desc}</description>
    </item>`;
  }).join('');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>LEAPPs Blog</title>
    <link>https://leapps.org/blog</link>
    <description>Forensics deep dives, tool updates, artifact write-ups, and community contributions from the LEAPPs project.</description>
    <language>en-us</language>
    <atom:link href="https://leapps-api.4n6-198.workers.dev/blog/feed" rel="self" type="application/rss+xml" />
    ${items}
  </channel>
</rss>`;

  const responseToCache = new Response(xml, {
    status: 200,
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': `public, max-age=${BLOG_CACHE_TTL}`,
      'Access-Control-Allow-Origin': '*',
      'X-Cache': 'MISS',
    },
  });
  await cache.put(cacheKey, responseToCache.clone());

  return responseToCache;
}

async function handleChangelogFeed(env) {
  const CHANGELOG_REPOS = [
    { name: 'iLEAPP', repo: 'abrignoni/iLEAPP' },
    { name: 'ALEAPP', repo: 'abrignoni/ALEAPP' },
    { name: 'RLEAPP', repo: 'abrignoni/RLEAPP' },
    { name: 'VLEAPP', repo: 'abrignoni/VLEAPP' },
    { name: 'LAVA',   repo: 'leapps-org/LAVA-releases' },
  ];

  const cache = caches.default;
  const cacheKey = new Request('https://leapps-api.4n6-198.workers.dev/changelog/feed__cache');
  const cached = await cache.match(cacheKey);
  if (cached) {
    const cachedResponse = new Response(cached.body, cached);
    cachedResponse.headers.set('X-Cache', 'HIT');
    cachedResponse.headers.set('Access-Control-Allow-Origin', '*');
    return cachedResponse;
  }

  const headers = {
    'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'LEAPPs-Worker/1.0',
  };

  const allReleases = [];
  await Promise.all(CHANGELOG_REPOS.map(async ({ name, repo }) => {
    try {
      const res = await fetch(`https://api.github.com/repos/${repo}/releases?per_page=50`, { headers });
      if (!res.ok) return;
      const releases = await res.json();
      for (const r of releases) {
        if (r.draft) continue;
        allReleases.push({ name, repo, tag: r.tag_name, date: r.published_at, body: r.body || '' });
      }
    } catch (_) {}
  }));

  allReleases.sort((a, b) => new Date(b.date) - new Date(a.date));

  function esc(s) {
    return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  const items = allReleases.slice(0, 100).map(r => {
    const link = `https://github.com/${r.repo}/releases/tag/${encodeURIComponent(r.tag)}`;
    const pubDate = new Date(r.date).toUTCString();
    return `
    <item>
      <title>${esc(r.name + ' ' + r.tag)}</title>
      <link>${link}</link>
      <guid isPermaLink="true">${link}</guid>
      <pubDate>${pubDate}</pubDate>
      <description>${esc(r.body.slice(0, 500))}</description>
    </item>`;
  }).join('');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>LEAPPs Changelog</title>
    <link>https://leapps.org/changelog</link>
    <description>Unified release history across iLEAPP, ALEAPP, RLEAPP, VLEAPP, and LAVA.</description>
    <language>en-us</language>
    <atom:link href="https://leapps-api.4n6-198.workers.dev/changelog/feed" rel="self" type="application/rss+xml" />
    ${items}
  </channel>
</rss>`;

  const responseToCache = new Response(xml, {
    status: 200,
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': `public, max-age=${CACHE_TTL}`,
      'Access-Control-Allow-Origin': '*',
      'X-Cache': 'MISS',
    },
  });
  await cache.put(cacheKey, responseToCache.clone());
  return responseToCache;
}

const ALLOWED_DOWNLOADS = {
  'ileapp-module-contributor-guide.pdf': `https://raw.githubusercontent.com/${BLOG_REPO}/main/downloads/ileapp-module-contributor-guide.pdf`,
  'apple-unified-logs-ileapp-field-guide.pdf': `https://raw.githubusercontent.com/${BLOG_REPO}/main/downloads/apple-unified-logs-ileapp-field-guide.pdf`,
  'apple-unified-logs-predicate-reference.pdf': `https://raw.githubusercontent.com/${BLOG_REPO}/main/downloads/apple-unified-logs-predicate-reference.pdf`,
  'telegram-system-events-reference.pdf': `https://raw.githubusercontent.com/${BLOG_REPO}/main/downloads/telegram-system-events-reference.pdf`,
};

async function handleTrackedDownload(url, env, ctx) {
  const filename = url.pathname.replace(/^\/downloads\//, '');
  const target = ALLOWED_DOWNLOADS[filename];
  if (!target) return corsResponse(JSON.stringify({ error: 'Not found' }), 404);

  if (env.CACHE) {
    const writePromise = (async () => {
      const key = `dl_count:${filename}`;
      const current = parseInt(await env.CACHE.get(key) || '0', 10);
      await env.CACHE.put(key, String(current + 1));
    })();
    ctx.waitUntil(writePromise);
  }

  return Response.redirect(target, 302);
}

async function handleDownloadCounts(env) {
  const counts = {};
  for (const filename of Object.keys(ALLOWED_DOWNLOADS)) {
    try {
      const val = await env.CACHE?.get(`dl_count:${filename}`);
      counts[filename] = parseInt(val || '0', 10);
    } catch (_) {
      counts[filename] = 0;
    }
  }
  return corsResponse(JSON.stringify(counts), 200);
}

async function handleDownloadsDaily(env) {
  const rawUrl = `https://raw.githubusercontent.com/abrignoni/leapps-website/main/data/downloads.json`;
  const cacheKey = 'downloads-daily';

  try {
    const cached = await env.CACHE?.get(cacheKey);
    if (cached) return corsResponse(cached, 200, { 'Cache-Control': 'public, max-age=3600' });
  } catch (_) {}

  try {
    const res = await fetch(rawUrl);
    if (!res.ok) return corsResponse(JSON.stringify({ error: 'Could not load snapshot data' }), 502);

    const data = await res.json();
    const snapshots = data.snapshots || [];

    if (snapshots.length < 2) {
      const result = JSON.stringify({ available: false, reason: 'Not enough snapshots yet' });
      return corsResponse(result, 200, { 'Cache-Control': 'public, max-age=3600' });
    }

    const today = snapshots[snapshots.length - 1];
    const yesterday = snapshots[snapshots.length - 2];

    const daily = {};
    let totalDaily = 0;
    for (const key of Object.keys(today.totals)) {
      const delta = Math.max(0, (today.totals[key] || 0) - (yesterday.totals[key] || 0));
      daily[key] = delta;
      totalDaily += delta;
    }

    const result = JSON.stringify({
      available: true,
      date: today.date,
      daily,
      totalDaily,
      totals: today.totals,
    });

    try { await env.CACHE?.put(cacheKey, result, { expirationTtl: 3600 }); } catch (_) {}
    return corsResponse(result, 200, { 'Cache-Control': 'public, max-age=3600' });
  } catch (e) {
    return corsResponse(JSON.stringify({ error: 'Failed to compute daily downloads' }), 500);
  }
}

function corsResponse(body, status = 200, extraHeaders = {}) {
  return new Response(body, {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      ...extraHeaders,
    },
  });
}
