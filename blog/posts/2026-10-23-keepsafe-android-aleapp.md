---
title: "KeepSafe for Android Caught an Intruder. It Was Me."
date: 2026-10-23
author: Heather Charpentier
tags: [ALEAPP, Android, artifacts, research, media]
excerpt: KeepSafe hides photos behind a PIN, a decoy vault and a fake calculator. It also quietly photographs anyone who gets the PIN wrong. I found that out by finding the top of my own head in the extraction. Here is how the app stores its data and what the new ALEAPP module reports.
---

# KeepSafe for Android Caught an Intruder. It Was Me.

Every examiner has a moment where the data looks back at them. Mine came while building a new ALEAPP module for KeepSafe. I was scrolling through a folder called `files/breakin`, opened a file with a `.ksd` extension, and there it was: an extremely unflattering, up-the-nose-adjacent photo of the top of my head.

I did not know KeepSafe did that, and on the free version there is no way to find out: the app takes the photo either way, but you have to pay for Premium to see your alerts. At some point I had typed one wrong PIN, and the app had taken my picture as an intruder. In my own vault. On my own phone.

More on my forehead later. First, the app.

## What KeepSafe is

KeepSafe (package `com.kii.safe`) is a photo and video vault app. It:

- Keeps photos and videos behind a PIN, in albums.
- Backs them up to KeepSafe's cloud.
- Has a Trash for deleted items.

It also takes a photo of anyone who enters a wrong PIN (Intruder Alerts).

