// Edge OG-injection for blog posts.
//
// Crawlers like LinkedIn and Facebook don't run JavaScript, so they read
// blog-post.html's *raw* (generic) meta tags. This Worker rewrites the OG /
// Twitter tags — and the <title> and canonical — per post at the edge, using
// Cloudflare's built-in HTMLRewriter, so a shared post shows its real title,
// description, and per-post social card on the clean leapps.org URL.
//
// Only /blog-post?post=<slug> is touched; every other request passes straight
// through to the static assets, and any error falls back to the static page.
// A /blog-post address that names no post gets a 404 status, so search
// engines drop it instead of reporting a page that says "Post not found".

const ORIGIN = 'https://leapps.org';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/blog-post') {
      // Tolerate a stray trailing slash on the slug (e.g. ...-images/), which
      // a pasted URL can carry — otherwise the slug fails validation and the
      // per-post OG tags are silently skipped.
      const slug = (url.searchParams.get('post') || '').replace(/\/+$/, '');
      if (!slug || !/^[\w-]+$/.test(slug)) return notFound(url, env);
      try {
        return await injectOG(request, url, slug, env);
      } catch (_) {
        // fall through to the unmodified static page
      }
    }
    return env.ASSETS.fetch(request);
  },
};

// The blog-post page itself, sent with a 404 status. Its script shows the
// same "Post not found" message a reader saw before; only the status changes.
// The page is fetched without the visitor's conditional headers, so the reply
// always carries the page body rather than an empty "not modified".
async function notFound(url, env) {
  const page = await env.ASSETS.fetch(new Request(`${url.origin}/blog-post`));
  const headers = new Headers(page.headers);
  headers.delete('etag');
  return new Response(page.body, { status: 404, headers });
}

async function injectOG(request, url, slug, env) {
  const idxRes = await env.ASSETS.fetch(new Request(`${url.origin}/blog/posts/index.json`));
  if (!idxRes.ok) return env.ASSETS.fetch(request);
  const index = await idxRes.json();
  const post = Array.isArray(index) ? index.find((p) => p.slug === slug) : null;
  if (!post) {
    // A post pushed moments ago can deploy before the workflow regenerates
    // index.json, so the markdown file decides: no file means no post.
    const md = await env.ASSETS.fetch(new Request(`${url.origin}/blog/posts/${slug}.md`, { method: 'HEAD' }));
    return md.ok ? env.ASSETS.fetch(request) : notFound(url, env);
  }

  const pageRes = await env.ASSETS.fetch(request);
  if (!(pageRes.headers.get('content-type') || '').includes('text/html')) return pageRes;

  const title = `${post.title} — LEAPPs Blog`;
  const desc = post.excerpt || 'News, updates and forensics insights from the LEAPPs project.';
  // Version the card URL by the post date. It's the same image, but the
  // distinct URL forces social platforms to fetch it fresh instead of serving
  // a previously-cached result (e.g. a 404 cached before the card deployed).
  const image = `${ORIGIN}/blog/og/${encodeURIComponent(slug)}.png?v=${encodeURIComponent(post.date || '1')}`;
  const postUrl = `${ORIGIN}/blog-post?post=${encodeURIComponent(slug)}`;

  const content = (val) => ({ element(el) { el.setAttribute('content', val); } });

  return new HTMLRewriter()
    .on('title', { element(el) { el.setInnerContent(title); } })
    .on('meta[name="description"]', content(desc))
    .on('meta[property="og:title"]', content(title))
    .on('meta[property="og:description"]', content(desc))
    .on('meta[property="og:image"]', content(image))
    .on('meta[property="og:url"]', content(postUrl))
    .on('meta[name="twitter:title"]', content(title))
    .on('meta[name="twitter:description"]', content(desc))
    .on('meta[name="twitter:image"]', content(image))
    .on('link[rel="canonical"]', { element(el) { el.setAttribute('href', postUrl); } })
    .transform(pageRes);
}
