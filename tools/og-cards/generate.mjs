// Generates 1200x630 Open Graph social cards for the LEAPPs blog.
// Reads blog/posts/index.json and writes blog/og/<slug>.png (+ default.png).
// Run: node generate.mjs   (CI runs this on push; see .github/workflows/og-cards.yml)

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import satori from 'satori';
import { Resvg } from '@resvg/resvg-js';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '..', '..');
const fontsDir = path.join(here, 'fonts');
const indexPath = path.join(repo, 'blog', 'posts', 'index.json');
const outDir = path.join(repo, 'blog', 'og');

const GOLD = '#F5C020';
const CREAM = '#F0EDE6';
const BLACK = '#0E0E0E';
const MUTED = '#888888';
const RULE = '#2C2C2C';

// tool tag -> accent color + display label. Non-tool posts fall back to gold.
const TOOLS = {
  ileapp: { color: '#E30613', label: 'iLEAPP' },
  aleapp: { color: '#A4C639', label: 'ALEAPP' },
  rleapp: { color: '#4BA3C7', label: 'RLEAPP' },
  vleapp: { color: '#531dab', label: 'VLEAPP' },
  dleapp: { color: '#B173A9', label: 'DLEAPP' },
  gleapp: { color: '#FD9B41', label: 'GLEAPP' },
  batch:  { color: '#1FB8A6', label: 'BATCH LEAPP' },
  lava:   { color: GOLD,      label: 'LAVA'   },
};

const fonts = [
  { name: 'Barlow Condensed', data: fs.readFileSync(path.join(fontsDir, 'BarlowCondensed-Black.woff')), weight: 900, style: 'normal' },
  { name: 'IBM Plex Mono', data: fs.readFileSync(path.join(fontsDir, 'IBMPlexMono-Regular.woff')), weight: 400, style: 'normal' },
  { name: 'IBM Plex Mono', data: fs.readFileSync(path.join(fontsDir, 'IBMPlexMono-Medium.woff')), weight: 500, style: 'normal' },
];

function fmtDate(iso) {
  const d = new Date(iso + 'T00:00:00Z');
  if (isNaN(d)) return '';
  const m = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'][d.getUTCMonth()];
  return `${m} ${d.getUTCDate()}, ${d.getUTCFullYear()}`;
}

function accentFor(tags) {
  const list = (Array.isArray(tags) ? tags : []).map(t => String(t).toLowerCase());
  // honor the post's own tag order — the first tool tag is the primary one
  for (const tag of list) {
    if (TOOLS[tag]) return { color: TOOLS[tag].color, label: TOOLS[tag].label };
  }
  // non-tool post: gold accent, first tag as the eyebrow topic
  const first = list[0];
  return { color: GOLD, label: first ? first.toUpperCase() : null };
}

function titleSize(title) {
  const n = title.length;
  if (n <= 26) return 96;
  if (n <= 42) return 80;
  if (n <= 60) return 66;
  return 56;
}

// minimal element helper
const el = (type, style, children) => ({ type, props: { style, children } });

function card({ title, footerLeft, accent, eyebrowMain, eyebrowAccent }) {
  const eyebrow = el('div', { display: 'flex', flexDirection: 'row', marginTop: 20, fontFamily: 'IBM Plex Mono', fontSize: 25, letterSpacing: 3 }, [
    el('div', { color: GOLD }, eyebrowMain),
    ...(eyebrowAccent ? [el('div', { color: accent, marginLeft: 14 }, eyebrowAccent)] : []),
  ]);

  const top = el('div', { display: 'flex', flexDirection: 'column' }, [
    el('div', { fontFamily: 'Barlow Condensed', fontWeight: 900, fontSize: 50, color: CREAM, letterSpacing: 1 }, 'LEAPPs'),
    eyebrow,
  ]);

  const titleEl = el('div', {
    display: 'flex', fontFamily: 'Barlow Condensed', fontWeight: 900,
    fontSize: titleSize(title), color: CREAM, textTransform: 'uppercase',
    lineHeight: 1.0, letterSpacing: 0.5,
  }, title);

  const footer = el('div', { display: 'flex', flexDirection: 'column' }, [
    el('div', { width: '100%', height: 1, backgroundColor: RULE, marginBottom: 22 }, null),
    el('div', { display: 'flex', flexDirection: 'row', justifyContent: 'space-between', fontFamily: 'IBM Plex Mono', fontSize: 24, letterSpacing: 1 }, [
      el('div', { color: MUTED }, footerLeft),
      el('div', { color: GOLD }, 'leapps.org'),
    ]),
  ]);

  const content = el('div', {
    display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
    width: '100%', height: '100%', padding: '74px 84px',
  }, [top, titleEl, footer]);

  const bar = el('div', { position: 'absolute', left: 0, top: 0, width: 16, height: 630, backgroundColor: accent }, null);

  return el('div', {
    position: 'relative', display: 'flex', flexDirection: 'column',
    width: 1200, height: 630, backgroundColor: BLACK, fontFamily: 'Barlow Condensed',
  }, [bar, content]);
}

async function render(vdom, outPath) {
  const svg = await satori(vdom, { width: 1200, height: 630, fonts });
  const png = new Resvg(svg, { fitTo: { mode: 'width', value: 1200 } }).render().asPng();
  fs.writeFileSync(outPath, png);
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const posts = JSON.parse(fs.readFileSync(indexPath, 'utf8'));

  let made = 0;
  for (const p of posts) {
    const { color, label } = accentFor(p.tags);
    await render(card({
      title: p.title,
      footerLeft: `${(p.author || 'LEAPPS').toUpperCase()}${p.date ? '  ·  ' + fmtDate(p.date) : ''}`,
      accent: color,
      eyebrowMain: label ? 'LEAPPS BLOG ·' : 'LEAPPS BLOG',
      eyebrowAccent: label,
    }), path.join(outDir, `${p.slug}.png`));
    made++;
    console.log(`  card: ${p.slug}.png  (accent ${color}${label ? ', ' + label : ''})`);
  }

  // site-wide card — used as the OG image for non-blog pages, and as the blog fallback
  await render(card({
    title: 'Leap ahead of the evidence',
    footerLeft: 'iLEAPP·ALEAPP·RLEAPP·VLEAPP·DLEAPP·GLEAPP·LAVA',
    accent: GOLD,
    eyebrowMain: 'DIGITAL FORENSICS TOOLS',
    eyebrowAccent: null,
  }), path.join(outDir, 'default.png'));
  console.log('  card: default.png');

  console.log(`\nGenerated ${made} post cards + default.`);
}

main().catch(e => { console.error(e); process.exit(1); });
