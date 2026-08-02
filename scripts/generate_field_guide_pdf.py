#!/usr/bin/env python3
"""Render a printable guide PDF from a blog post's markdown.

The first edition of the field guide PDF was generated ad hoc, with no source in the
repo, so the moment the post gained the native iLEAPP workflow the PDF silently went
stale. This script makes the post the single source of truth: edit the markdown, run
this, commit both.

Usage:
    python3 scripts/generate_field_guide_pdf.py            # the Unified Logs field guide
    python3 scripts/generate_field_guide_pdf.py --post blog/posts/<slug>.md \
        --output downloads/<name>.pdf --updated "Month D, YYYY" \
        --footer-label "LEAPPs Reference - ..." --subject "..."

With no arguments it builds the original field guide, so existing automation keeps
working. The cover's live-version link is derived from the post filename.

Handles the markdown subset the posts actually use: #/##/### headings, paragraphs,
bulleted and numbered lists, fenced code blocks, pipe tables, blockquotes, and inline
bold / italic / code / links. Anything fancier should stay out of the posts anyway.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, PageBreak, PageTemplate, Paragraph,
    Preformatted, Spacer, Table, TableStyle,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_blog_index import parse_frontmatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POST = ROOT / 'blog' / 'posts' / '2026-07-29-apple-unified-logs.md'
DEFAULT_OUTPUT = ROOT / 'downloads' / 'apple-unified-logs-ileapp-field-guide.pdf'
DEFAULT_UPDATED = 'August 1, 2026'
DEFAULT_FOOTER = 'LEAPPs Field Guide - Apple Unified Logs'
DEFAULT_SUBJECT = 'Apple Unified Logs acquisition and iLEAPP analysis workflow'
DEFAULT_KICKER = 'LEAPPs FIELD GUIDE'

ACCENT = colors.HexColor('#B8860B')   # readable on white, kin to the site's yellow
INK = colors.HexColor('#1A1A1A')
MUTED = colors.HexColor('#666666')
CODE_BG = colors.HexColor('#F4F2ED')
RULE = colors.HexColor('#DDDDDD')

BODY = ParagraphStyle('Body', fontName='Helvetica', fontSize=9.5, leading=13.5,
                      textColor=INK, spaceAfter=7, alignment=TA_LEFT)
H1 = ParagraphStyle('H1', parent=BODY, fontName='Helvetica-Bold', fontSize=15,
                    leading=18, spaceBefore=16, spaceAfter=8, textColor=INK)
H2 = ParagraphStyle('H2', parent=BODY, fontName='Helvetica-Bold', fontSize=12,
                    leading=15, spaceBefore=12, spaceAfter=6, textColor=ACCENT)
BULLET = ParagraphStyle('Bullet', parent=BODY, leftIndent=14, bulletIndent=4, spaceAfter=4)
QUOTE = ParagraphStyle('Quote', parent=BODY, leftIndent=12, borderPadding=6,
                       backColor=CODE_BG, spaceBefore=6, spaceAfter=8)
CODE = ParagraphStyle('Code', fontName='Courier', fontSize=8, leading=10.5,
                      textColor=INK, backColor=CODE_BG, borderPadding=6,
                      spaceBefore=4, spaceAfter=8)
CELL = ParagraphStyle('Cell', parent=BODY, fontSize=8, leading=10.5, spaceAfter=0)
CELL_HEAD = ParagraphStyle('CellHead', parent=CELL, fontName='Helvetica-Bold')


def inline(text: str) -> str:
    """Markdown inline formatting to ReportLab paragraph markup."""
    out = html.escape(text, quote=False)
    out = re.sub(r'`([^`]+)`', r'<font face="Courier" size="8.5">\1</font>', out)
    out = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', out)
    out = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', out)
    out = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                 rf'<a href="\2" color="{ACCENT.hexval().replace("0x", "#")}">\1</a>', out)
    return out


def table_flowable(rows: list[list[str]]) -> Table:
    data = [[Paragraph(inline(cell), CELL_HEAD if i == 0 else CELL) for cell in row]
            for i, row in enumerate(rows)]
    table = Table(data, hAlign='LEFT', colWidths=None, repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, RULE),
        ('BACKGROUND', (0, 0), (-1, 0), CODE_BG),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return table


def body_flowables(markdown: str) -> list:
    story = []
    lines = markdown.split('\n')
    i = 0
    list_counter = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith('```'):
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                block.append(lines[i])
                i += 1
            story.append(Preformatted('\n'.join(block), CODE))
        elif stripped.startswith('|') and i + 1 < len(lines) and set(lines[i + 1].strip()) <= set('|-: '):
            rows = [[c.strip() for c in stripped.strip('|').split('|')]]
            i += 2
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            story.append(table_flowable(rows))
            story.append(Spacer(1, 6))
            continue
        elif stripped.startswith('# '):
            pass  # the document title renders on the cover, not in the body
        elif stripped.startswith('## '):
            story.append(Paragraph(inline(stripped[3:]), H1))
            story.append(HRFlowable(width='100%', thickness=0.6, color=RULE, spaceAfter=6))
        elif stripped.startswith('### '):
            story.append(Paragraph(inline(stripped[4:]), H2))
        elif stripped.startswith('> '):
            quote = [stripped[2:]]
            while i + 1 < len(lines) and lines[i + 1].strip().startswith('>'):
                i += 1
                quote.append(lines[i].strip()[2:].strip())
            story.append(Paragraph(inline(' '.join(quote)), QUOTE))
        elif stripped.startswith('- '):
            list_counter = 0
            story.append(Paragraph(inline(stripped[2:]), BULLET, bulletText='•'))
        elif re.match(r'^\d+\. ', stripped):
            list_counter += 1
            story.append(Paragraph(inline(re.sub(r'^\d+\. ', '', stripped)),
                                   BULLET, bulletText=f'{list_counter}.'))
        elif stripped:
            list_counter = 0
            story.append(Paragraph(inline(stripped), BODY))
        i += 1
    return story


def cover(meta: dict, updated: str, slug: str, kicker: str) -> list:
    cover_title = ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=22,
                                 leading=27, textColor=INK, spaceAfter=10)
    cover_kicker = ParagraphStyle('CoverKicker', fontName='Helvetica-Bold', fontSize=11,
                                  textColor=ACCENT, spaceAfter=18)
    cover_sub = ParagraphStyle('CoverSub', parent=BODY, fontSize=11, leading=16,
                               textColor=MUTED, spaceAfter=22)
    cover_meta = ParagraphStyle('CoverMeta', parent=BODY, fontSize=10, textColor=MUTED)
    live = f'leapps.org/blog-post?post={slug}'
    return [
        Spacer(1, 1.6 * inch),
        Paragraph(html.escape(kicker), cover_kicker),
        Paragraph(html.escape(meta['title']), cover_title),
        HRFlowable(width='100%', thickness=1, color=ACCENT, spaceAfter=16),
        Paragraph(html.escape(meta['excerpt']), cover_sub),
        Paragraph(f"{html.escape(meta['author'])}<br/>Updated {updated}", cover_meta),
        Spacer(1, 0.5 * inch),
        Paragraph(f'Live version: <a href="https://{live}" '
                  f'color="{ACCENT.hexval().replace("0x", "#")}">{live}</a>',
                  cover_meta),
        PageBreak(),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--post', type=Path, default=DEFAULT_POST)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--updated', default=DEFAULT_UPDATED)
    parser.add_argument('--footer-label', default=DEFAULT_FOOTER)
    parser.add_argument('--subject', default=DEFAULT_SUBJECT)
    parser.add_argument('--kicker', default=DEFAULT_KICKER)
    args = parser.parse_args()

    post = args.post if args.post.is_absolute() else ROOT / args.post
    output = args.output if args.output.is_absolute() else ROOT / args.output

    raw = post.read_text(encoding='utf-8-sig')
    meta = parse_frontmatter(raw)
    if meta is None:
        print('Post frontmatter missing; refusing to build a guide with no title.', file=sys.stderr)
        return 1
    body = raw.split('---', 2)[2]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(0.75 * inch, 0.5 * inch, args.footer_label)
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f'Page {doc.page}')
        canvas.restoreState()

    doc = BaseDocTemplate(
        str(output), pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.7 * inch, bottomMargin=0.75 * inch,
        title=meta['title'], author=meta['author'],
        subject=args.subject)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main')
    doc.addPageTemplates([PageTemplate(id='page', frames=[frame], onPage=footer)])

    doc.build(cover(meta, args.updated, post.stem, args.kicker) + body_flowables(body))
    print(f'Wrote {output.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
