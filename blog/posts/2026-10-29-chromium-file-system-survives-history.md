---
title: Clearing History Does Not Clear Chromium's File System Storage
date: 2026-10-29
author: Alexis Brignoni
tags: [ALEAPP, Android, Chromium, Chrome, browsers, artifacts, research]
excerpt: Websites can save real files inside a Chromium browser. On Android, those files stayed after browsing history was cleared in a known-data test. ALEAPP now reads them, building on Ryan Benson's 2019 work.
---

# Clearing History Does Not Clear Chromium's File System Storage

![A wooden desk at night under a green lamp. On the desk, a phone shows a History screen with every row blank and a few sparkles around it, as if wiped clean. Below, the desk's drawer is pulled open and full of colored file folders tabbed 000 to 004, two with papers sticking out.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-29-chromium-file-system-survives-history/chromium-file-system-hero.webp)

Websites can keep files inside your browser. Not cookies, not a database. Actual folders and files. Chromium gives sites APIs to do this, and the files sit in the browser profile under `File System`.

Credit first. Ryan Benson explained this store for desktop Chrome back in 2019 in [Deciphering Browser Hieroglyphics: FileSystem (Part 3)](https://hindsig.ht/blog/deciphering-browser-hieroglyphics-leveldb-filesystem/), and Hindsight parses it. The Origins and Paths LevelDBs, the numbered site folders with their `t` and `p` subfolders, the data files with no extension: it is all there. Go read it. What follows builds on his work.

What is new here is Android, a newer API that writes to the same place, and what happens when a user clears their history.

## Where it lives on Android

The store sits in any Chromium profile, at `<package>/app_*/Default/File System`. That covers Chrome, Edge, Samsung Internet and DuckDuckGo, plus apps that show web pages in a WebView.

On our test images, ALEAPP found 33 site records on 16 of 22 images, across all of those browsers and one app's WebView.

## The newer API writes to the same place

Ryan's post predates the Origin Private File System (`navigator.storage.getDirectory`). On Chrome 124, a file written through it landed in this same store, in the same site folder as a file written through the older `webkitRequestFileSystem`. One store, two APIs. Good to know when you go looking.

## The test

Known data, on Chrome 124.0.6367.219 in an Android 15 emulator. A local test page at `http://localhost:8765` wrote one file through each API. Three snapshots followed.

1. **After writing.** Both files were there, with their names and the exact text the page wrote.
2. **After clearing browsing history only, for the last hour.** The test site's History rows were gone. The site's Origins record, its folder names, its file names and the file contents were all still there. One detail: Chrome rewrote the Origin Private File System file between the two snapshots, so that file's data path and its folder's time changed. Same name, same contents.
3. **Control: after clearing cookies and site data, for the last hour.** This one removed the site's folder and its files. It also left a deleted Origins record that still names the site, sitting in the LevelDB log until compaction.

Those leftover records turn up in real extractions too. Here are two of them, from a training extraction, as LAVA shows them:

![LAVA showing the Chromium File System API - Sites artifact with two rows. Both have State Deleted, Folder Present No and Browser Chrome. The Site and Site Key columns are covered with gray bars marked redacted.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-29-chromium-file-system-survives-history/lava-sites-deleted-redacted.webp)

*Two deleted site records in a training extraction. The site names are redacted.*

So the History screen can be empty while the files a site saved are still on the device. Correct? That is what the known data shows.

## Reading the records

The format below comes from the Chromium source at commit [3a50e01](https://github.com/chromium/chromium/tree/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755) (tag 130.0.6723.58).

- **Origins** keys look like `ORIGIN:<scheme_host_port>`, and each stores the name of the site's numbered folder ([sandbox_origin_database.cc](https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_origin_database.cc#L253-L258)). A port of 0 means the scheme's default port ([database_identifier.cc](https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/common/database/database_identifier.cc#L101-L104)). The test site was `ORIGIN:http_localhost_8765`.
- **Paths** keys look like `CHILD_OF:<parent id>:<name>`, and each numeric id holds a parent id, a data path, a name and a time ([sandbox_directory_database.cc](https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L38-L49)).
- **Only folders keep a usable time.** Chromium updates a folder's time whenever something inside it is created, copied, moved or removed ([obfuscated_file_util.cc](https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L103-L106)). A file's time comes from its data file instead ([obfuscated_file_util.cc](https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L1144-L1156)). In the test, both file entries stored a time of 0.
- **A deleted `CHILD_OF` key** means a name was removed from that folder by a delete, a rename or a move. It tells you the name and the parent folder, and nothing else.

## What a record means, and what it does not

A site record means the site opened this storage. It does not mean the site saved anything. On our test images, 30 of the 31 live site records had no saved folders or files. Do not read a record as "this site stored data here" without looking at the Paths.

It also does not tell you when the browser was used or who used it. The Origins database stores no time.

Storage a site keeps while it is embedded in another site lives somewhere else, under `WebStorage/<bucket>/FileSystem`. ALEAPP does not read that one.

## The limits

One Chrome version, one emulator, and only the "last hour" time range. WebView apps and compaction timing were not tested. If you test this on other versions or devices, please share what you find. Send a pull request or reach out, we will be happy to add it.

## In ALEAPP

Two new artifacts, added in [ALEAPP #1839](https://github.com/abrignoni/ALEAPP/pull/1839) and coming in the next release:

- **Chromium File System API - Sites**: the site records, live and deleted, with the folder each one points to.
- **Chromium File System API - Files**: the folders and files each site saved, rebuilt from its Paths database, with the saved files shown as media.

The notes on each artifact carry the Chromium source citations and the test details.

Thanks again to Ryan Benson. His post did the hard part years ago. This just follows it to Android.

Hope this helps.
