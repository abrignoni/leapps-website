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

The picture may show application content. It may show a launch screen. It may be a downscaled copy. The application may have deliberately covered sensitive information before iOS captured it. The file has a modified time. A database has a creation time and another field named `lastUsedDate`. None of those facts gives us permission to write a story the evidence did not record.<sup><a href="#note-1">[1]</a></sup><sup><a href="#note-3">[3]</a></sup><sup><a href="#note-5">[5]</a></sup>

Still, this is excellent evidence when we handle it carefully.

I first wrote about [iOS snapshots and KTX files in 2019](https://abrignoni.blogspot.com/2019/09/ios-snapshots-triage-parser-working.html), building on [Geraldine Blay's snapshot research](https://gforce4n6.blogspot.com/2019/09/a-quick-look-into-ios-snapshots.html). The workflow found KTX images, converted them, and used `applicationState.db` to add application context and timestamps.<sup><a href="#note-2">[2]</a></sup>

Seven years later, the artifact is still here. iOS has changed where and how it organizes the files, scene-based applications have complicated the paths, and iLEAPP has gained a much better way to put the pieces together.<sup><a href="#note-2">[2]</a></sup><sup><a href="#note-3">[3]</a></sup>

So we went back.

**Short version:** current iLEAPP source now converts KTX snapshots into correctly identified PNG files that display inside the report, joins each image to its `XBApplicationSnapshotManifest` record, reports the bundle, scene, identifier, variant, and three separately labeled time fields, and carries much stronger interpretation warnings.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-4">[4]</a></sup>

**Long version:** the labels matter as much as the parser.

## What iOS is taking a picture for

Apple documents that immediately after an application moves to the background, the system captures its window and uses the snapshot to represent the application in the task switcher.<sup><a href="#note-1">[1]</a></sup>

That gives us the first important interpretation rule:

> An app snapshot is a cached representation prepared for the operating system. It is not automatically a photograph of what a human was looking at.<sup><a href="#note-1">[1]</a></sup>

Apple tells developers that they can alter the view hierarchy before suspension, including covering the application contents or presenting a lock or authentication screen.<sup><a href="#note-1">[1]</a></sup> Our test data also shows why the image itself must control the interpretation: a launch/default presentation may appear where we hoped to find live content.<sup><a href="#note-7">[7]</a></sup>

Here is a real example from the public iOS 12.4 CTF test image used in the validation:<sup><a href="#note-7">[7]</a></sup>

<img src="https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-08-10-ios-app-snapshots-seven-years-later/uber-default-snapshot.webp" alt="A black iOS Uber launch snapshot with a centered white Uber logo, illustrating that an app snapshot can be a generated default screen rather than evidence of viewed content." style="display:block;width:min(360px,100%);height:auto;margin:1.5rem auto;">

That is a valid snapshot associated with Uber. It does not show a trip, a map, an account, or any other user content. The honest interpretation is the useful one: the snapshot existed, the manifest associated it with the application, and the image itself is a launch/default presentation.<sup><a href="#note-7">[7]</a></sup>

## Where the evidence lives now

The 2019 workflow commonly found snapshots in an application's container under paths involving `Library/Caches/Snapshots`.<sup><a href="#note-2">[2]</a></sup> The current iLEAPP artifact also covers SplashBoard paths such as:<sup><a href="#note-3">[3]</a></sup>

```text
/private/var/mobile/Library/SplashBoard/Snapshots/<bundle id>/...

/private/var/mobile/Containers/Data/Application/<UUID>/
    Library/SplashBoard/Snapshots/<snapshot group>/...
```

Inside those locations, the updated artifact accepts JPEG images and KTX containers holding ASTC-compressed image data. It also identifies images under a `downscaled` directory as downscaled variants.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-7">[7]</a></sup>

The corresponding metadata is parsed separately from:<sup><a href="#note-2">[2]</a></sup><sup><a href="#note-4">[4]</a></sup>

```text
/private/var/mobile/Library/FrontBoard/applicationState.db
/private/var/mobile/Library/FrontBoard/applicationState.db-wal
/private/var/mobile/Library/FrontBoard/applicationState.db-shm
```

In `applicationState.db`, iLEAPP parses serialized snapshot-manifest data stored under the `XBApplicationSnapshotManifest` key. The decoded records can provide the bundle identifier, snapshot group, image identifier, relative path, orientation, scale, creation date, last-used date, and other context.<sup><a href="#note-4">[4]</a></sup><sup><a href="#note-5">[5]</a></sup>

The image and the manifest are two halves of one answer.

![Diagram showing iLEAPP joining an iOS KTX or JPEG snapshot with applicationState database metadata to produce a PNG preview with bundle, scene, variant, and separately labeled timestamps.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-08-10-ios-app-snapshots-seven-years-later/snapshot-evidence-map.webp)

## Scene paths changed the naming game

Older snapshot folders often made the application name easy to read. Scene-based paths handled by the current artifact can look like this:<sup><a href="#note-2">[2]</a></sup><sup><a href="#note-3">[3]</a></sup>

```text
sceneID:com.example.app-default

sceneID:com.example.app-19F2E62F-A756-4397-9E92-2DD765BDB306
```

iLEAPP treats the full scene directory as the snapshot group, while the manifest supplies the bundle identifier. A trailing `default` label or UUID is therefore kept with the group rather than appended to the bundle ID.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-10">[10]</a></sup>

The older iLEAPP logic trimmed the path at the first hyphen. That could truncate a legitimate bundle identifier because Apple permits hyphens in `CFBundleIdentifier`; it could also leave `sceneID` text where an examiner expected a bundle ID.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-6">[6]</a></sup>

The updated artifact reads the directory structure first and then lets the manifest confirm the bundle identifier. It also reports the full snapshot group separately. We keep both pieces instead of forcing two different ideas into one column.<sup><a href="#note-3">[3]</a></sup>

That means a report can now tell you:<sup><a href="#note-3">[3]</a></sup>

- Bundle ID: `com.example.app`
- Snapshot Group: `sceneID:com.example.app-<scene UUID>`
- Snapshot Identifier: the image UUID
- Variant: `default` or `downscaled`

Small change on the screen. Much cleaner evidence underneath.

## KTX conversion had a browser problem

iLEAPP was already converting supported KTX image data into PNG bytes. During this revisit, we found an end-to-end problem hiding after the conversion: the media could retain its source `.ktx` extension—or even inherit a bundle-like suffix such as `.Maps` or `.Docs`—after becoming a PNG.<sup><a href="#note-3">[3]</a></sup>

The conversion worked, but the wrong media identity meant the HTML report offered a link instead of displaying the snapshot.<sup><a href="#note-3">[3]</a></sup>

That is now fixed. Converted images are checked into the report as `image/png` with a `.png` filename. JPEG snapshots keep the correct JPEG identity.<sup><a href="#note-3">[3]</a></sup> All 558 displayable KTX snapshots in the three real-data tests rendered as images in the finished reports.<sup><a href="#note-7">[7]</a></sup>

Forensic tooling is full of bugs like this. The parser can be right, the bytes can be right, and the last six inches to the examiner can still be wrong. Test the finished report, not only the function that produced it.

## The three clocks

The updated report places three time fields next to the same image. They are not interchangeable.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-4">[4]</a></sup>

### File Modified Date

This is source-file metadata preserved by the extraction and media pipeline.<sup><a href="#note-3">[3]</a></sup> On ZIP-based acquisitions, be careful about the timestamp source your tool is showing. ZIP's standard modified date and time fields use MS-DOS format, which does not specify a time zone; the commonly used `0x5455` extended timestamp stores Unix time in UTC. A four-hour difference in an Eastern Daylight Time workflow can therefore be a time-zone presentation issue rather than a four-hour forensic event.<sup><a href="#note-8">[8]</a></sup>

### Manifest Creation Date

This is the `creationDate` stored in the corresponding snapshot record decoded from the `XBApplicationSnapshotManifest` data.<sup><a href="#note-4">[4]</a></sup><sup><a href="#note-5">[5]</a></sup>

In our iOS 18.7.8 and iOS 26.5.2 extractions, the ZIP `0x5455` UTC modified time was available for 490 displayable snapshot files. Every one agreed with its manifest creation time within one second. The combined median absolute difference was about 0.37 seconds.<sup><a href="#note-7">[7]</a></sup><sup><a href="#note-8">[8]</a></sup>

That is strong empirical support that these two fields describe the same snapshot-creation operation in those tested datasets, at the precision preserved by the extraction ZIP.<sup><a href="#note-7">[7]</a></sup>

It is not a universal guarantee. Validate the operating-system version, acquisition format, and tool chain in front of you.

### Manifest Last Used Date

This is where restraint earns its keep.

Runtime-derived SplashBoard headers expose `creationDate` and `lastUsedDate` on `XBApplicationSnapshot`, including a `setLastUsedDate:` method. That gives us a published source for the field name and shows that the latter property can be set. It does not document which internal event updates it.<sup><a href="#note-5">[5]</a></sup>

Across our three test images, `lastUsedDate` was sparse:<sup><a href="#note-4">[4]</a></sup><sup><a href="#note-7">[7]</a></sup>

- 64 of 257 manifest records on iOS 12.4
- 31 of 362 manifest records on iOS 18.7.8
- 20 of 284 manifest records on iOS 26.5.2<sup><a href="#note-7">[7]</a></sup>

When present, it was later than `creationDate` by intervals ranging from seconds to much longer in the tested data. That behavior is consistent with a settable property on the snapshot object being updated after creation, but the public header does not identify the triggering event. It does not prove the application was foregrounded at that moment. It does not prove the user saw the image. It does not prove a tap.<sup><a href="#note-5">[5]</a></sup><sup><a href="#note-7">[7]</a></sup>

iLEAPP therefore reports the value by its stored name and documents the limitation.<sup><a href="#note-4">[4]</a></sup> Corroborate it with Biome, KnowledgeC, Usage/Application State, Unified Logs, application data, or whatever else the case provides.

Mystery solved halfway is still progress. We know what Apple calls the field. We do not pretend Apple documented its forensic meaning.

## The WAL is not optional decoration

One of the best findings from the real-data test was not in a KTX file at all.

When we parsed the iOS 26 `applicationState.db` file without its sidecars, only 279 of the current image filenames matched a manifest record. When iLEAPP processed the database together with `applicationState.db-wal` and `applicationState.db-shm`, all 283 displayable images matched.<sup><a href="#note-7">[7]</a></sup>

Four matching records were available only when the write-ahead log was included.<sup><a href="#note-7">[7]</a></sup>

That is why the updated App Snapshots artifact requests `applicationState.db*`, not only the bare database.<sup><a href="#note-3">[3]</a></sup> Acquire the set. Keep the set together. SQLite documents that committed changes can remain in the WAL and warns that separating a database from its WAL can lose committed transactions.<sup><a href="#note-9">[9]</a></sup>

## Real data, three iOS generations

We tested the updated source through complete iLEAPP runs against full-file-system images from iOS 12.4, iOS 18.7.8, and iOS 26.5.2.<sup><a href="#note-7">[7]</a></sup>

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

<sup><a href="#note-7">[7]</a></sup>

Why do the manifest and image counts differ? The test establishes that the two populations do not map one-to-one, but the counts alone do not establish one reason for every unmatched record. An extraction may omit related files, and iLEAPP skips KTX files smaller than 2,500 bytes under the artifact's established threshold. Report the populations separately rather than assuming every manifest row must have a picture.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-7">[7]</a></sup>

The real-data runs covered default and downscaled variants, old and scene-based directory layouts, the database sidecars, KTX-to-PNG display in HTML, and the LAVA output path.<sup><a href="#note-7">[7]</a></sup> Focused regression fixtures separately covered bundle identifiers containing hyphens, scene UUID suffixes, downscaled paths, and duplicate manifest filenames.<sup><a href="#note-10">[10]</a></sup>

We added regression tests for the path and manifest-join logic too.<sup><a href="#note-10">[10]</a></sup> Real data tells us the code works today.<sup><a href="#note-7">[7]</a></sup> Focused tests help keep tomorrow's cleanup from quietly putting `sceneID` back in the bundle column.

## Working it in iLEAPP and LAVA

The update was merged into current iLEAPP source after the latest packaged release, so it is intended for the next release.<sup><a href="#note-11">[11]</a></sup> The merged artifact names and fields support this workflow:<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-4">[4]</a></sup>

1. Process the complete iOS full-file-system extraction with [iLEAPP](https://www.leapps.org/releases#section-ileapp).
2. Open **App Snapshots** to review the image and its joined manifest context in one row.
3. Compare **File Modified Date** and **Manifest Creation Date**. Record the source and time-zone handling if they differ.
4. Treat **Manifest Last Used Date** as a stored SplashBoard field requiring corroboration, not as a synonym for app use.
5. Use **Bundle ID**, **Snapshot Group**, **Snapshot Identifier**, and **Variant** to distinguish related images.
6. Open **Application Snapshot** when you need manifest records whose image is no longer available.
7. Correlate with the application, system timelines, and other device-usage artifacts.

The App Snapshots artifact emits the joined fields and media to LAVA as well as the standard reports.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-12">[12]</a></sup> In LAVA, filter by bundle, group, time range, or variant, then open the media for the rows that matter.<sup><a href="#note-12">[12]</a></sup> A folder with hundreds of UUID-named KTX files becomes a searchable set of application evidence.

## What changed since 2019

The original research remains the foundation. KTX still matters. `applicationState.db` still matters. The warning that timestamps need interpretation matters more than ever.<sup><a href="#note-2">[2]</a></sup><sup><a href="#note-4">[4]</a></sup>

What changed is the workflow and the context:

- Snapshot storage expanded from the older cache layouts into SplashBoard and scene-based groups.<sup><a href="#note-2">[2]</a></sup><sup><a href="#note-3">[3]</a></sup>
- The application name is no longer safely derived by chopping a folder name at the first hyphen.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-6">[6]</a></sup>
- iLEAPP converts KTX natively; no Automator workflow is required.<sup><a href="#note-2">[2]</a></sup><sup><a href="#note-3">[3]</a></sup>
- Converted images now reach the report with the correct PNG identity.<sup><a href="#note-3">[3]</a></sup>
- The image and `XBApplicationSnapshotManifest` are joined into one report row.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-4">[4]</a></sup>
- Bundle, scene, identifier, and default/downscaled variant are reported separately.<sup><a href="#note-3">[3]</a></sup>
- File modified, manifest creation, and manifest last-used times are labeled by source.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-5">[5]</a></sup>
- Interpretation notes now distinguish snapshot creation from foreground use and human viewing.<sup><a href="#note-3">[3]</a></sup><sup><a href="#note-4">[4]</a></sup>
- Real data from iOS 12 through iOS 26 backs the implementation.<sup><a href="#note-7">[7]</a></sup>

That is why I enjoy revisiting old artifacts. The old work does not become worthless when the operating system changes. It becomes the map that tells us where to look next.

Sometimes we find more data. Sometimes we fix a display bug. Sometimes the most important update is replacing a confident sentence with a careful one.

All three make the tool better.

## Thank you

Thank you to [Geraldine Blay](https://gforce4n6.blogspot.com/2019/09/a-quick-look-into-ios-snapshots.html) for the research that helped establish the forensic value and interpretation challenges of iOS snapshots; to [Yogesh Khatri](https://www.swiftforensics.com/) for bringing snapshot parsing and KTX conversion into iLEAPP; and to [mxkrt](https://github.com/mxkrt) for the `XBApplicationSnapshotManifest` work that made the database side of this revisit possible.<sup><a href="#note-2">[2]</a></sup><sup><a href="#note-13">[13]</a></sup>

Good open-source work compounds. One person documents the files. Another writes the parser. Someone else adds the missing metadata. Years later, we can put those pieces back on the bench, test them against three generations of iOS, and make the whole answer better for everybody.

Free tools. Real data. Careful conclusions. Go look at the pictures—and read the labels beside them.

## Endnotes

<ol class="blog-endnotes">
<li id="note-1">Apple, <a href="https://developer.apple.com/library/archive/qa/qa1838/_index.html">Technical Q&amp;A QA1838: Preventing Sensitive Information From Appearing in the Task Switcher</a>. Apple states that the system captures the application window immediately after the app moves to the background, uses it in the task switcher, and allows the app to cover or replace sensitive content before capture.</li>
<li id="note-2">Alexis Brignoni, <a href="https://abrignoni.blogspot.com/2019/09/ios-snapshots-triage-parser-working.html">iOS Snapshots Triage Parser &amp; working with KTX files</a> (2019); Geraldine Blay, <a href="https://gforce4n6.blogspot.com/2019/09/a-quick-look-into-ios-snapshots.html">A “Quick Look” into iOS Snapshots</a> (2019). These posts document the older cache paths, KTX-to-PNG Automator workflow, nested binary-plist data in <code>applicationState.db</code>, and the original timestamp caveats.</li>
<li id="note-3">iLEAPP, <a href="https://github.com/abrignoni/iLEAPP/blob/295e60a31c680fb95cb372e1b1b6b127de34cf42/scripts/artifacts/appSnapshots.py"><code>appSnapshots.py</code> at merged commit <code>295e60a</code></a>, and <a href="https://github.com/abrignoni/iLEAPP/pull/1888">PR #1888</a>. The implementation defines the covered paths, 2,500-byte KTX threshold, ASTC conversion, bundle/group parsing, manifest join, variant labels, media types, output columns, and interpretation notes.</li>
<li id="note-4">iLEAPP, <a href="https://github.com/abrignoni/iLEAPP/blob/295e60a31c680fb95cb372e1b1b6b127de34cf42/scripts/artifacts/applicationStateDB.py"><code>applicationStateDB.py</code> at merged commit <code>295e60a</code></a>. The parser queries the <code>XBApplicationSnapshotManifest</code> value in <code>applicationState.db</code>, decodes its nested data, exposes the snapshot fields, and documents conservative timestamp semantics.</li>
<li id="note-5">Runtime-derived SplashBoard interfaces: <a href="https://github.com/nst/iOS-Runtime-Headers/blob/master/PrivateFrameworks/SplashBoard.framework/XBApplicationSnapshot.h"><code>XBApplicationSnapshot.h</code></a> exposes <code>creationDate</code>, <code>lastUsedDate</code>, <code>setLastUsedDate:</code>, identifiers, paths, image scale, orientation, and related properties; <a href="https://github.com/nst/iOS-Runtime-Headers/blob/master/PrivateFrameworks/SplashBoard.framework/XBApplicationSnapshotManifest.h"><code>XBApplicationSnapshotManifest.h</code></a> exposes the manifest’s bundle identifier and snapshot-group methods. These are runtime-derived private-framework headers, not Apple documentation of forensic meaning.</li>
<li id="note-6">Apple, <a href="https://developer.apple.com/documentation/BundleResources/Information-Property-List/CFBundleIdentifier"><code>CFBundleIdentifier</code></a>. Apple permits alphanumeric characters, hyphens, and periods in bundle identifiers.</li>
<li id="note-7">LEAPPs real-data validation, summarized publicly in <a href="https://github.com/abrignoni/iLEAPP/pull/1888">iLEAPP PR #1888</a> and independently rerun for this accuracy review on August 10, 2026. Complete iLEAPP runs used full-file-system images from iOS 12.4, 18.7.8, and 26.5.2. They produced 68, 207, and 283 displayable snapshots respectively, with every image joined to a manifest record and all 558 KTX conversions rendered as PNG. A fresh parse of the iOS 18 and iOS 26 acquisition ZIPs found 490 matching <code>0x5455</code> UTC modified timestamps; all differed from manifest <code>creationDate</code> by less than one second (combined median absolute difference 0.3674965 seconds; maximum 0.938875 seconds). The iOS 12.4 image is the public 2020 CTF iOS dataset; the later validation images are not publicly distributed.</li>
<li id="note-8"><a href="https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT">PKWARE ZIP File Format Specification</a>, sections 4.4.6 and 4.6.1, defines the standard MS-DOS date/time fields and lists <code>0x5455</code> as the extended timestamp field. The <a href="https://commons.apache.org/proper/commons-compress/apidocs/org/apache/commons/compress/archivers/zip/X5455_ExtendedTimestamp.html">Apache Commons Compress <code>X5455_ExtendedTimestamp</code> documentation</a>, based on Info-ZIP’s field definition, specifies 32-bit Unix timestamps in UTC/GMT. The base ZIP fields do not identify a time zone.</li>
<li id="note-9">SQLite, <a href="https://sqlite.org/wal.html">Write-Ahead Logging</a>. SQLite explains that committed changes may exist only in the separate WAL until checkpointing and that the WAL is part of the database’s persistent state and should remain with the database when copied.</li>
<li id="note-10">iLEAPP, <a href="https://github.com/abrignoni/iLEAPP/blob/295e60a31c680fb95cb372e1b1b6b127de34cf42/admin/test/scripts/test_app_snapshots.py">App Snapshots regression tests at merged commit <code>295e60a</code></a>. The fixtures cover scene paths, UUID suffixes, hyphenated bundle IDs, downscaled groups, and duplicate manifest-filename matching.</li>
<li id="note-11"><a href="https://github.com/abrignoni/iLEAPP/pull/1888">iLEAPP PR #1888</a> merged the update on August 7, 2026. At publication, the latest packaged iLEAPP release was <a href="https://github.com/abrignoni/iLEAPP/releases/tag/v2026.2.1">v2026.2.1</a>, published July 27, 2026, so the merged snapshot changes were newer than the packaged release.</li>
<li id="note-12">LEAPPs, <a href="https://www.leapps.org/releases#section-lava">LAVA releases</a>. The merged App Snapshots artifact declares standard output, which includes LAVA output, and checks converted snapshots into the shared media pipeline; see <a href="https://github.com/abrignoni/iLEAPP/blob/295e60a31c680fb95cb372e1b1b6b127de34cf42/scripts/artifacts/appSnapshots.py"><code>appSnapshots.py</code></a>.</li>
<li id="note-13">Contributor attribution is recorded in the artifact metadata and history: <a href="https://github.com/abrignoni/iLEAPP/blob/295e60a31c680fb95cb372e1b1b6b127de34cf42/scripts/artifacts/appSnapshots.py"><code>appSnapshots.py</code></a> credits <code>@ydkhatri</code> and Alexis Brignoni; <a href="https://github.com/abrignoni/iLEAPP/blob/295e60a31c680fb95cb372e1b1b6b127de34cf42/scripts/artifacts/applicationStateDB.py"><code>applicationStateDB.py</code></a> credits <code>@mxkrt</code> and Alexis Brignoni; the foundational research is documented in the two 2019 posts in note 2.</li>
</ol>
