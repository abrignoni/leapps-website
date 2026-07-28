#!/usr/bin/env python3
"""Create a Mailjet campaign draft announcing newly published blog post(s).

Runs from .github/workflows/blog-mailing-draft.yml when a push to main adds a
new file under blog/posts/. For each new post it creates a campaign DRAFT in
Mailjet addressed to the mailing list — it never sends. Review the draft in
the Mailjet dashboard (Campaigns) and send it from there.

Usage:
    python3 scripts/create_mailing_draft.py [--dry-run] blog/posts/<slug>.md ...

Environment (all required unless --dry-run):
    MAILJET_API_KEY / MAILJET_API_SECRET   API credentials (repo secrets)
    MAILJET_LIST_ID                        numeric contact list ID
    MAILJET_SENDER_EMAIL                   validated sender address in Mailjet
    MAILJET_SENDER_NAME                    sender display name
"""

from __future__ import annotations

import base64
import html
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_blog_index import parse_frontmatter  # noqa: E402

API_BASE = "https://api.mailjet.com/v3/REST"
SITE = "https://leapps.org"


def mailjet_post(path: str, payload: dict, key: str, secret: str) -> dict:
    token = base64.b64encode(f"{key}:{secret}".encode()).decode()
    request = urllib.request.Request(
        API_BASE + path,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as err:
        body = err.read().decode(errors="replace")
        print(f"Mailjet API error on {path}: HTTP {err.code}\n{body}", file=sys.stderr)
        raise SystemExit(1) from err


def build_email(meta: dict, slug: str) -> tuple[str, str]:
    """Return (html_part, text_part) for the announcement email."""
    title = html.escape(meta["title"])
    author = html.escape(meta["author"])
    excerpt = html.escape(meta["excerpt"])
    date = meta["date"]
    post_url = f"{SITE}/blog-post?post={slug}"
    card_url = f"{SITE}/blog/og/{slug}.png"

    html_part = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8" /></head>
<body style="margin:0; padding:0; background:#0E0E0E; font-family:Arial,Helvetica,sans-serif; color:#F0EDE6;">
  <div style="max-width:600px; margin:0 auto; padding:24px 16px;">
    <div style="background:#161616; border:1px solid #2C2C2C;">
      <a href="{post_url}" style="text-decoration:none;">
        <img src="{card_url}" alt="{title}" width="600"
             style="display:block; width:100%; height:auto; border:0;" />
      </a>
      <div style="padding:28px 28px 32px;">
        <p style="margin:0 0 8px; font-size:12px; letter-spacing:2px; text-transform:uppercase; color:#F5C020;">
          New on the LEAPPs Blog
        </p>
        <h1 style="margin:0 0 12px; font-size:26px; line-height:1.2;">
          <a href="{post_url}" style="color:#F0EDE6; text-decoration:none;">{title}</a>
        </h1>
        <p style="margin:0 0 18px; font-size:13px; color:#888888;">
          By {author} &middot; {date}
        </p>
        <p style="margin:0 0 24px; font-size:15px; line-height:1.6; color:#CFC9BE;">
          {excerpt}
        </p>
        <a href="{post_url}"
           style="display:inline-block; background:#F5C020; color:#0E0E0E; font-size:14px; font-weight:bold;
                  letter-spacing:1px; text-transform:uppercase; text-decoration:none; padding:12px 28px;">
          Read the post
        </a>
      </div>
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
        f"New on the LEAPPs Blog\n"
        f"\n"
        f"{meta['title']}\n"
        f"By {meta['author']} - {date}\n"
        f"\n"
        f"{meta['excerpt']}\n"
        f"\n"
        f"Read the post: {post_url}\n"
        f"\n"
        f"You are receiving this because you subscribed to the LEAPPs mailing "
        f"list at {SITE}/mailing\n"
    )
    return html_part, text_part


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in sys.argv[1:]
    if not args:
        print("No post files given; nothing to do.")
        return 0

    if not dry_run:
        try:
            key = os.environ["MAILJET_API_KEY"]
            secret = os.environ["MAILJET_API_SECRET"]
            list_id = int(os.environ["MAILJET_LIST_ID"])
            sender_email = os.environ["MAILJET_SENDER_EMAIL"]
            sender_name = os.environ["MAILJET_SENDER_NAME"]
        except KeyError as missing:
            print(f"Missing required environment variable: {missing}", file=sys.stderr)
            return 1

    for arg in args:
        path = Path(arg)
        meta = parse_frontmatter(path.read_text(encoding="utf-8-sig"))
        if meta is None or any(k not in meta for k in ("title", "date", "author", "excerpt")):
            print(f"{path.name}: missing or incomplete frontmatter, skipping.", file=sys.stderr)
            continue

        slug = path.stem
        subject = f"New on the LEAPPs Blog: {meta['title']}"
        html_part, text_part = build_email(meta, slug)

        if dry_run:
            print(f"--- DRY RUN: {slug} ---")
            print(f"Subject: {subject}")
            print(text_part)
            continue

        draft = mailjet_post(
            "/campaigndraft",
            {
                "Locale": "en_US",
                "Subject": subject,
                "Title": f"Blog announcement: {slug}",
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
        print(f"Created Mailjet draft {draft_id} for {slug}.")
        print("Review and send it at https://app.mailjet.com/campaigns (Drafts).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
