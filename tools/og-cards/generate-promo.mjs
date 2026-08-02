// Generates a square (1254x1254) Instagram promo image for a blog post.
//
// The first promo, for the Unified Logs field guide, was made by hand outside the
// repo, so it could not be reproduced or restyled later. This shares the OG card's
// fonts, palette, and renderer so promos stay on brand and stay regenerable.
//
// Run:
//   node generate-promo.mjs --out ../../blog/images/<slug>/instagram-promo.png \
//     --eyebrow "REFERENCE GUIDE" --accent-label "iLEAPP" \
//     --headline "APPLE|UNIFIED LOG|PREDICATES" \
//     --tagline "34 ARTIFACTS. 230 PREDICATES." \
//     --subline "EVERY ONE SOURCED + VALIDATED"
//
// Headline lines are separated by "|". Tagline words are colored in rotation
// (gold, cream, red) the way the first promo colored ACQUIRE. PROCESS. QUERY.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import satori from 'satori';
import { Resvg } from '@resvg/resvg-js';

const here = path.dirname(fileURLToPath(import.meta.url));
const fontsDir = path.join(here, 'fonts');

const GOLD = '#F5C020';
const CREAM = '#F0EDE6';
const BLACK = '#0E0E0E';
const RED = '#E30613';
const RULE = '#2C2C2C';
const FAINT = '#1C1C1C';

const SIZE = 1254;

const fonts = [
  { name: 'Barlow Condensed', data: fs.readFileSync(path.join(fontsDir, 'BarlowCondensed-Black.woff')), weight: 900, style: 'normal' },
  { name: 'IBM Plex Mono', data: fs.readFileSync(path.join(fontsDir, 'IBMPlexMono-Regular.woff')), weight: 400, style: 'normal' },
  { name: 'IBM Plex Mono', data: fs.readFileSync(path.join(fontsDir, 'IBMPlexMono-Medium.woff')), weight: 500, style: 'normal' },
];

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const el = (type, style, children) => ({ type, props: { style, children } });

// Faint unified-log texture. Real message shapes, no real device data.
const LOG_LINES = [
  '2026-08-01 10:14:23.123456-0400  0x1f2  Default  callservicesd     Started tracking call: <private>',
  '2026-08-01 10:14:23.183902-0400  0x1f3  Info     SpringBoard       Processed authentication request (success=YES)',
  '2026-08-01 10:14:24.004118-0400  0x1f4  Default  backboardd        contact 1 presence: touching',
  '2026-08-01 10:14:24.551093-0400  0x1f5  Info     contextstored     Setting value for /device/app/inFocus',
  '2026-08-01 10:14:25.238740-0400  0x1f6  Default  kernel            PearlCamFrameReceived - isFaceDetected=1',
  '2026-08-01 10:14:25.902334-0400  0x1f7  Info     sharingd          Scanning mode Contacts Only',
  '2026-08-01 10:14:26.118765-0400  0x1f8  Default  powerexperienced  plugin state changed to 1',
  '2026-08-01 10:14:26.774510-0400  0x1f9  Info     wifid             MotionState: Driving',
  '2026-08-01 10:14:27.330982-0400  0x1fa  Default  assetsd           Created asset IMG_0421',
  '2026-08-01 10:14:27.884201-0400  0x1fb  Info     apsd              Screen did unlock (Was locked for 347.28s)',
];

// Texture only. Kept to the right of the left-aligned copy so it never sits
// under the wordmark, eyebrow, subline, or URL, and clipped by the right edge
// the way a real log view runs past the viewport.
function logColumn({ left, top, count, offset = 0 }) {
  const lines = [];
  for (let i = 0; i < count; i++) lines.push(LOG_LINES[(i + offset) % LOG_LINES.length]);
  return el('div', {
    position: 'absolute', left, top, display: 'flex', flexDirection: 'column',
    fontFamily: 'IBM Plex Mono', fontSize: 15, color: FAINT, lineHeight: 1.9,
  }, lines.map(l => el('div', { display: 'flex' }, l)));
}

