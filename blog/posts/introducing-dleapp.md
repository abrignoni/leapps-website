---
title: Introducing DLEAPP
date: 2026-07-27
author: Alexis Brignoni
tags: [DLEAPP, desktop, Electron, artifacts, announcement]
excerpt: The seventh LEAPP is here. DLEAPP parses desktop application artifacts — Discord, Signal, WhatsApp, and Wire so far — and gives a home to any artifact that does not fit the other LEAPPs. Packaged for Windows, macOS, and Linux.
---

The LEAPP family has a new member. **DLEAPP** — Desktop Logs, Events And Protobuf Parser — is now available, with packaged releases for Windows, macOS, and Linux.

## What it is

DLEAPP parses the artifacts desktop applications leave behind. Most modern desktop apps are Electron apps, which means under the hood they are Chromium browsers: their data lives in IndexedDB and LevelDB stores, Local Storage, service worker and HTTP caches, cookies, and application logs. DLEAPP reads those container formats directly and turns them into the reports and LAVA output you already know from the other LEAPPs.

Just as important: DLEAPP is the home for parsers that do not fit neatly anywhere else. Not iOS, not Android, not a provider return, not a vehicle. If an artifact has no obvious LEAPP to live in, it belongs in DLEAPP. Desktop applications are the start, not the boundary.

## What ships today

Twenty-one modules covering four desktop messaging applications:

- **Discord** (8 modules) — messages, attachments and recovered media, servers, channels, users, searches, reactions, drafts, client activity, and a full cache index
- **Wire** (6 modules) — accounts, devices, conversations, messages, calls, cookies, service worker cache, and media recovered by decrypting cached asset blobs
- **WhatsApp** (4 modules) — messages, calls, contacts, and media from the desktop client
- **Signal** (3 modules) — messages, decrypted attachments, conversations and groups, calls, reactions, and account details

The Discord work deserves a special mention. Discord Desktop keeps no message database of its own — the client renders from REST API responses, and those responses stay in the Chromium HTTP cache. DLEAPP reads that cache directly, which means messages, attachments, and the images themselves are recoverable **even after they were deleted server-side**. The approach follows Alex Caithness's excellent work at CCL Solutions on treating a web app's browser artifacts as an application in their own right. Thank you, Alex. 🙌

Signal Desktop encrypts its database with SQLCipher and wraps the key with the OS credential store. DLEAPP handles the whole chain: pass it the credential, the raw key, or — on a dead-box macOS image — the account's login password, and it recovers the Signal credential from the extracted keychain offline and unwraps everything with no external tooling.

## The numbers from our test data

Every DLEAPP module documents what it was validated against, and those numbers tell the story better than I can. Across our test extractions, DLEAPP recovered **more than 156,000 records** in the aggregate:

- **WhatsApp (macOS):** 91,459 records — including 45,363 messages and 43,910 media rows from a single desktop profile
- **Discord (macOS):** 59,977 records from a profile with no message database at all — 12,940 messages and about 8,400 distinct media files pulled back out of roughly 57,600 Chromium cache entries spanning two and a half years
- **Signal (macOS):** 4,912 records from a fully encrypted profile — every one of the 12,226 SQLCipher database pages authenticated, and all 297 attachments decrypted and verified

No names, no case data — just the volume these desktop apps quietly keep on disk. And as with the other LEAPPs, the validation counts live right in each module's header: open the [Artifacts page](https://leapps.org/artifacts), hit the DLEAPP filter, and expand any parser's samples.

## How to get it

Grab the packaged releases from the [releases page](https://leapps.org/releases#section-dleapp) — CLI and GUI builds for Windows (x64 and arm64), macOS (Intel and Apple Silicon), and Linux (x64 and arm64). No Python installation required.

Prefer to run from source? Clone [the repo](https://github.com/abrignoni/DLEAPP), then:

```
pip install -r requirements.txt
python dleapp.py -t fs -i /path/to/profile -o /path/to/output
```

Or launch the GUI with `python dleappGUI.py`. Reports open in your browser or load straight into [LAVA](https://leapps.org/releases#section-lava).

## Contribute

The Chromium container readers (Simple Cache, Local Storage LevelDB) are reusable by any future Electron application parser — Slack, Teams, Telegram Desktop, and friends are all waiting for someone to take them on. If you have done research on a desktop application, DLEAPP is where it belongs. The [module writing guide](https://leapps.org/blog-post?post=2026-06-14-how-to-write-an-ileapp-module) applies here too.

Happy hunting! 🔎
