---
title: "Full File System extractions in Zip: MAC times, part two"
date: 2026-10-23
author: Alexis Brignoni
tags: [iLEAPP, ALEAPP, RLEAPP, VLEAPP, DLEAPP, timestamps, zip, validation]
excerpt: The times stored inside full file system zips do not always mean what their labels say. CLBX zips put the access time in every slot, and GrayKey style zips carry a fourth time. Here is how CTF writeups and a photo's EXIF settled it, and what changed in the LEAPPs.
---

# Full File System extractions in Zip: MAC times, part two

![A zip file on the left fans out into four clocks labelled s1 to s4. A camera on the right holds its own clock. A red dotted line from the camera to the s3 clock ends in an X, and a green dotted line joins the camera to the s4 clock.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-23-ffs-zip-mac-times-part-two/ffs-zip-timestamps-hero.webp)

Back in May 2024 I [wrote about](https://abrignoni.blogspot.com/2024/05/full-file-system-extractions-in-zip-mac.html) MAC times inside full file system (FFS) extractions that come in zip format. I also put up a small script, [`extract_timestamps.py`](https://github.com/abrignoni/Misc-Scripts/tree/main/zipMACtimes) in my Misc-Scripts repo, that reads the timestamps a zip keeps for each file. The short version of that post: the zip specification only defines a modified time, so the creation and access times your tools show come from the extra field at the end of each entry.

This week I went back to that question with a bigger corpus and a sharper one. What do those extra field values actually mean, writer by writer? I expected a quick confirmation. I got two surprises instead. One of them changes what you should read for Cellebrite CLBX zips. The other one was solved by community CTF writeups, which is my favorite kind of solution.

Here is what I found, what I measured, and what I still do not know.

## What a zip actually stores

Every zip entry has a DOS date and time. The PKWARE zip specification ([APPNOTE](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT)) defines it in the MS-DOS format. That format has 2-second resolution and carries no time zone. In practice it is the wall clock of the machine that wrote the zip.

Think of it like a handwritten note that says "3 PM" with no city on it. You know the hour. You do not know where.

Here is a measured example. I have the same iPhone 14 Plus (UDID 00008110-0008196A2299401E) as it was released for Magnet Virtual Summit (MVS) 2025 and again for MVS 2026. For `/Applications/AppStore.app/AppIcon60x60@2x.png` both zips carry identical Unix timestamps in the 0x5455 extra field. The DOS times are one hour apart: 08:44:42 in one, 09:44:42 in the other. Same file, same phone, same stored instant. Different writer clock.

So the real times live in the extra fields. Two of them matter here:

- **0x5455, Info-ZIP extended timestamp.** Unix seconds, UTC. The Info-ZIP spec ([`extrafld.txt`](https://trac.netlabs.org/ports/browser/unzip/vendor/current/proginfo/extrafld.txt?rev=200)) defines three flag bits: bit 0 modification, bit 1 access, bit 2 creation. It also says the central directory copy carries the modification time only.
- **0x000a, NTFS.** Windows FILETIME values for modified, accessed and created, per APPNOTE.

## What the corpus holds

I measured 118 zips from my corpus. The split:

| Extra field present | Zips |
|---|---|
| 0x5455 only | 55 |
| NTFS 0x000a only | 19 |
| Neither (DOS time only) | 44 |
| Both | 0 |

Those 44 with neither are worth a pause. For those zips the DOS time is all there is, with all the limits above.

The writers fall into a few shapes (my measurement, grouped by the bytes of the field):

| Shape | Seen in |
|---|---|
| 0x5455, 13 bytes, flags 0x07, three values | UFED and CLBX style zips |
| 0x5455, 17 bytes, flags 0x0f, four values | GrayKey style `files_full.zip`: MVS 2023, the Jess CTF, MVS 2025, MVS 2026 and others |
| NTFS 0x000a, central directory only | Magnet 2020 CTF iOS, Magnet 2021 CTF macOS, MVS 2026 MacBook Pro |

One more measured detail. In these zips the central directory copy of 0x5455 carries all of the values, not just the modification time. That goes beyond what the Info-ZIP spec describes.

## The CLBX surprise

Cellebrite publishes a spec for its CLBX format on GitHub ([cellebrite-labs/clbx](https://github.com/cellebrite-labs/clbx/blob/3fc10c5f626d75c3265bc745ef0e6ef67a4d6224/README.md), README v0.3.0). Credit to them for publishing it. The spec says the 0x5455 field holds modification, access and creation (birth) times. It also says a file called `metadata.msgpack` inside the zip is the complete and authoritative per-file stat record, with mtime, ctime, atime and btime in nanoseconds.

So I compared the two. I measured all 7 CLBX-0.3.1 zips in my corpus, including the Cellebrite CTF 2023 images for Felix, Otto and Abe.

What I found: on every file I sampled, all three 0x5455 slots hold the same value. And that value equals the **access time** from `metadata.msgpack`. Not the modification time. On the iphone11_ios17 image, for example, 1,671 of 1,671 resolvable files where mtime and atime differ had the zip field match atime.

That means any tool that reads the zip extra field on these CLBX zips will show the access time in the Modified column and in the Created column. The decoding is correct. The value just does not mean what the label says.

A side note for anyone parsing `metadata.msgpack` yourself. The spec does not say how a missing time is written. On the Cellebrite CTF Felix iOS 17 image (546,633 records), 8,993 mtimes and 10,030 atimes hold INT64_MAX nanoseconds, which would be a date in the year 2262. Across the 7 CLBX zips, no time field holds INT64_MIN. Do not render either extreme as a date. That image also has 9,772 mtimes after the year 2100 that are not INT64_MAX. I report those as stored. I do not know why they are there.

The lesson I keep relearning: 7-Zip, zipinfo, my 2024 script and the new LEAPP code all agreed on the 0x5455 values. Four decoders agreeing proves the decoding. It says nothing about the meaning. To check meaning you need a second record of the same fact. Here that second record was sitting in the same zip.

## The four-value puzzle

The GrayKey style zips set flag bit 0x08 and store four values. Info-ZIP defines only three bits. Bit 0x08 is not in the spec. So what is the fourth value, and which slot is birth?

I found no Magnet or GrayKey vendor document that gives the slot order. Magnet's blog post ["Understanding iOS Time Stamps"](https://www.magnetforensics.com/resources/understanding-ios-time-stamps/) (published March 2020, per the page metadata) is the closest thing. It lists the four times iOS `stat` shows (Access, Modify, Change, Birth), says GrayKey zips retain the time stamps, and says birth is synonymous with created. Its testing also showed that changing a file's permissions updated only the Change time, which is what a change time should do. It does not say which slot in the zip is which.

The best written source I found is [gkls](https://github.com/slo-sleuth/gkls/blob/1b8690309c0270ae6f74c83df89ebe976fb83b6b/README.md#L140-L152) by slo-sleuth on GitHub. Its README documents the order as Mtime, Atime, Ctime ("file metadata changed time") and Btime ("file creation (birth) time"). It also notes that commercial tools showed only three of the four dates. [FFS-Explorer](https://github.com/KlasScripts/FFS-Explorer) by KlasScripts uses the same layout. That is a researcher's finding, not a vendor statement. So I went looking for a way to check it.

## How CTF writeups solved it

This is where the community comes in. Folks who write up CTF solutions post screenshots of what their tools displayed. I have copies of the same CTF images. So I could take a file from a writeup, read its four slots myself, and see which slot the tool put in which column.

Here is what that gave me. Each row is a tool's display, taken from a public writeup, matched to my own read of the same file:

| Tool column | Matches slot | Writeup | File and values (UTC) |
|---|---|---|---|
| AXIOM Modified | s1 | [stark4n6, MVS 2023](https://www.stark4n6.com/2023/03/magnet-virtual-summit-2023-ctf-ios-16.html) | IMG_0034.HEIC: slots 15:36:27, 15:36:26, 15:36:28, 15:36:26. AXIOM showed Modified 15:36:27 |
| AXIOM Accessed | s2 | [Doug Metz (Baker Street Forensics), MVS 2025](https://bakerstreetforensics.com/2025/02/24/exploring-magnet-virtual-summit-2025-ctf-challenges-ios/) | Wallpaper PDF: slots 01:54:20, 01:56:23, 02:01:28, 01:54:20. AXIOM showed Accessed 1:56:23 |
| AXIOM Created | s4 | [Doug Metz (Baker Street Forensics), Jess CTF](https://bakerstreetforensics.com/2022/07/28/magnet-2022-ctf-ios15/), AXIOM 6.4 | IMG_0002.HEIC: slots 14:09:00, 14:09:00, 2022-01-21 22:27:34, 14:08:59. AXIOM showed Created 2:08:59 PM |
| Forensic Explorer 5.6.8 Created | s3 | [GetData Forensics walkthrough, MVS 2023](https://download.getdata.com/support/documents/ctf/Magnet%20Virtual%20Summit%202023%20CTF%20-%20iOS%2016.pdf) | IMG_0068.HEIC: slots 14:57:04, 14:57:04, 15:07:04, 14:57:03. Forensic Explorer showed Created 3:07:04 PM, Modified and Accessed 2:57:04 PM |

A few honest caveats on that table:

- For the Jess CTF row, Photos.sqlite ZDATECREATED falls in the same second as s4. So AXIOM could have taken Created from the database instead of the zip. [Hexordia's MVS 2026 writeup](https://www.hexordia.com/blog/magnet-virtual-summit-2026-ctf-ios-questions) helps here: a Zangi snapshot in it, matched to my copy, rules out s2 as AXIOM's Created.
- The Forensic Explorer screenshot in the GetData walkthrough (page 26) shows no time zone. Its three values line up with the slots read as UTC. That screenshot shows no version either. The 5.6.8 comes from the title bar of another screenshot in the same walkthrough and case (page 23).
- Riya Chaudhari's [LinkedIn article](https://www.linkedin.com/pulse/hands-on-magnet-axiom-ctf-challenges-virtual-summit-2026-chaudhari-fmslf/) on MVS 2026 has an AXIOM 9.10 screenshot of the same AppStore icon from the top of this post. AXIOM showed 13:44:43 for Created, Accessed and Modified. In my copy all four 0x5455 slots read 13:44:43 UTC, and the DOS time is 09:44:42. So AXIOM showed the extra field value in UTC, not the DOS time. The screenshot has no zone label. All four slots are equal on that file, so it does not help with slot order.

So AXIOM reads s4 as Created. Forensic Explorer, in that walkthrough, reads s3 as Created. Two tools, same kind of zip, different answers. That is a display mapping, measured. It still does not tell us which one the writer meant as birth.

## The EXIF decider

The photo itself answered that. IMG_0068.HEIC from MVS 2023 carries its own EXIF DateTimeOriginal: 2023-01-02 15:57:04.139 +01:00. That is 14:57:04 UTC.

Now look at the slots again: s1 14:57:04, s2 14:57:04, s3 15:07:04, s4 14:57:03.

A file cannot be born 10 minutes after the camera wrote it. So s3 is not birth. s4, about a second before the stored capture time, fits a file created as the photo was taken.

One file is one file, so I ran the whole population. I measured 802,194 four-value files (members with a 17-byte 0x5455 block, flags 0x0f) across four images and counted the cases that would break the gkls order:

| Check | MVS 2023 | Jess CTF | MVS 2026 | MVS 2025 |
|---|---|---|---|---|
| Four-value files | 338,592 | 66,635 | 294,934 | 102,033 |
| s3 earlier than s1 | 2 | 12 | 19 | 180 |
| s4 later than s1 | 3 | 0 | 0 | 6,523 |
| s3 earlier than s4 | 5 | 0 | 0 | 9 |

The 6,523 files with s4 later than s1 are on the MVS 2025 image. I have not established the cause. It is consistent with files that were copied or restored with their modification time kept, but that is a reading, not a finding.

My conclusion: s1 is modified, s2 is accessed, s3 is changed (metadata change), s4 is born (created). I have high confidence in the display mapping because I measured it against tool screenshots. I have moderate to high confidence in what the writer meant, from gkls, the EXIF check and the population counts. There is no vendor statement behind it. If someone at Magnet can confirm or correct the slot order, I would love to hear it.

## What changed in the tools

The LEAPP cores now read these fields. A first round of PRs on 23 October taught the zip reader to read the NTFS and 0x5455 fields: [ALEAPP #1766](https://github.com/abrignoni/ALEAPP/pull/1766), [iLEAPP #2553](https://github.com/abrignoni/iLEAPP/pull/2553), [RLEAPP #613](https://github.com/abrignoni/RLEAPP/pull/613), [VLEAPP #387](https://github.com/abrignoni/VLEAPP/pull/387) and [DLEAPP #698](https://github.com/abrignoni/DLEAPP/pull/698). It prefers NTFS 0x000a, then 0x5455, then the DOS time.

The findings above then went into a second round, merged the same day: [ALEAPP #1769](https://github.com/abrignoni/ALEAPP/pull/1769), [iLEAPP #2560](https://github.com/abrignoni/iLEAPP/pull/2560), [RLEAPP #615](https://github.com/abrignoni/RLEAPP/pull/615), [VLEAPP #389](https://github.com/abrignoni/VLEAPP/pull/389) and [DLEAPP #700](https://github.com/abrignoni/DLEAPP/pull/700).

- On four-value 0x5455 blocks, created comes from s4, never s3. Modified stays s1. Three-value blocks keep the Info-ZIP layout.
- CLBX zips get their times from `metadata.msgpack` (btime as created, mtime as modified, to the nanosecond). Their 0x5455 values are not used. Both INT64 extremes are treated as no time.
- This adds msgpack as a dependency. Without it, or when a file has no record, that file gets no recorded times, the log says so once per zip, and extraction carries on.

Before and after runs show the effect. On the MVS 2023 image, media created times moved earlier on 64 of 1,670 items, from s3 to s4. On a CLBX image (iphone11_ios17), created and updated times changed on 5,906 of 6,869 media items, with the same row counts. A three-value zip and an NTFS-field zip, used as controls, did not change. Credit to slo-sleuth, whose gkls documented the four-value layout.

My `extract_timestamps.py` got the same treatment in [Misc-Scripts #1](https://github.com/abrignoni/Misc-Scripts/pull/1). It labels the third value as change time and the fourth as birth. For CLBX zips it prints a note that the extra field holds the access time, and prints the `metadata.msgpack` times when the msgpack package is installed.

## Takeaways

- **Know which writer produced the zip.** UFED, CLBX, GrayKey style and NTFS-field zips store different things in similar-looking places.
- **Do not trust DOS times.** No zone, 2-second resolution, and the writer's clock. The same phone gave me one hour of difference between two releases.
- **Do not assume a tool's "Created" is birth.** Two tools showed two different slots as Created for the same kind of zip.
- **For CLBX, use `metadata.msgpack`.** In the zips I tested, the zip field holds the access time in all three slots.
- **Verify against a second record.** EXIF, app databases and vendor sidecars. Agreement between decoders is not that second record.
- **Credit the writeups.** This work was only possible because stark4n6, Doug Metz, Hexordia, Riya Chaudhari, GetData Forensics and others took the time to publish their screenshots and answers. Thank you.

If you have a zip from a writer I did not cover, or a vendor document that settles the four-value order, send it my way. Happy to be corrected.