function promo({ eyebrow, accentLabel, headline, tagline, subline, site }) {
  const lines = headline.split('|');
  // Longest line drives the size so three-line headlines still fill the square.
  const longest = Math.max(...lines.map(l => l.length));
  const headSize = longest <= 9 ? 210 : longest <= 12 ? 175 : longest <= 16 ? 140 : 118;

  const top = el('div', { display: 'flex', flexDirection: 'column' }, [
    el('div', { display: 'flex', fontFamily: 'Barlow Condensed', fontWeight: 900, fontSize: 74, color: CREAM, letterSpacing: 1 }, 'LEAPPs'),
    el('div', { display: 'flex', flexDirection: 'row', marginTop: 18, fontFamily: 'IBM Plex Mono', fontSize: 26, letterSpacing: 3 }, [
      el('div', { color: GOLD }, eyebrow),
      ...(accentLabel ? [el('div', { color: RED, marginLeft: 16 }, `· ${accentLabel}`)] : []),
    ]),
  ]);

  const headEl = el('div', {
    display: 'flex', flexDirection: 'column', fontFamily: 'Barlow Condensed', fontWeight: 900,
    fontSize: headSize, color: CREAM, textTransform: 'uppercase', lineHeight: 0.92, letterSpacing: 0.5,
  }, lines.map(l => el('div', { display: 'flex' }, l)));

  // Colour the tagline word by word, cycling gold / cream / red.
  const palette = [GOLD, CREAM, RED];
  const tagEl = el('div', {
    display: 'flex', flexDirection: 'row', flexWrap: 'wrap', marginTop: 26,
    fontFamily: 'IBM Plex Mono', fontSize: 40, letterSpacing: 2,
  }, tagline.split(' ').map((w, i) => el('div', { color: palette[i % palette.length], marginRight: 16 }, w)));

  const bottom = el('div', { display: 'flex', flexDirection: 'column' }, [
    el('div', { display: 'flex', width: '100%', height: 2, backgroundColor: RULE, marginBottom: 26 }, null),
    el('div', { display: 'flex', fontFamily: 'IBM Plex Mono', fontSize: 30, letterSpacing: 2, color: CREAM }, subline),
    el('div', { display: 'flex', marginTop: 46, fontFamily: 'IBM Plex Mono', fontSize: 34, letterSpacing: 2, color: GOLD }, site),
  ]);

  const content = el('div', {
    display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
    width: '100%', height: '100%', padding: '86px 92px',
  }, [top, el('div', { display: 'flex', flexDirection: 'column' }, [headEl, tagEl]), bottom]);

  const bar = el('div', { position: 'absolute', left: 0, top: 0, width: 22, height: SIZE, backgroundColor: RED }, null);

  return el('div', {
    position: 'relative', display: 'flex', flexDirection: 'column',
    width: SIZE, height: SIZE, backgroundColor: BLACK, fontFamily: 'Barlow Condensed',
  }, [
    logColumn({ left: 575, top: 58, count: 8 }),
    logColumn({ left: 730, top: 1002, count: 6, offset: 4 }),
    bar,
    content,
  ]);
}

async function main() {
  const out = path.resolve(here, arg('out', 'promo.png'));
  const vdom = promo({
    eyebrow: arg('eyebrow', 'REFERENCE GUIDE'),
    accentLabel: arg('accent-label', 'iLEAPP'),
    headline: arg('headline', 'APPLE|UNIFIED LOG|PREDICATES'),
    tagline: arg('tagline', '34 ARTIFACTS. 230 PREDICATES.'),
    subline: arg('subline', 'EVERY ONE SOURCED + VALIDATED'),
    site: arg('site', 'leapps.org'),
  });
  const svg = await satori(vdom, { width: SIZE, height: SIZE, fonts });
  const png = new Resvg(svg, { fitTo: { mode: 'width', value: SIZE } }).render().asPng();
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, png);
  console.log(`Wrote ${out}`);
}

main().catch(e => { console.error(e); process.exit(1); });
