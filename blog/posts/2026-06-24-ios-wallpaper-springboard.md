---
title: Recovering Pre-iOS 16 Wallpaper from SpringBoard
date: 2026-06-24
author: James Habben
tags: [iLEAPP, iOS, SpringBoard, artifacts, media]
excerpt: A quick research note on extracting older iOS wallpaper files from SpringBoard, including legacy cpbitmap conversion and JPG thumbnail handling in iLEAPP.
---

# Recovering Pre-iOS 16 Wallpaper from SpringBoard

This started from a Discord conversation about SpringBoard artifacts in [iLEAPP](https://leapps.org/releases#section-ileapp).

We already had an icon parser that recovered the home screen layout: apps, folders, widgets, stacks, and the dock. Brigs then updated that work so iLEAPP could draw a visual representation of how the screen would have looked. That raised the next obvious question: if we can show the icons, what about the wallpaper behind them?

So I started digging into the wallpaper side of SpringBoard. It is not always the flashiest artifact, but it can be very human. A wallpaper may be a personal photo, a downloaded image, or just one more small detail that helps explain what a user was seeing every day.

This post is about the older side of that work: **pre-iOS 16 wallpaper files stored under SpringBoard**. There is newer PosterBoard wallpaper support too, but I am going to save that for a follow-up post so this one can stay focused.

The artifact appears in iLEAPP as **SpringBoard Wallpaper** in the **iOS Screens** category.

![iLEAPP module selection showing the SpringBoard Wallpaper artifact](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-06-24-ios-wallpaper-springboard/ileapp-springboard-wallpaper.png)
*Figure 1: iLEAPP GUI showing Springboard artifact selection*

## Where the files live

On older iOS versions, wallpaper files can show up under `Library/SpringBoard`. In an iOS 15 test image, I found files like:

```text
Library/SpringBoard/LockBackground.cpbitmap
Library/SpringBoard/LockBackgrounddark.cpbitmap
Library/SpringBoard/LockBackgroundThumbnail.jpg
Library/SpringBoard/LockBackgroundThumbnaildark.jpg
Library/SpringBoard/OriginalLockBackground.cpbitmap
Library/SpringBoard/OriginalLockBackgrounddark.cpbitmap
```

That mix is important. The `.cpbitmap` files need conversion before they are useful to most examiners, while the JPG thumbnails can be checked into iLEAPP's media pipeline directly.

![Crush Forensics file listing showing iOS 15 SpringBoard wallpaper files](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-06-24-ios-wallpaper-springboard/crush-ios15-lockbackground.png)
*Figure 2: Crush Forensics file listing showing wallpaper files*

For this first pass, the SpringBoard wallpaper artifact searches for background files using these patterns:

```text
**/SpringBoard/*Background*.cpbitmap
**/SpringBoard/*Background*.jpg
**/SpringBoard/*Background*.jpeg
**/SpringBoard/*Background*.png
**/SpringBoard/*Background*.heic
```

The JPG pattern is there because those thumbnail files are definitely present in real backups. The PNG and HEIC patterns are included as practical coverage for image-backed variants if they appear in a sample. If the file is already a standard image, iLEAPP just checks it into the media output.

This works for both iTunes/logical backups and full file system extractions. In a backup, the files may be surfaced through the backup manifest and domain layout. In a full file system extraction, they may appear closer to their on-device paths. Either way, the artifact is looking for the SpringBoard background files and then preserving the source path in the output.

## The cpbitmap part

The more interesting challenge is `.cpbitmap`.

Those files are not normal PNGs or JPGs. The converter added to iLEAPP reads the width and height from the cpbitmap trailer, chooses a row alignment based on the installed iOS version, converts BGRA pixel data into RGBA, writes a PNG with Pillow, and then checks the converted image into the report.

The expected alignment changes by iOS version:

| iOS version | Expected alignment |
|-------------|--------------------|
| iOS < 10 | 4 |
| iOS >= 10 and < 12 | 8 |
| iOS >= 12 | 16 |

iLEAPP uses `context.get_installed_os_version()` to pick the first alignment to try. If that does not match the file size, the converter falls back through the other known alignments. That little fallback matters because forensic data does not always arrive in the neat shape you hoped for.

The cpbitmap conversion logic was adapted from Harold Thetiot's MIT-licensed `cpbitmap-to-png` project. That original project is JavaScript-based, and it was really nice to have working code to port instead of starting from a blank page. The iLEAPP version keeps the same core idea, but fits it into the artifact framework and media output flow.

I also added some basic guardrails:

- Minimum file size checks
- Positive width and height checks
- A maximum pixel count
- File-size validation before conversion
- Logging when conversion or media check-in fails

None of that is glamorous, but it is the kind of boring work that makes a parser nicer to run against unknown data.

## What it looks like

In [LAVA](https://leapps.org/releases#section-lava), the converted wallpaper images show up alongside the source filename, type, variant, status, and location. For this iOS 15 sample, the artifact recovered the current, dark, original, and original dark lock screen backgrounds from SpringBoard.

![LAVA table showing converted iOS 15 SpringBoard wallpaper artifacts](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-06-24-ios-wallpaper-springboard/lava-ios15-wallpaper.png)
*Figure 3: LAVA showing converted wallpaper images*

The status column is useful because it tells you whether a file was converted from cpbitmap or checked in directly as media. The source path is also shown, because with wallpaper artifacts the location can be part of the story.

## A quick tool note

The file listing screenshot above came from [Crush Forensics](https://github.com/kalink0/crush-forensics), an open source forensic file viewer by kalink0. I have been using it while poking through these samples because it makes this kind of quick visual triage comfortable: search for a filename, preview the image, and keep moving.

That is really the spirit of this artifact too. It is a small parser, but it turns a handful of older SpringBoard files into something easier to review. Next up: the newer iOS 16+ PosterBoard side of wallpaper storage.
