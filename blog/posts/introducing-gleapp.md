---
title: Meet GLEAPP, Media Triage Built for the Backlog
date: 2026-09-25
author: Alexis Brignoni
tags: [GLEAPP, media, triage, Project VIC, images, video, DFIR, open source]
excerpt: A modern extraction can hold tens of thousands of images and videos. GLEAPP hashes and de-duplicates them, finds the same face across the case, puts geolocated files on an offline map, and gives you a gallery built for categorizing. Free and open source.
---

Pull a full filesystem extraction off a current phone and count the pictures. It is not a few hundred anymore. It is tens of thousands: camera roll, app caches, message attachments, thumbnails, stickers, the lot. Somebody has to look at them, and in the cases that matter most, what they find decides where the case goes next.

GLEAPP exists for that job. It is an open-source toolkit for triaging and analyzing large sets of images and video, written by Heather Charpentier & Alexis Brignoni and now part of the LEAPP family. It takes the media, hashes and de-duplicates it, pulls the metadata, extracts key frames from video, matches against known-hash lists, and puts all of it in a local review gallery built for the way examiners actually work a backlog.

One thing up front, because it matters for a tool in this space. GLEAPP is a defensive investigative tool for authorized examiners. It ships no illegal-content hash database, does not download or connect to one, and does no content classification. Categorization is always a human decision. The categories you see in the screenshots below were applied to a test image for demonstration. None of those files is what the label says.

## Point it at the evidence

![The GLEAPP launcher in a dark theme. A Recent Cases list shows one test case with 33,531 files. Below it, Open Existing Case, then a New Case form with fields for case name, case folder and examiner, and an Evidence to Ingest box that accepts folders, zip and tar archives, E01 and raw disk images, split image sets and JSON job files. Two checkboxes at the bottom read Face and skin tone pre-processing, and Enable hash stash matching.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/introducing-gleapp/launcher.webp)
*Figure 1: Start a case, name the examiner, and add as many sources as the case needs. They all ingest into one case.*

You start by telling GLEAPP where the media lives, and it takes more than a folder. A full filesystem extraction, zip or tar, is read in place, so the case stays small and every file is registered by its path on the device. A disk image, an E01 with its segments or a raw image, has its filesystems walked file by file, which means each file keeps the name, the path and the dates the filesystem recorded rather than turning up as a nameless carved blob. Recovering deleted media is there when you want it, from deleted filesystem records first and then by carving free space, and it stays a separate, deliberate step.

Add as many sources as you need. They land in one case, and you can add more evidence later without starting over.

## A gallery built for categorizing

![The GLEAPP review gallery for a test case of 24,867 files, sorted by faces. Along the top, a category bar lists the locked Project VIC categories numbered 1 to 5, plus an examiner category named Evidence numbered 6. Each thumbnail carries a colored category bar underneath, and a badge in the corner counts the faces detected in it. Two tiles carry a badge reading approximately equal to 2, marking a visual duplicate stack. A filter sidebar on the left offers category, flag, type and source, and collapsible sections for known hashes, faces and skin, duplicates, errors and location.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/introducing-gleapp/gallery-categories.webp)
*Figure 2: The review gallery. Every case starts with the locked Project VIC 2.0 (US) categories, and the examiner adds their own from code 6 on.*

This is where the time goes, so this is where GLEAPP puts the most effort. Every case is seeded with the locked Project VIC 2.0 (US) category scheme, codes 0 through 5, and you add your own categories on top. Flags sit alongside categories and are independent of them, so a file can carry any number of labels your case calls for.

Categorizing is the review step. Filter to what is still uncategorized, work through it with the keyboard, and the cursor moves to the next file on its own. Every action is saved to the case the moment you take it, with timestamped backups and an audit log of what was done.

The volume problem is handled before you ever see a thumbnail. GLEAPP de-duplicates in three tiers: files that are byte-for-byte identical stack into one, pictures that are the same to the eye stack too (the badge that reads **≈ 2**), and a looser similar-group cluster is there to browse. The same meme saved by four apps shows up as one stack instead of four separate tiles.

## Find the same face across the case

![The gallery showing files with a matching face, 250 similar files, with a banner reading Showing files with a matching face and a Back to all button. Each tile carries a similarity percentage in its corner, from 100 percent down to about 62 percent, and several tiles are video frames with a duration shown. One tile in the third row is blurred. On the right, a details pane shows the selected image with boxes drawn around two detected faces, its category, Find similar and Hex view buttons, and its source, type, original name and full path inside the extraction.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/introducing-gleapp/matching-faces.webp)
*Figure 3: Click a face and GLEAPP lists every file in the case with a matching face, ranked by similarity, stills and video frames alike.*

