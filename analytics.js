// Google Analytics with a simple consent gate.
//
// Cloudflare Web Analytics runs separately (cookieless, auto-injected, no
// consent needed). GA4 sets cookies, so it only loads after the visitor
// clicks Accept; the choice is remembered in localStorage and the banner
// doesn't reappear. Declining leaves GA unloaded entirely.
(function () {
  var GA_ID = 'G-G6WS09KNKH';
  var KEY = 'lp-analytics-consent';

  function loadGA() {
    if (window.__gaLoaded) return;
    window.__gaLoaded = true;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    // Send page_view manually (not on config): blog posts set their <title>
    // asynchronously after fetching Markdown, so the automatic page_view would
    // record the generic title. We fire it once the correct title is known.
    window.gtag('config', GA_ID, { send_page_view: false });

    window.lpPageView = function (params) {
      if (typeof window.gtag !== 'function') return;
      window.gtag('event', 'page_view', Object.assign({
        page_location: location.href,
        page_title: document.title,
        page_referrer: document.referrer || undefined
      }, params || {}));
    };

    // Regular pages have their final <title> at load — fire now. Blog posts
    // fire their own page_view when the post loads (see blog-post.html); if the
    // post already loaded before consent, its params wait in window.__lpPV.
    if (/\/blog-post(\.html)?$/.test(location.pathname)) {
      if (window.__lpPV) window.lpPageView(window.__lpPV);
    } else {
      window.lpPageView();
    }
  }

  var choice = null;
  try { choice = localStorage.getItem(KEY); } catch (e) {}
  if (choice === 'granted') { loadGA(); return; }
  if (choice === 'denied') { return; }

  function decide(val) {
    try { localStorage.setItem(KEY, val); } catch (e) {}
    if (val === 'granted') loadGA();
    var el = document.getElementById('lp-consent');
    if (el) el.remove();
  }

  function showBanner() {
    if (document.getElementById('lp-consent')) return;
    var bar = document.createElement('div');
    bar.id = 'lp-consent';
    bar.setAttribute('role', 'dialog');
    bar.setAttribute('aria-label', 'Analytics consent');
    bar.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:99999;background:var(--surface,#161616);border-top:1px solid var(--gold,#F5C020);color:var(--text,#F0EDE6);font-family:"IBM Plex Mono",monospace;font-size:.78rem;line-height:1.6;padding:.85rem 1.25rem;display:flex;align-items:center;justify-content:center;gap:.9rem;flex-wrap:wrap;';

    var txt = document.createElement('span');
    txt.style.cssText = 'max-width:620px;';
    txt.textContent = 'We use Google Analytics to understand site traffic. Privacy-friendly analytics runs either way.';

    var accept = document.createElement('button');
    accept.type = 'button';
    accept.textContent = 'Accept';
    accept.style.cssText = 'font-family:inherit;font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;font-weight:700;cursor:pointer;background:var(--gold,#F5C020);color:var(--off-black,#0E0E0E);border:1px solid var(--gold,#F5C020);padding:.45rem 1.1rem;';

    var decline = document.createElement('button');
    decline.type = 'button';
    decline.textContent = 'Decline';
    decline.style.cssText = 'font-family:inherit;font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;font-weight:700;cursor:pointer;background:transparent;color:var(--text,#F0EDE6);border:1px solid var(--text,#F0EDE6);padding:.45rem 1.1rem;';

    accept.addEventListener('click', function () { decide('granted'); });
    decline.addEventListener('click', function () { decide('denied'); });

    bar.appendChild(txt);
    bar.appendChild(accept);
    bar.appendChild(decline);
    document.body.appendChild(bar);
  }

  if (document.body) showBanner();
  else document.addEventListener('DOMContentLoaded', showBanner);
})();

// Outbound + download click tracking (GA4).
//
// One delegated listener fires GA4 events for clicks that leave the site:
//   - `download`        — a GitHub release/archive link or an asset file
//                         (PDF walkthroughs, zips). This is download *intent*:
//                         the actual file transfer happens on github.com,
//                         which we can't observe, so a release-link click is
//                         the strongest signal available client-side.
//   - `outbound_click`  — any other cross-origin link.
// Param names mirror GA4's built-in enhanced-measurement dimensions
// (link_url, link_domain, link_text, file_name, file_extension), so they
// populate existing reports without custom-dimension setup; `tool` is the
// only custom param (register it in GA4 to break downloads down by tool).
//
// The listener no-ops until window.gtag exists, so it respects the same
// consent gate as the loader above — declined visitors are never tracked.
(function () {
  var ASSET_RE = /\.(zip|exe|dmg|pkg|whl|tar\.gz|tgz|7z|pdf)(?:[?#]|$)/i;

  function repoTool(url) {
    // github.com/<owner>/<repo>/... -> normalized tool name (LAVA-releases -> LAVA)
    if (url.hostname !== 'github.com') return '';
    var seg = url.pathname.split('/').filter(Boolean);
    return seg.length < 2 ? '' : seg[1].replace(/-releases$/i, '');
  }

  document.addEventListener('click', function (e) {
    if (!window.gtag) return; // no consent / GA not loaded
    var a = e.target && e.target.closest && e.target.closest('a[href]');
    if (!a) return;

    var url;
    try { url = new URL(a.href, window.location.href); } catch (_) { return; }
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return;

    var crossHost = url.hostname !== window.location.hostname;
    var isAsset = ASSET_RE.test(url.pathname);
    var isRelease = url.hostname === 'github.com' &&
      /\/(releases|archive|zipball|tarball)(\/|$)/.test(url.pathname);
    if (!crossHost && !isAsset) return; // same-site internal nav: ignore

    var label = (a.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 100);
    var href = url.href.slice(0, 100);

    if (isAsset || isRelease) {
      var fname = url.pathname.split('/').filter(Boolean).pop() || '';
      var dot = fname.lastIndexOf('.');
      window.gtag('event', 'download', {
        link_url: href,
        link_domain: url.hostname,
        link_text: label,
        file_name: fname.slice(0, 100),
        file_extension: dot > -1 ? fname.slice(dot + 1).toLowerCase() : '',
        tool: repoTool(url)
      });
    } else {
      window.gtag('event', 'outbound_click', {
        link_url: href,
        link_domain: url.hostname,
        link_text: label
      });
    }
  }, true); // capture phase: fire even if a handler stops propagation
})();
