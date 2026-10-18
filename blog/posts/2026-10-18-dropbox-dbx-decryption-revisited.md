---
title: Dropbox DBX Decryption, Nine Years Later
date: 2026-10-18
author: Alexis Brignoni
tags: [DLEAPP, Windows, Dropbox, cloud, artifacts, research]
excerpt: An update to the 2017 Zena Forensics post on decrypting Dropbox DBX files. The key moved out of DPAPI and into a file next to the databases. Heather and I built DLEAPP artifacts that read it, plus the sync history, file trees, thumbnails and more.
---

# Dropbox DBX Decryption, Nine Years Later

![A dark steel safe stands open, gold light spilling out of it. Taped to its own side is a paper file tag holding a gold key, with a dotted line running from the key to the open door. Out of the light float an account card, a sync icon, two photo thumbnails, a timeline and a folder. The only text is .dbx on the front of the safe.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-18-dropbox-dbx-decryption-revisited/dropbox-dbx-hero.webp)

*Figure 1: the safe is still locked. The key is just taped to the side of it now.*

If you have worked a Windows case with Dropbox on it, you probably know the 2017 post on the Zena Forensics blog by dfirfpi, [Brush up on Dropbox DBX decryption](https://blog.digital-forensics.it/2017/04/brush-up-on-dropbox-dbx-decryption.html). It built on research by Nicolas Ruff and Florian Ledoux, and it came with an open source toolkit, [decwindbx](https://github.com/dfirfpi/decwindbx). For years that was how examiners opened the encrypted `.dbx` files the Dropbox client keeps in the user profile.

That method stopped working on current clients. This post is the update: what changed, what we can read now, and what is now in DLEAPP thanks to work by Heather ([charpy4n6](https://github.com/charpy4n6) on GitHub) and me.

## How it used to work

In plain terms, the 2017 recipe was:

1. Dropbox kept a key in the user's registry hive.
2. That key was locked with DPAPI, the Windows feature that ties a secret to the user's login. To unlock it you needed the user's password or their DPAPI master key material.
3. With the key unlocked, a fixed derivation produced the database key, and the `.dbx` files opened as SQLite databases.

Step 2 was the hard part. No password, no master key, no data.

## What changed

Around 2021, people on the decwindbx issue tracker noticed the registry value had a new name and that the payload [no longer appeared to be DPAPI protected](https://github.com/dfirfpi/decwindbx/issues/1#issuecomment-808895040). The scripts were never updated for it.

The install Heather gave me goes a step further. The key is in a small file right next to the databases. Inside each Dropbox instance folder under `AppData\Local\Dropbox` sits that file, `ks_Client1` in `instance1` and `ks_Client` in `instance_db`. Inside it:

- a version number and a length,
- the 16-byte key, stored in the clear,
- a checksum (HMAC) that verifies with the same constant decwindbx published in 2017.

The rest of the 2017 derivation still applies. Run the stored key through the same PBKDF2 step with the same salt and iteration count and you get the database key. Each page of the database is then AES encrypted, with the page's own nonce stored in its last 12 bytes. That page layout is something we worked out on this install. I did not find it published anywhere, so treat it as tested on one client, not as documentation.

What it means for you: **no DPAPI, no Windows password, no master keys.** If the extraction has the `AppData\Local\Dropbox` folder, DLEAPP can open `config.dbx` and `instance.dbx` on its own.

## What you get

All of these show up under the Dropbox category in the DLEAPP report and in LAVA.

**Dropbox Linked Account** (the decrypted `config.dbx`). The account the client is linked to: email, display name, account ID, user ID, the device's display name, the local Dropbox folder and the client version, plus when the client was first linked and last started. The database also holds an OAuth refresh token and a client key pair. Those are credentials, so DLEAPP leaves them out of the report and says so in the log.

**Dropbox Sync History.** Uploads, downloads, moves and deletes, with the local path, the server path and a file ID you can follow into the other artifacts. Where the client cached a thumbnail for that file, you see the picture right on the row.

**Dropbox Sync Engine Items.** Dropbox's current sync engine keeps three file trees: what is in the cloud, what is on disk and what was last in sync. This artifact lists every file and folder across the three, with sizes, times and hashes, and the thumbnail where one exists.

**Dropbox Sync Engine History.** This is the one that surprised me. Heather noticed that the sync engine's write-ahead log keeps earlier versions of those trees, so DLEAPP replays it and lists what changed: files added, removed, renamed, moved and restored. On her test install it showed a rename, including the old name, which we did not find in any other Dropbox file DLEAPP reads. It only shows what is still in the log, so a missing change is not proof it never happened.

**Dropbox Client Events.** Usage events the client logs for itself, such as preference views, selective sync and sharing actions. Some sharing events carry a file ID you can match to a file. These are the client's own telemetry. A row says the client logged an interface event, not what the person meant to do.

**Dropbox Thumbnails, Storage Files, Upload Records, Account Info and Client Info.** The cached thumbnails on their own, the client's storage list with its offline flag as stored, block upload records, `info.json` and a few client and machine values.

## What it does not do

- It was built and tested on **one Windows install** of a personal account. Business and team accounts, other client versions and other Windows builds have not been tested.
- **Older clients** that keep the key in the registry are not decrypted. DLEAPP logs it when it finds a `config.dbx` with no key file beside it.
- **macOS** is not covered.
- A thumbnail shows the file as it was when the thumbnail was made, not necessarily at the time of the event on the same row.
- Several fields are undocumented. The artifact notes in the report say which values are read as stored, which were checked against another file and which are still unexplained. Please read them before you rely on a column.

## Credit

Heather did the heavy lifting on the sync engine side: the file trees, the write-ahead log history, the client events, upload records and the thumbnail cache. She also built a test install and kept a record of what she did on it, which is what let us check the output against known actions instead of guessing. I worked out the key file and the page encryption and added the Linked Account artifact and the inline thumbnails. We combined the two efforts into [one pull request](https://github.com/abrignoni/DLEAPP/pull/645).

None of this happens without dfirfpi's 2017 post and toolkit, and the Ruff and Ledoux research behind it. The constants published in 2017 still verify today. That is what good, open research looks like.

## Help us test it

If you have a Windows Dropbox install you can share for testing, especially a business account, an older client or one that still keeps its key in the registry, please reach out or [open an issue](https://github.com/abrignoni/DLEAPP/issues). Test data you create yourself is perfect. And if something in the output looks wrong, tell us. Send a pull request and we will be happy to look at it.

DLEAPP is free and open source under the MIT license, and it stays that way.