With face screening turned on, GLEAPP detects faces as the media is processed. Open an image, click the box around a face, and GLEAPP lists every file in the case carrying a matching face, ranked by similarity. That includes key frames pulled from video, so a person who appears in a clip turns up next to the photos they appear in. The matching runs entirely inside the case. Nothing is sent anywhere to do it.

*Find similar* does the same thing for the whole picture rather than a face, across stills and video key frames, so a still can lead you back to the video it came from.

## Where a picture was taken, without leaving the machine

![The details pane for a geolocated photo of a gas pump. Under the photo, a dark offline map shows a street grid with a red pin, highway shields for routes 90 and 156, and an OpenStreetMap contributors attribution. Below the map, the file name, its category, and its source, type, original name and path.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/introducing-gleapp/details-map.webp)
*Figure 4: A geolocated file shows its location right in the details pane.*

![A full-window dark map with a single red pin among labeled streets, campus buildings, libraries and restaurants, with zoom controls in the corner.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/introducing-gleapp/full-map.webp)
*Figure 5: The same location opened full size, still drawn from the offline basemap.*

When a file carries GPS coordinates, the details pane shows where it was taken on a map, and you can open that map full size. The map is drawn from an offline basemap you import once, so looking at where a picture was taken does not send that location to a map service, which is how it should work for casework.

## Known hashes, both ways

GLEAPP imports Project VIC case files directly, keeping each record's MediaID, series, flags and tags, and it exports back to Project VIC with your categories filled in. It also takes CAID-style and plain hash lists into a case or into a shared global store, along with the NSRL for known-good files. A known-good match can mark an uncategorized file non-pertinent and get it out of your way, and a match against a Project VIC set brings that record's details into the gallery and every report.

## Reports that stand on their own

![The top of an HTML report for a test case. The header shows the GLEAPP logo, the case name, and fields for agency, case number, item number, examiner, when it was generated and the timezone times are shown in. Below it, collapsible sections for report contents and for locations, buttons to jump to each category section, and switches for Blur images and Dark mode, both turned on.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/introducing-gleapp/report-header.webp)
*Figure 6: The report header carries the case details, and the Blur images switch is on by default.*

![The report contents summary. A ring chart with 131 files in the middle, and a table listing files in the report as 120 images, 10 videos and 1 other file, broken down by category and by flag, with 22 files matching a known set out of 29,351 media files in the case.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/introducing-gleapp/report-summary.webp)
*Figure 7: What the report covers, at a glance: counts by category, by flag and by known-hash match.*

The HTML report is a single contact sheet you can hand to someone else. It opens with the case details, then a summary of what it contains, then the files grouped by category. Pick which categories go in, and the report says so at the top.

![The report's Locations section, showing 23 geolocated files on a map of the northeastern United States. Points fan out from a cluster so each one can be clicked, and a smaller group of three sits near Atlanta. Below the map, a note explains the map was drawn on the imported offline basemap, and a Jump to a file list names each geolocated file.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/introducing-gleapp/report-locations.webp)
*Figure 8: The report draws its own location overview. Click a point or a name to jump to that file.*

![Three file cards from the report. Each has a heavily blurred thumbnail, a category label, a small locator map with a red pin, and the file's metadata: file name, path on the device, EXIF capture time, filesystem created time, MD5 and SHA-1, file size, camera model and GPS coordinates, with a link to open the original.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/introducing-gleapp/report-blur-location.webp)
*Figure 9: Each file gets its own card: a blurred thumbnail, a locator map, hashes, capture times, camera and coordinates.*

The report draws its own maps from the same offline basemap, an overview near the top and a small locator map on each geolocated file's card. Those maps are baked into the report file, so a saved report works without a network connection, and it names the basemap and its hash so anyone reviewing it can load the same map. Each card carries what someone reviewing it will ask for: where the file came from on the device, its capture and filesystem times, its hashes, the camera, the coordinates, and a link back to the original.

Blurring is on by default. Thumbnails open blurred, and you hover over one when you need to see it clearly. Anyone who has done this work knows why that matters, and it should not be something you have to go looking for.

Beyond HTML, GLEAPP writes CSV and JSON, a KMZ of geolocated media for Google Earth with thumbnails embedded, an MD5 list, the Project VIC round trip, and a LAVA project so the case opens in the same viewer the rest of the LEAPP family uses.

## Give it a try

GLEAPP runs on Windows, macOS and Linux, and builds are on the [releases page](https://github.com/abrignoni/GLEAPP/releases/latest). It is free and open source under the MIT license. The full manual is built into the app under the Help button.

A big thank you to Heather for building this and putting it in the community's hands. If you find something that could be better, open an issue or send a pull request. We will be happy to take a look.
