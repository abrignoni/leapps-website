---
title: iOS App Snapshots, Seven Years Later: The Screen, the Scene, and Three Clocks
date: 2026-08-10
author: Alexis Brignoni
tags: [iLEAPP, iOS, App Snapshots, KTX, SplashBoard, DFIR]
excerpt: iOS still keeps app-switcher snapshots, but the storage moved, scenes arrived, and that mysterious second timestamp finally has a name—not a license to overclaim. We went back to the files, joined the picture to its manifest, and tested the result from iOS 12 through iOS 26.
---

# iOS App Snapshots, Seven Years Later: The Screen, the Scene, and Three Clocks

An iPhone can leave you a picture of an application screen.

That sounds wonderfully simple. It is not.

The picture may show application content. It may show a launch screen. It may be a downscaled copy. The application may have deliberately covered sensitive information before iOS captured it. The file has a modified time. A database has a creation time and another field named `lastUsedDate`. None of those facts gives us permission to write a story the evidence did not record.

Still, this is excellent evidence when we handle it carefully.

I first wrote about [iOS snapshots and KTX files in 2019](https://abrignoni.blogspot.com/2019/09/ios-snapshots-triage-parser-working.html), building on [Geraldine Blay's snapshot research](https://gforce4n6.blogspot.com/2019/09/a-quick-look-into-ios-snapshots.html). The workflow found KTX images, converted them, and used `applicationState.db` to add application context and timestamps.

Seven years later, the artifact is still here. iOS has changed where and how it organizes the files, scene-based applications have complicated the paths, and iLEAPP has gained a much better way to put the pieces together.

So we went back.

**Short version:** current iLEAPP source now converts KTX snapshots into correctly identified PNG files that display inside the report, joins each image to its `XBApplicationSnapshotManifest` record, reports the bundle, scene, identifier, variant, and three separately labeled time fields, and carries much stronger interpretation warnings.

**Long version:** the labels matter as much as the parser.

## What iOS is taking a picture for

Apple's [UIKit background guidance](https://developer.apple.com/documentation/uikit/preparing-your-ui-to-run-in-the-background) explains that the system takes a snapshot of an application's user interface after it enters the background. iOS uses that image to represent the application in places such as the app switcher and to make the return to the foreground look smooth.

That gives us the first important interpretation rule:

> An app snapshot is a cached representation prepared for the operating system. It is not automatically a photograph of what a human was looking at.

Apple also tells developers to remove passwords and other sensitive information before background capture. An application can cover its interface, replace it, blur it, or show a different view. A launch or default image may appear where we hoped to find live content.

Here is a real example from our iOS 12 test image:

<img src="https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-08-10-ios-app-snapshots-seven-years-later/uber-default-snapshot.webp" alt="A black iOS Uber launch snapshot with a centered white Uber logo, illustrating that an app snapshot can be a generated default screen rather than evidence of viewed content." style="display:block;width:min(360px,100%);height:auto;margin:1.5rem auto;">

That is a valid snapshot associated with Uber. It does not show a trip, a map, an account, or any other user content. The honest interpretation is the useful one: the snapshot existed, iOS associated it with the application, and the image itself is a launch/default presentation.

## Where the evidence lives now

The 2019 workflow commonly found snapshots in an application's container under paths involving `Library/Caches/Snapshots`. Modern devices also use SplashBoard paths such as:

```text
/private/var/mobile/Library/SplashBoard/Snapshots/<bundle id>/...

/private/var/mobile/Containers/Data/Application/<UUID>/
    Library/SplashBoard/Snapshots/<snapshot group>/...
```

Inside those locations you may find JPEG images or KTX containers holding ASTC-compressed image data. You may also find a `downscaled` directory with smaller versions of the same general snapshot material.

The metadata lives separately:

```text
/private/var/mobile/Library/FrontBoard/applicationState.db
/private/var/mobile/Library/FrontBoard/applicationState.db-wal
/private/var/mobile/Library/FrontBoard/applicationState.db-shm
```

The database stores serialized `XBApplicationSnapshotManifest` objects. Those records can provide the bundle identifier, snapshot group, image identifier, relative path, orientation, scale, creation date, last-used date, and other context.

The image and the manifest are two halves of one answer.

![Diagram showing iLEAPP joining an iOS KTX or JPEG snapshot with applicationState database metadata to produce a PNG preview with bundle, scene, variant, and separately labeled timestamps.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-08-10-ios-app-snapshots-seven-years-later/snapshot-evidence-map.webp)

## Scene paths changed the naming game

Older snapshot folders often made the application name easy to read. Scene-based paths can look like this:

```text
sceneID:com.example.app-default

sceneID:com.example.app-19F2E62F-A756-4397-9E92-2DD765BDB306
```

That suffix describes a scene or snapshot group. It is not part of the bundle identifier.

The older iLEAPP logic trimmed the path at the first hyphen. That worked until an application identifier legitimately contained one, and it could also leave `sceneID` text where an examiner expected a bundle ID.

The updated artifact reads the directory structure first and then lets the manifest confirm the bundle identifier. It also reports the full snapshot group separately. We keep both pieces instead of forcing two different ideas into one column.

That means a report can now tell you:

- Bundle ID: `com.example.app`
- Snapshot Group: `sceneID:com.example.app-<scene UUID>`
- Snapshot Identifier: the image UUID
- Variant: `default` or `downscaled`

Small change on the screen. Much cleaner evidence underneath.

## KTX conversion had a browser problem

iLEAPP was already converting supported KTX image data into PNG bytes. During this revisit, we found an end-to-end problem hiding after the conversion: the media could retain its source `.ktx` extension—or even inherit a bundle-like suffix such as `.Maps` or `.Docs`—after becoming a PNG.

The conversion worked. The browser still saw a file it did not recognize as an image, so the report offered a link instead of displaying the snapshot.

That is now fixed. Converted images are checked into the report as `image/png` with a `.png` filename. JPEG snapshots keep the correct JPEG identity. All 558 displayable KTX snapshots in the three real-data tests rendered as images in the finished reports.

Forensic tooling is full of bugs like this. The parser can be right, the bytes can be right, and the last six inches to the examiner can still be wrong. Test the finished report, not only the function that produced it.

## The three clocks

The updated report places three time fields next to the same image. They are not interchangeable.

### File Modified Date

This is file-system metadata preserved by the extraction and media pipeline. On ZIP-based acquisitions, be careful about the timestamp source your tool is showing. A ZIP's ordinary date fields may be rendered as local time, while extended timestamp data can preserve UTC. A four-hour difference can be a time-zone presentation issue rather than a four-hour forensic event.

### Manifest Creation Date

This is the `creationDate` stored in the corresponding `XBApplicationSnapshotManifest` record.

In our iOS 18.7.8 and iOS 26.5.2 extractions, source modified time was available for 490 displayable snapshot files. Every one agreed with its manifest creation time within one second. The median absolute difference was about 0.36 seconds.

That is strong empirical support that these two fields describe the same snapshot-creation operation in those tested datasets, at the precision preserved by the extraction ZIP.

It is not a universal guarantee. Validate the operating-system version, acquisition format, and tool chain in front of you.

### Manifest Last Used Date

This is where restraint earns its keep.

Runtime-derived [SplashBoard headers expose `creationDate` and `lastUsedDate`](https://github.com/nst/iOS-Runtime-Headers/blob/master/PrivateFrameworks/SplashBoard.framework/XBApplicationSnapshot.h) on `XBApplicationSnapshot`. That gives us a published source for the field name. It does not tell us exactly which internal event updates it.

Across our three test images, `lastUsedDate` was sparse:

- 64 of 257 manifest records on iOS 12.4
- 31 of 362 manifest records on iOS 18.7.8
- 20 of 284 manifest records on iOS 26.5.2

When present, it could be later than `creationDate` by seconds, days, or much longer. That behavior is consistent with a property on the snapshot object being updated after creation. It does not prove the application was foregrounded at that moment. It does not prove the user saw the image. It does not prove a tap.

iLEAPP therefore reports the value by its stored name and says what we do not know. Corroborate it with Biome, KnowledgeC, Usage/Application State, Unified Logs, application data, or whatever else the case provides.

Mystery solved halfway is still progress. We know what Apple calls the field. We do not pretend Apple documented its forensic meaning.

## The WAL is not optional decoration

One of the best findings from the real-data test was not in a KTX file at all.

When we parsed the iOS 26 `applicationState.db` file without its sidecars, only 279 of the current image filenames matched a manifest record. When iLEAPP processed the database together with `applicationState.db-wal` and `applicationState.db-shm`, all 283 displayable images matched.

Recent records were still in the write-ahead log.

That is why the updated App Snapshots artifact requests `applicationState.db*`, not only the bare database. Acquire the set. Keep the set together. A clean query against an incomplete SQLite set can produce a cleanly incomplete answer.

## Real data, three iOS generations

We tested the updated source against full-file-system images from iOS 12.4, iOS 18.7.8, and iOS 26.5.2.

<div style="max-width:100%;overflow-x:auto;">
<table>
<thead>
<tr><th>iOS version</th><th>Manifest records</th><th>Records with <code>lastUsedDate</code></th><th>Displayable snapshots</th><th>Images joined to manifest</th></tr>
</thead>
<tbody>
<tr><td>12.4</td><td>257</td><td>64</td><td>68</td><td>68 / 68</td></tr>
<tr><td>18.7.8</td><td>362</td><td>31</td><td>207</td><td>207 / 207</td></tr>
<tr><td>26.5.2</td><td>284</td><td>20</td><td>283</td><td>283 / 283</td></tr>
</tbody>
</table>
</div>

Why do the manifest and image counts differ? A manifest can outlive an available image, an extraction may not preserve every related file, and iLEAPP skips very small KTX files under its established threshold when they do not provide a useful image. The counts describe related populations, not a requirement that every manifest row have a picture.

The test also covered both default and downscaled variants, old and scene-based directory layouts, bundle identifiers containing hyphens, the database sidecars, KTX-to-PNG display in HTML, and the LAVA output path.

We added regression tests for the path and manifest-join logic too. Real data tells us the code works today. Focused tests help keep tomorrow's cleanup from quietly putting `sceneID` back in the bundle column.

## Working it in iLEAPP and LAVA

The update is in current iLEAPP source and is intended for the next packaged release.

1. Process the complete iOS full-file-system extraction with [iLEAPP](https://www.leapps.org/releases#section-ileapp).
2. Open **App Snapshots** to review the image and its joined manifest context in one row.
3. Compare **File Modified Date** and **Manifest Creation Date**. Record the source and time-zone handling if they differ.
4. Treat **Manifest Last Used Date** as a stored SplashBoard field requiring corroboration, not as a synonym for app use.
5. Use **Bundle ID**, **Snapshot Group**, **Snapshot Identifier**, and **Variant** to distinguish related images.
6. Open **Application Snapshot** when you need manifest records whose image is no longer available.
7. Correlate with the application, system timelines, and other device-usage artifacts.

LAVA makes the joined fields particularly useful. Filter by bundle, group, time range, or variant, then open the media for the rows that matter. A folder with hundreds of UUID-named KTX files becomes a searchable set of application evidence.

## What changed since 2019

The original research remains the foundation. KTX still matters. `applicationState.db` still matters. The warning that timestamps need interpretation matters more than ever.

What changed is the workflow and the context:

- Snapshot storage expanded from the older cache layouts into SplashBoard and scene-based groups.
- The application name is no longer safely derived by chopping a folder name at the first hyphen.
- iLEAPP converts KTX natively; no Automator workflow is required.
- Converted images now reach the report with the correct PNG identity.
- The image and `XBApplicationSnapshotManifest` are joined into one report row.
- Bundle, scene, identifier, and default/downscaled variant are reported separately.
- File modified, manifest creation, and manifest last-used times are labeled by source.
- Interpretation notes now distinguish snapshot creation from foreground use and human viewing.
- Real data from iOS 12 through iOS 26 backs the implementation.

That is why I enjoy revisiting old artifacts. The old work does not become worthless when the operating system changes. It becomes the map that tells us where to look next.

Sometimes we find more data. Sometimes we fix a display bug. Sometimes the most important update is replacing a confident sentence with a careful one.

All three make the tool better.

## Thank you

Thank you to [Geraldine Blay](https://gforce4n6.blogspot.com/2019/09/a-quick-look-into-ios-snapshots.html) for the research that helped establish the forensic value and interpretation challenges of iOS snapshots; to [Yogesh Khatri](https://www.swiftforensics.com/) for bringing snapshot parsing and KTX conversion into iLEAPP; and to [mxkrt](https://github.com/mxkrt) for the `XBApplicationSnapshotManifest` work that made the database side of this revisit possible.

Good open-source work compounds. One person documents the files. Another writes the parser. Someone else adds the missing metadata. Years later, we can put those pieces back on the bench, test them against three generations of iOS, and make the whole answer better for everybody.

Free tools. Real data. Careful conclusions. Go look at the pictures—and read the labels beside them.
