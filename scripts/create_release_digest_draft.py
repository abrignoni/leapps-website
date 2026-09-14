#!/usr/bin/env python3
"""Create a Mailjet campaign draft digesting recent LEAPP tool releases.

Run by hand from .github/workflows/release-mailing-draft.yml when a mailer is
needed. Looks across all tool repos for releases published inside the lookback
window; if there are none it exits quietly, otherwise it creates ONE Mailjet
campaign DRAFT that digests them all, so same-day releases of several tools
become a single email.
Like the blog announcement flow, it never sends: review the draft in the
Mailjet dashboard (Campaigns) and send it from there.

Two modes:
    window   (default) releases published inside the lookback window, set with
             --hours (36 when omitted).
    current  --current, the newest release of every tool regardless of age, for
             a "where the suite stands" mailer that does not depend on several
             tools happening to ship inside one window.

Usage:
    python3 scripts/create_release_digest_draft.py [--dry-run] [--hours N]
    python3 scripts/create_release_digest_draft.py [--dry-run] --current

Environment:
    GITHUB_TOKEN                           optional, raises API rate limits
    MAILJET_API_KEY / MAILJET_API_SECRET   API credentials (unless --dry-run)
    MAILJET_LIST_ID                        numeric contact list ID
    MAILJET_SENDER_EMAIL                   validated sender address in Mailjet
    MAILJET_SENDER_NAME                    sender display name
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_mailing_draft import SITE, mailjet_post  # noqa: E402

# (display name, github repo, anchor on leapps.org/releases)
TOOLS = (
    ("iLEAPP", "abrignoni/iLEAPP", "section-ileapp"),
    ("ALEAPP", "abrignoni/ALEAPP", "section-aleapp"),
    ("RLEAPP", "abrignoni/RLEAPP", "section-rleapp"),
    ("VLEAPP", "abrignoni/VLEAPP", "section-vleapp"),
    ("DLEAPP", "abrignoni/DLEAPP", "section-dleapp"),
    ("LAVA", "leapps-org/LAVA-releases", "section-lava"),
    ("Batch LEAPP", "abrignoni/batch-leapp", "section-batch-leapp"),
)

NOTES_MAX_CHARS = 700
CURRENT_NOTES_MAX_CHARS = 280


def github_releases(repo: str) -> list:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases?per_page=10",
        headers={"Accept": "application/vnd.github+json"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as err:
        print(f"warning: could not list releases for {repo}: HTTP {err.code}",
              file=sys.stderr)
        return []


def recent_releases(hours: int) -> list:
    """Releases across all tools published within the last `hours` hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    found = []
    for tool, repo, anchor in TOOLS:
        for release in github_releases(repo):
            if release.get("draft") or release.get("prerelease"):
                continue
            published = datetime.fromisoformat(
                release["published_at"].replace("Z", "+00:00"))
            if published >= cutoff:
                found.append({
                    "tool": tool,
                    "anchor": anchor,
                    "tag": release.get("tag_name", ""),
                    "name": release.get("name") or release.get("tag_name", ""),
                    "notes": release.get("body") or "",
                    "published": published,
                })
    found.sort(key=lambda r: r["published"])
    return found


def latest_release_per_tool() -> list:
    """The newest published release of every tool, in suite order.

    Unlike recent_releases() this ignores age entirely, so a tool that last
    shipped months ago still appears with its current version. Tools with no
    published release are skipped and named on stderr rather than silently
    dropped.
    """
    found = []
    for tool, repo, anchor_id in TOOLS:
        published_releases = []
        for release in github_releases(repo):
            if release.get("draft") or release.get("prerelease"):
                continue
            published_releases.append((
                datetime.fromisoformat(
                    release["published_at"].replace("Z", "+00:00")),
                release,
            ))
        if not published_releases:
            print(f"warning: no published release found for {tool} ({repo})",
                  file=sys.stderr)
            continue
        published, release = max(published_releases, key=lambda pair: pair[0])
        found.append({
            "tool": tool,
            "anchor": anchor_id,
            "tag": release.get("tag_name", ""),
            "name": release.get("name") or release.get("tag_name", ""),
            "notes": release.get("body") or "",
            "published": published,
        })
    return found