Optional Premium features, per [KeepSafe's help center](https://support.getkeepsafe.com/hc/en-us/articles/209134106), include viewing Intruder Alerts, a Decoy Vault, a Calculator disguise, Album Lock and Space Saver. The app offers a 3-day free Premium trial.

### Premium features and my test data

My test account never had a paid Premium subscription, and most of the Premium features above were not in use in the data:

| Premium feature | What the test data showed |
|---|---|
| Intruder Alerts | **Present**: one break-in record with its photo, captured on the free version. Without Premium I could not view it in the app. |
| Decoy Vault | A built-in album of type `decoy` exists, with no files in it, since Decoy Vault is a Premium feature. |
| Calculator | The `secret_door` preference was `CALCULATOR`, but the calculator disguise was not active on the phone, since it is a Premium feature. |
| Space Saver | One space-saver record, with `isSpaceSaved` set to false, since Space Saver is a Premium feature. |
| Album Lock | Not seen in the album records. |
| Cloud storage | All 27 items had `backupState` set to `backedUp`, under the Basic limit of 200. That is the phone's own record; nothing from KeepSafe's servers was examined. |

So if you are looking for Decoy Vault content, Calculator disguise activity or Space Saver behavior, my test data will not show you what those look like when used. That is something to test on a device with an active Premium subscription.

## Where the data lives

Everything is under `/data/data/com.kii.safe/`, and there is more variety than you might expect:

| Location | Format | What is in it |
|---|---|---|
| `files/*_db/*.cblite2/db.sqlite3` | Couchbase Lite (SQLite with Fleece-encoded records) | Media, albums, break-ins, browser tabs, sync state |
| `files/media/XX/ID/` | Plain files | The vault media: `PHOTO`, `VIDEO` or `GIF`, plus `PREVIEW` and `THUMBNAIL` |
| `files/breakin/*.ksd` | JPEG, despite the extension | Break-in photos |
| `files/accountsv2.mpack` | MessagePack | Account and device records |
| `shared_prefs/*.xml` | Android preferences | Sign-up date, login times, lock settings, theme, trash, IDs |

### Reading the Fleece-encoded records

KeepSafe's databases are SQLite files. In each one, Couchbase Lite keeps the records of the default collection, the only one KeepSafe uses, in one table, `kv_default`, and each record's details (for a vault file, an album or a break-in) sit in a single `body` column as a binary blob in Couchbase's **Fleece** format. The photos and videos themselves are separate files, under `files/media` and `files/breakin`.

![DB Browser for SQLite showing the kv_default table of KeepSafe's mediaDb. The body column, outlined in red, holds a BLOB for every record. One record's body is selected and shown on the right as hex bytes with a text column, outlined in blue.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-23-keepsafe-android-aleapp/keepsafe-fleece-body.webp)

*Figure 1: KeepSafe's media database in DB Browser for SQLite. Every record is one blob in the `body` column; the right side shows one of them byte by byte.*

Fleece is a compact, JSON-like binary format. Two things make it awkward to read by hand:

- **It is read from the end.** The last two bytes of the blob point back to the top-level record (with one more hop when the record is larger than 64 KB), and any value that does not fit inline is reached through a pointer that always points backwards ([Fleece format notes](https://github.com/couchbase/fleece/blob/8ce5f690480b77c0f93d03f456a29828b5a55d66/Fleece.md#L54)).
- **Many field names aren't in the record.** A field name of up to 16 characters, made only of letters, digits, `_` or `-`, is stored as a small number, up to 2,048 names per database ([SharedKeys.hh](https://github.com/couchbase/fleece/blob/8ce5f690480b77c0f93d03f456a29828b5a55d66/Fleece/Core/SharedKeys.hh#L111-L112)). The list that turns those numbers back into names is stored once per database, in the `kv_info` table under the key `SharedKeys` ([DocumentKeys.hh](https://github.com/couchbase/couchbase-lite-core/blob/ea2f962af6d51d3eac84531fa4de2f3a1593a09e/LiteCore/Storage/DocumentKeys.hh#L30)). Longer names, like the 17-character `createdAtOnDevice` in Figure 1, are stored as text in the record itself.

So a hex view of a `body` shows the values (`image/jpeg`, `backedUp`, a SHA-1 hash) but not the names of most of the fields they belong to. Decode it with `SharedKeys` and you get something readable:

```json
{
  "modelType": "file",
  "type": "photo",
  "originalFilename": "Screenshot_20260911-095906.png",
  "createdAt": 1792603629.427,
  "isInTrash": false,
  "media": [
    { "type": "photo", "mimeType": "image/png", "width": 1008, "height": 2244,
      "dataSize": 909941, "localHash": "74bff4feb70dfeb80ca8637af90a278d815af8d3" },
    ...
  ]
}
```

The ALEAPP module includes a small Fleece decoder written in plain Python. It reads `SharedKeys` first, then decodes each record's `body`. One more detail: when a record is deleted, Couchbase saves it, marked as deleted, in a second table, `kv_del_default`, which has the same columns, and removes it from `kv_default` ([BothKeyStore.cc](https://github.com/couchbase/couchbase-lite-core/blob/ea2f962af6d51d3eac84531fa4de2f3a1593a09e/LiteCore/Storage/BothKeyStore.cc#L44-L47)).

## The artifacts

The module adds five artifacts under a **KeepSafe** category.

### KeepSafe - Media Files

One row per file in the vault, with the thumbnail and the original embedded in the report.

The part I like most is that the module also opens each file and reads what the file itself says:

- **For photos:** EXIF date and time with its UTC offset, Make, Model, Software and GPS.
- **For videos:** the MP4 `mvhd` creation time (seconds since 1904, because MP4 inherited QuickTime's calendar), plus the `com.android.manufacturer` and `com.android.model` keys the Android camera writes.

Every one of those values names its source in the report, so you always know whether you are looking at EXIF, the MP4 header or KeepSafe's database.

That separation matters. KeepSafe's `createdAt` is **not** when a photo was taken; it is when the file was added to KeepSafe or captured with the app. My photos from August all had a `createdAt` in October, within seconds of each other, when I added them to the vault. The EXIF date and `createdAt` tell two different stories, and you want both.

Also, on my phone the camera photos still had their GPS tags, but every value was zero or empty. That one is on me: I never turned location on for my photos. The module reports that as "EXIF GPS tags present but empty" rather than putting a pin in the ocean at 0,0.

![The KeepSafe - Media Files page of an ALEAPP report, showing a selection of columns: Date/Time In File (UTC), Created At, Date/Time In File (as stored), Metadata Source, Make, Model, File Metadata Note, Thumbnail and Original Filename. Five rows are shown, each with a thumbnail: a Pixel 8 Pro video and photo with MP4 and EXIF metadata, a video recorded in KeepSafe with an MP4 date but no make or model, and two screenshots with EXIF dates.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-23-keepsafe-android-aleapp/aleapp-keepsafe-media-files.webp)

*Figure 2: the KeepSafe - Media Files report, with a selection of its columns. The date in the file and `createdAt` sit side by side, and each file value names its source.*

### KeepSafe - Albums

The album records: name, ID, type, and how many files point at each one. On my phone there were two built-in `MAIN` albums, one with type `private` and one with type `decoy`, plus the one I created.

![The KeepSafe - Albums page of an ALEAPP report with three rows: a MAIN album of type private with 25 files, a MAIN album of type decoy with 0 files, and an album named "things I recorded from within keepsafe app" with 2 files.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-23-keepsafe-android-aleapp/aleapp-keepsafe-albums.webp)

*Figure 3: the KeepSafe - Albums report. The `decoy` album is there with no files in it.*

### KeepSafe - Break-in Records

Each break-in record has the time, the PIN that was typed in plain text, and the photo. ALEAPP shows the photo right next to the PIN and the time.

![The KeepSafe - Break-in Records page of an ALEAPP report with one row: the time captured, the break-in photo, the attempted PIN, Is PIN Lock Type, Is Read, the photo file path and the record ID.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-23-keepsafe-android-aleapp/aleapp-keepsafe-break-in-records.webp)

*Figure 4: the KeepSafe - Break-in Records report. Yes, that's me.*

### KeepSafe - Browser Tabs

Tabs from the in-app browser: title, URL, when each was created and last accessed, plus the session's search engine and current tab.

### KeepSafe - Account & Preferences

Values from the account file `accountsv2.mpack`: package, app version code, email, owner ID, device name, device ID, country, language and push token.

![The first page of the KeepSafe - Account & Preferences report in ALEAPP: numbered rows with Group, Field, Value, Value as UTC and Stored Key columns. Rows 1 to 11 are the Account values, from Package to Firebase Push Token, followed by the first Account & Login preferences.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-23-keepsafe-android-aleapp/aleapp-keepsafe-account-preferences.webp)

*Figure 5: the first page of the KeepSafe - Account & Preferences report.*

After those come the preference values, grouped:

- **Account & Login:** sign-up date, login time, last activity
- **Install & Usage:** install time, first install, first open, three launch counters
- **Device Identifiers**
- **Lock & Security:** PIN hash, lock type, Calculator disguise setting
- **Appearance:** lock style, theme color, dark mode
- **Trash**
- **Private Browser & Web**

One honest warning about the launch counters: KeepSafe keeps three of them, and on my phone they said 9, 8 and 5. I do not know what each one counts, so the report shows all three under their own names and does not pick a winner.

## About my forehead

Back to that `.ksd` file.

A wrong PIN gets a break-in record and a photo, Premium or not. Mine is a view from below: ceiling tiles, two office lights, the bottom of a monitor, and in the corner my forehead and eyes, taken at the exact moment I was thinking "wait, what was the PIN?" The record kept the wrong PIN I typed, to the millisecond, right next to my forehead.

![A photo taken from below, looking up at a white tiled office ceiling with two fluorescent light fixtures. The bottom edge of a computer monitor crosses the top of the frame. In the bottom right corner, only the top of a person's head, forehead and eyes are in the shot, looking down at the phone.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-23-keepsafe-android-aleapp/keepsafe-breakin-photo.jpg)

*Figure 6: KeepSafe's break-in photo of me, the intruder, in my own vault, on my own phone. Rotated upright, resized, and metadata removed for the blog; the file in the extraction is a full-size JPEG with a `.ksd` extension.*

Now picture this happening on a real case.

You have a seized phone. KeepSafe is on it. Free version, paid version, doesn't matter. Someone on the team decides to "just try a couple of common PINs" before sending it to the lab. Each wrong guess gets a timestamp, the PIN they typed, and a photo of their face, all saved neatly into the suspect's data.

Congratulations: you are now in the evidence. Your forehead has a chain of custody. Your face will be in the report, embedded at 300 pixels, right under the vault media. Opposing counsel will ask who the person in the break-in photo is, and the honest answer will be "that's Dave from our unit, and he really thought it was 0000."

The less funny version, which is still worth a laugh:

- **Manual attempts on the device create data.** On KeepSafe they create records with your PIN guesses and your picture, even on the free version, where the owner can't see them. Document every attempt in your notes, because the app certainly will.
- **Not every break-in record is the subject.** Before you call someone an intruder, check the time against your own handling of the device. The intruder might be you.
- **If you test apps on your own phone, check your break-in folder before sharing data.** Ask me how I know.

## Reading any Couchbase Lite database

KeepSafe is not the only app that keeps its data in Couchbase Lite, and the ALEAPP module only reads what KeepSafe stores. For everything else there is [cblite-parser](https://github.com/abrignoni/cblite-parser), a read-only reader for Couchbase Lite databases and the Fleece documents inside them. It is pure Python with no dependencies, free and open source under the MIT license, and it does not open the database in place: it copies the database and its `-wal` and `-shm` to a temporary folder and reads the copy.

It reads:

- every document of every collection, decoded, with its revision ID, sequence and flags;
- the revision tree, including any older version of a document the database kept;
- deleted documents in the `kv_del_` tables;
- the database's own records in `kv_info`, including the shared key table;
- blob references, with a check that each blob file matches the digest the document recorded;
- rows that exist only in the `-wal`.

`python -m cblite_parser export <store> <new folder>` writes a report for someone who would rather not use a command line: an `index.html` that opens in any browser with no network, plus `documents.csv`, `revisions.csv`, `blobs.csv` and an `export_info.json` with the size and SHA-256 of every source file it read.

KeepSafe on iOS uses Couchbase Lite too. Here is cblite-parser's export of KeepSafe's iOS store from the iOS image in Cody Bounds' public Digital Forensics Cookbook Datasets (iOS 17.5.1, listed on [The Evidence Locker](https://theevidencelocker.github.io/)):

![The top of a cblite-parser HTML export of photovault.cblite2: the export time and tool version, a Source table listing db.sqlite3, its -wal and -shm with their sizes and SHA-256 hashes, a Database section showing versioning 1 (revision trees, 3.x schema), 28 shared keys and 30 documents with 0 tombstones, collapsed kv_info and shared key tables, and the start of the documents table with sequence, key, revid, flags, expiration and body columns.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-23-keepsafe-android-aleapp/cblite-export-overview.webp)

*Figure 7: the top of the HTML export. The source files are hashed, and the database's own records come before the documents.*

![One document from the same export, expanded: the full decoded body of a KeepSafe photo record with its field names, including id, ownerId, type, importedAt, albumId, originalFilename, a media list for the photo, thumbnail and preview with their sizes and hashes, backupState and createdAtOnDevice.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-23-keepsafe-android-aleapp/cblite-export-document.webp)

*Figure 8: one document expanded. The field names come from the database's shared key table, and `createdAtOnDevice` is there as text, as described above.*

## Getting the module

The KeepSafe module is now part of ALEAPP ([abrignoni/ALEAPP#1758](https://github.com/abrignoni/ALEAPP/pull/1758)). It was built and checked against a full file-system extraction of my own test phone, a Pixel 8 Pro running KeepSafe 14.23.0.

And if you try it on your own phone first, you may find someone familiar in the Break-in Records. Smile.