def notes_excerpt(markdown: str, max_chars: int = NOTES_MAX_CHARS) -> str:
    """Crude markdown -> short plain text for the email body."""
    text = re.sub(r"```.*?```", "", markdown, flags=re.DOTALL)      # code blocks
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)                # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)            # links -> text
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)      # headings
    text = re.sub(r"[*_`]", "", text)                               # emphasis
    text = re.sub(r"\r\n", "\n", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(None, 1)[0] + " …"
    return text


FALLBACK_INTRO = (
    "Fresh releases are out for the LEAPP tools. Here is what shipped and "
    "where to get it."
)

CURRENT_FALLBACK_INTRO = (
    "Here is where every LEAPP tool stands right now, with the current "
    "version of each one and where to download it."
)

# Style reference for the generated intro: Alexis's own words, sampled from
# abrignoni.blogspot.com announcement posts.
VOICE_SAMPLES = """\
- "Tor Browser investigations usually don't go beyond possible user saved \
bookmarks. Thanks to a find by Loicforensic we can locate Tor Browser \
thumbnails of opened tabs."
- "Have you heard about binary JSON in SQLite? I hadn't. Today I was made \
aware of it by digital forensics examiner and software developer \
extraordinaire Alex Caithness."
- "The need to analyze cars for digital forensic artifacts has grown recently \
as vehicles have smart mobile features by default. From GPS coordinates, \
contact databases, call logs, and even automated driving, the forensic value \
of these items cannot be overstated."
- "If you have ever had a folder full of extractions and needed to run them \
through iLEAPP one at a time, this is for you."
"""


def generate_intro(releases: list, mode: str = "window") -> str:
    """Ask Claude for a short intro in Alexis's voice; None-safe fallback.

    The result lands in a Mailjet DRAFT that is reviewed by a human before
    sending, so a bad generation is editable/deletable, never subscriber-facing.
    Any failure (missing key, missing SDK, API error) falls back to a static
    intro rather than blocking the digest.
    """
    try:
        import anthropic

        cap = CURRENT_NOTES_MAX_CHARS if mode == "current" else NOTES_MAX_CHARS
        notes = "\n\n".join(
            f"### {r['tool']} {r['tag']} — {r['name']}\n"
            f"{notes_excerpt(r['notes'], cap)}"
            for r in releases
        )
        if mode == "current":
            task = (
                "Write the intro paragraph for a mailing list email that lists "
                "the current version of every tool in the LEAPP suite. This is "
                "not an announcement of something that just shipped: it is a "
                "snapshot of where the suite stands today, so a reader can "
                "check what they are running against what is current. Say that "
                "it covers every tool. Do not imply all of these are new. Keep "
                "it to 2 to 4 sentences. Return only the paragraph, nothing "
                "else.\n\n"
            )
        else:
            task = (
                "Write the intro paragraph for a mailing list email "
                "announcing these releases. Mention every tool released by "
                "name, with a brief note on what its update brings a "
                "forensic examiner. Keep it to 2-3 sentences for a single "
                "release, and up to 4-5 sentences when several tools "
                "released together, and every tool must get a mention. "
                "Return only the paragraph, nothing else.\n\n"
            )
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            system=(
                "You write the opening paragraph for the LEAPPs project mailing "
                "list release announcements, in the voice of Alexis Brignoni: "
                "direct, warm, practical, enthusiastic about open source digital "
                "forensics and the community behind it. Plain sentences, no "
                "corporate fluff, no emoji, no hashtags, no markdown. "
                "Never use em-dashes; use periods, commas, colons or "
                "parentheses instead. Do not open with filler hooks that "
                "delay the news, such as telling the reader to grab a "
                "coffee, to buckle up, or to hold on to their hat. Lead "
                "with what shipped. "
                "Occasionally a rhetorical hook or a light touch of humor. "
                "Credit contributors by name when the release notes name them.\n\n"
                "Style samples of his writing:\n" + VOICE_SAMPLES
            ),
            messages=[{"role": "user", "content": task + notes}],
        )
        if response.stop_reason == "refusal":
            return CURRENT_FALLBACK_INTRO if mode == "current" else FALLBACK_INTRO
        intro = next(
            (b.text.strip() for b in response.content if b.type == "text"), "")
        return intro or (CURRENT_FALLBACK_INTRO if mode == "current"
                         else FALLBACK_INTRO)
    except Exception as err:  # noqa: BLE001 — intro is best-effort by design
        print(f"warning: intro generation failed ({err}); using fallback.",
              file=sys.stderr)
        return CURRENT_FALLBACK_INTRO if mode == "current" else FALLBACK_INTRO


def build_email(releases: list, mode: str = "window") -> tuple[str, str, str]:
    """Return (subject, html_part, text_part) for the digest."""
    current = mode == "current"
    if current:
        # Seven tools would make an unreadable subject line, so name the month
        # instead of listing every version.
        subject = ("Current LEAPPs versions: "
                   f"{datetime.now(timezone.utc):%B %Y}")
        heading = "Current Versions"
        text_heading = "Current LEAPPs versions"
    else:
        versions = ", ".join(f"{r['tool']} {r['tag']}" for r in releases)
        subject = (f"New LEAPPs release{'s' if len(releases) > 1 else ''}: "
                   f"{versions}")
        heading = f"New Release{'s' if len(releases) > 1 else ''}"
        text_heading = "New LEAPPs releases"
    notes_cap = CURRENT_NOTES_MAX_CHARS if current else NOTES_MAX_CHARS
    intro = generate_intro(releases, mode)

    sections_html = []
    sections_text = []
    for r in releases:
        notes = notes_excerpt(r["notes"], notes_cap)
        # In current mode a tool may have shipped months ago, so the date is
        # part of the answer rather than noise.
        released = (f'<p style="margin:0 0 12px; font-size:12px; color:#8A8A8A;">'
                    f'Released {r["published"]:%Y-%m-%d}</p>' if current else "")
        released_text = f"Released {r['published']:%Y-%m-%d}\n" if current else ""
        notes_html = html.escape(notes).replace("\n", "<br />")
        link = f"{SITE}/releases#{r['anchor']}"
        sections_html.append(f"""
      <div style="padding:24px 28px; border-top:1px solid #2C2C2C;">
        <p style="margin:0 0 6px; font-size:12px; letter-spacing:2px; text-transform:uppercase; color:#F5C020;">
          {html.escape(r["tool"])}
        </p>
        <h2 style="margin:0 0 12px; font-size:22px; line-height:1.2; color:#F0EDE6;">
          {html.escape(r["name"])}
        </h2>{released}
        <p style="margin:0 0 18px; font-size:14px; line-height:1.6; color:#CFC9BE;">
          {notes_html}
        </p>
        <a href="{link}"
           style="display:inline-block; background:#F5C020; color:#0E0E0E; font-size:13px; font-weight:bold;
                  letter-spacing:1px; text-transform:uppercase; text-decoration:none; padding:10px 22px;">
          Download {html.escape(r["tool"])}
        </a>
      </div>""")
        sections_text.append(
            f"{r['tool']}: {r['name']}\n{released_text}\n{notes}\n\n"
            f"Download: {link}\n")

    html_part = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8" /></head>
<body style="margin:0; padding:0; background:#0E0E0E; font-family:Arial,Helvetica,sans-serif; color:#F0EDE6;">
  <div style="max-width:600px; margin:0 auto; padding:24px 16px;">
    <div style="background:#161616; border:1px solid #2C2C2C;">
      <div style="padding:32px 28px 24px;">
        <p style="margin:0 0 6px; font-size:12px; letter-spacing:2px; text-transform:uppercase; color:#F5C020;">
          LEAPPs Project
        </p>
        <h1 style="margin:0 0 14px; font-size:28px; line-height:1.1; color:#F0EDE6;">
          {heading}
        </h1>
        <p style="margin:0; font-size:15px; line-height:1.6; color:#CFC9BE;">
          {html.escape(intro)}
        </p>
      </div>
      {''.join(sections_html)}
    </div>
    <p style="margin:20px 8px 0; font-size:12px; line-height:1.6; color:#888888; text-align:center;">
      You are receiving this because you subscribed to the LEAPPs mailing list at
      <a href="{SITE}/mailing" style="color:#888888;">leapps.org</a>.<br />
      <a href="[[UNSUB_LINK_EN]]" style="color:#888888;">Unsubscribe</a>
    </p>
  </div>
</body>
</html>"""

    text_part = (
        f"{text_heading}\n\n"
        f"{intro}\n\n"
        + "\n----------------------------------------\n\n".join(sections_text)
        + "\nYou are receiving this because you subscribed to the LEAPPs "
        f"mailing list at {SITE}/mailing\n"
    )
    return subject, html_part, text_part


def main() -> int:
    argv = sys.argv[1:]
    dry_run = "--dry-run" in argv
    mode = "current" if "--current" in argv else "window"
    hours = 36
    if "--hours" in argv:
        hours = int(argv[argv.index("--hours") + 1])

    if mode == "current":
        releases = latest_release_per_tool()
        if not releases:
            print("No published releases found for any tool; nothing to do.")
            return 0
    else:
        releases = recent_releases(hours)
        if not releases:
            print(f"No releases published in the last {hours} hours; "
                  "nothing to do.")
            return 0

    subject, html_part, text_part = build_email(releases, mode)
    label = "current version" if mode == "current" else "release"
    print(f"Found {len(releases)} {label}(s): "
          + ", ".join(f"{r['tool']} {r['tag']}" for r in releases))

    if dry_run:
        print(f"--- DRY RUN ---\nSubject: {subject}\n\n{text_part}")
        return 0

    try:
        key = os.environ["MAILJET_API_KEY"]
        secret = os.environ["MAILJET_API_SECRET"]
        list_id = int(os.environ["MAILJET_LIST_ID"])
        sender_email = os.environ["MAILJET_SENDER_EMAIL"]
        sender_name = os.environ["MAILJET_SENDER_NAME"]
    except KeyError as missing:
        print(f"Missing required environment variable: {missing}", file=sys.stderr)
        return 1

    today = datetime.now(timezone.utc).date().isoformat()
    title_prefix = "Current versions" if mode == "current" else "Release digest"
    draft = mailjet_post(
        "/campaigndraft",
        {
            "Locale": "en_US",
            "Subject": subject,
            "Title": f"{title_prefix}: {today}",
            "Sender": sender_name,
            "SenderName": sender_name,
            "SenderEmail": sender_email,
            "ContactsListID": list_id,
            "EditMode": "html2",
        },
        key,
        secret,
    )
    draft_id = draft["Data"][0]["ID"]
    mailjet_post(
        f"/campaigndraft/{draft_id}/detailcontent",
        {"Html-part": html_part, "Text-part": text_part},
        key,
        secret,
    )
    print(f"Created Mailjet draft {draft_id}.")
    print("Review and send it at https://app.mailjet.com/campaigns (Drafts).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
