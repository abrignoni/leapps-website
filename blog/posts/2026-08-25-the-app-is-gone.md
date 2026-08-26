---
title: The App Is Gone. The Story Isn't.
date: 2026-08-25
author: Alexis Brignoni
tags: [iLEAPP, iOS, Mobile Installation, Biome, app history, research]
excerpt: A current app list answers one question. Installation logs, App Store databases, Biome streams, and deletion records answer several others. We went back to an iOS workflow from 2018, tested it from iOS 12 through iOS 26, fixed what the real data exposed, and found a much better way to tell the story.
---

# The App Is Gone. The Story Isn't.

In 2018 I wanted a list of the applications installed on an iPhone and the directories that belonged to them.

Simple request, right?

It led me to `applicationState.db`. The database gave me bundle IDs, bundle paths, and sandbox paths. Then Phill Moore asked what happened to those records after an application was deleted, so I deleted three apps from a test phone and looked again.

The results were messy. One deleted app had an uninstall date. Another did not. Numeric keys I thought might be stable turned out to vary between devices. I published what I had, asked for help, and the community did what this community does.

Sarah Edwards corrected the query and pointed me toward the Mobile Installation logs. A week later I had a parser for them. Those three posts from 2018 and 2019 became part of the foundation for the installed-app artifacts we use today.<sup><a href="#note-1">[1]</a></sup>

Eight years later, the original question still matters. The answer is larger now.

**Short version:** `applicationState.db` is useful for mapping applications that currently have compatibility information to their bundle and data containers. It is not a complete installation history. Mobile Installation logs preserve lifecycle and container events for their retained window. App Store databases, Biome streams, and a deletion property list add other pieces. iLEAPP now keeps explicit installation outcomes separate from container-only activity, understands the Mobile Installation event forms we found from iOS 12 through iOS 26, decodes both App Install Biome layouts, and reports `UninstalledApplications.plist` when it exists.

**Long version:** an inventory and a stack of receipts are both useful. They are not interchangeable.

## Start with the question

“Was this app installed?” sounds like one question. In an examination it can mean several:

1. Was the app present when the device was acquired?
2. Was it installed at any point during the period covered by the evidence?
3. When did an installation, update, or uninstall occur?
4. Which bundle and data-container paths belonged to it?
5. Was it obtained by the Apple Account associated with the device?
6. Does a cached store or Biome record still name it after the app itself is gone?

No single artifact answers all six.

That is the first correction I would make to my old wording. We should not talk about “the installed-app list” as though iOS keeps one final answer in one final place. It keeps several records for several operating-system jobs.

## What the sources actually give us

### `applicationState.db`

The Application State artifact reads `compatibilityInfo` data from:

```text
/private/var/mobile/Library/FrontBoard/applicationState.db*
```

When that data is present, it can map a bundle ID to the application bundle path and sandbox path. That remains extremely useful when a forensic tool does not recognize an application and you need to find its container.

The boundary matters. iLEAPP skips an application identifier when it has no usable `compatibilityInfo` record. Across the images we tested, between 41 and 129 distinct identifiers per image lacked that mapping. On one image, more identifiers were omitted than reported. Absence from the Application State table is therefore not proof that an app was never installed. It means the mapping required by that artifact was not available in the database set being examined.<sup><a href="#note-2">[2]</a></sup>

### Mobile Installation logs

The files under:

```text
/private/var/installd/Library/Logs/MobileInstallation/
```

record successful installations, update attempts, container activity, uninstalls, and other installer events. The historical view is where the sequence becomes visible.

These are retained logs, not a device-lifetime ledger. Their timestamps are written without a time-zone marker. In our tested data they behaved like device-local time, which means the examiner still has to document the device time zone and corroborate important events.

iLEAPP now uses installer-reported outcomes to populate **Apps - Installed** and **Apps - Uninstalled**. A successful-install line establishes an installed outcome. An uninstall line or a container-destruction line establishes an uninstall-path outcome. That last distinction deserves attention: every one of the 100 tested `Destroying container` lines came from `MIUninstaller` or `MIUninstallNotifier`, so dropping them would discard useful uninstall evidence.

`Made container live`, data-container movement, and patch activity are different. They can occur during installation, updates, or maintenance and do not establish a successful installation by themselves. They remain in **Apps - Historical Combined**. Bundle IDs found only through those events also appear in **Apps - Container Activity Only**, where the label says exactly what the evidence supports.<sup><a href="#note-2">[2]</a></sup>

### `storeUser.db`

On newer versions of iOS, this App Store cache can be found at:

```text
/private/var/mobile/Library/Caches/com.apple.appstored/storeUser.db*
```

The `current_apps` table can hold bundle IDs, app names, versions, installation timestamps, and deletion-date fields. The `purchase_history_apps` table can preserve App Store purchase history and Apple Account context.

Those populations should not be collapsed into one claim. A purchase-history row associates an app with App Store history. It does not, by itself, prove the app was installed on this device at the reported time. Kevin Pagano documented the database, its schema differences, and that exact interpretation problem when he added the original iLEAPP artifacts.<sup><a href="#note-3">[3]</a></sup>

### `storeSystem.db`

The App Store also keeps system-side persistence databases under a GUID-named system container:

```text
/private/var/containers/Data/System/<UUID>/Documents/Persistence/storeSystem.db*
```

iLEAPP exposes three different populations from this source: install records, update records, and download-package records. Install rows can include bundle ID, application name, version, developer, account identifiers, transaction identifiers, and cached store metadata. Update rows describe what the App Store catalog offered when the cache was refreshed. Package rows describe downloads associated with an install and may repeat the same bundle ID because one application can use several download packages.

Again, the labels do the work. A catalog's latest version is not automatically the version installed on the phone. A package row is not another application. Some integer fields remain undocumented and should be reported as stored rather than translated by guesswork.<sup><a href="#note-2">[2]</a></sup>

### Biome

Modern iOS gives us several Biome views of application installation.

`App.Install` and `_DKEvent.App.Install` are sibling streams, but they do not carry the same message. The `_DKEvent` records contain activity, bundle ID, event and write timestamps, application strings, and an action GUID. The `App.Install` records we tested contain a bundle ID and one undocumented integer, which iLEAPP reports as stored. Published testing describes a 28-day retention setting for the `_DKEvent` stream, making it useful for a recent window rather than permanent history.<sup><a href="#note-4">[4]</a></sup>

The `App.InstalledApp` Biome Set is different again. It is a set of installed-application records with bundle IDs and display names. Its modified or written timestamp belongs to the set record. It is not automatically an installation time.<sup><a href="#note-5">[5]</a></sup>

The iOS 26 test image also contains an `App.Installation` stream. iLEAPP already had a parser for it, contributed by Mattia Epifani and me, and it reports 232 records in that image. The stream carries bundle IDs, versions, build versions, identifiers, 16-byte values, and timestamps. The revisit fixed 13 blank field values that an inferred protobuf decode had mistaken for nested messages.

One clock trap is worth keeping: `App.Installation` stores one timestamp as a Unix-epoch double, while `_DKEvent.App.Install` uses Apple's 2001 epoch. Applying one converter to the other moves the result by 31 years. The `App.Installation` event-type values 0, 1, 2, and 3 still have no published meaning we could verify, so iLEAPP leaves them raw.<sup><a href="#note-6">[6]</a></sup>

### `UninstalledApplications.plist`

This property list can provide bundle IDs and deletion timestamps from:

```text
/private/var/installd/Library/MobileInstallation/UninstalledApplications.plist
```

Prior research found that the file records the last observed deletion date for an app rather than every deletion in a reinstall cycle, and that it is not present in every extraction. We found it on two of 24 tested corpora, the public Cellebrite CTF Otto image on iOS 17.5.1 and an iOS 26 image, with five rows on each. iLEAPP now has a dedicated artifact for it and reports the property list dates as UTC.

That is useful evidence of what the file recorded. It is not a complete list of every app ever removed from the device.<sup><a href="#note-7">[7]</a></sup>

## The testing corrected the parser, and corrected me

This article started as a revisit of the old research. The first three real-data runs exposed enough questions that we widened the work to all 24 registered iOS corpora and completed reports against 16 of them.

The Mobile Installation logs had changed over the years in small but important ways. A success message used different capitalization on the iOS 26 samples. Newer versions described container destruction and patch activity differently. One greedy match even pulled distributor metadata into the bundle ID. The report still produced rows, which is exactly why these problems were easy to miss.

The more important correction was interpretive. We had allowed some container activity to make an app look installed even when the retained log never said the installation succeeded. That was too broad. The installed and uninstalled summaries now require an installer-reported outcome. The remaining container and patch activity stays visible in the history and in a separate **Apps - Container Activity Only** artifact.

Real data also corrected me. I initially thought iLEAPP did not parse the newer `App.Installation` stream. It did. Its actual problem was a handful of blank fields. I also thought container destruction should not affect uninstall state. Every destruction line we tested came from an uninstall component, so those events remain useful uninstall evidence. Other container activity does not become installation evidence.

Biome had one more surprise. `App.Install` and `_DKEvent.App.Install` sound almost interchangeable, but their records are structured differently. We had applied one layout to both, which meant the `App.Install` records were never decoded. Selecting the layout by stream fixed the missed population.<sup><a href="#note-8">[8]</a></sup>

This is why we test artifacts with real data. The code can run. The report can look reasonable. The label can still be making the wrong claim.

## What changed in the reports

Across the 16 full report runs, the before-and-after totals looked like this:

<div style="max-width:100%;overflow-x:auto;">
<table>
<thead>
<tr><th>Artifact</th><th>Before</th><th>After</th></tr>
</thead>
<tbody>
<tr><td>Apps - Historical Combined</td><td>9,575</td><td>11,786</td></tr>
<tr><td>Apps - Installed</td><td>3,981</td><td>791</td></tr>
<tr><td>Apps - Uninstalled</td><td>57</td><td>73</td></tr>
<tr><td>Apps - Container Activity Only</td><td>Not available</td><td>2,957</td></tr>
<tr><td>Biome - App Install</td><td>1,751</td><td>1,982</td></tr>
<tr><td>Biome - App Installation</td><td>232</td><td>232</td></tr>
<tr><td>Apps - Uninstalled Applications Plist</td><td>Not available</td><td>10</td></tr>
</tbody>
</table>
</div>

The installed count fell sharply because the old summary also contained app extensions, malformed bundle IDs, and applications known only through container activity. Those rows were not simply discarded. They were corrected or moved into a table with a narrower label. The history became larger while the state claim became smaller. That is the trade I want.<sup><a href="#note-8">[8]</a></sup>

## Real sources do not produce matching totals

The focused rerun against the public iOS 12.4 CTF image, the public iPhone 12 iOS 18.7 image, and an iOS 26.5.2 image produced these current figures:

<div style="max-width:100%;overflow-x:auto;">
<table>
<thead>
<tr><th>Source population</th><th>iOS 12.4</th><th>iOS 18.7</th><th>iOS 26.5.2</th></tr>
</thead>
<tbody>
<tr><td>Application State mappings</td><td>109</td><td>187</td><td>190</td></tr>
<tr><td>Mobile Installation historical events</td><td>1,003</td><td>591</td><td>455</td></tr>
<tr><td>Mobile Installation installed outcomes</td><td>49</td><td>58</td><td>61</td></tr>
<tr><td>Mobile Installation container-only rows</td><td>92</td><td>174</td><td>160</td></tr>
<tr><td><code>storeUser.db</code> current-app rows</td><td>Not present</td><td>84</td><td>76</td></tr>
<tr><td><code>storeSystem.db</code> install rows</td><td>Not present</td><td>19</td><td>12</td></tr>
<tr><td>Biome <code>App.InstalledApp</code> Set rows</td><td>Not present</td><td>91</td><td>85</td></tr>
<tr><td>Biome App Install rows</td><td>Not present</td><td>168</td><td>266</td></tr>
<tr><td>Biome <code>App.Installation</code> rows</td><td>Not present</td><td>Not present</td><td>232</td></tr>
<tr><td><code>UninstalledApplications.plist</code> rows</td><td>Not present</td><td>Not present</td><td>5</td></tr>
</tbody>
</table>
</div>

Those totals are not competing answers in an election. They count different things over different windows.

Application State counts mappings with the data the parser requires. Mobile Installation history counts events, so one bundle ID can appear many times. The state summaries require a retained installer outcome. App Store databases are caches with version-dependent schemas and populations. The Biome Set records set membership. The two Biome event artifacts record events using different layouts. The property list holds one recorded date per bundle ID.

If the numbers matched by accident, that would not make the sources equivalent.<sup><a href="#note-8">[8]</a></sup>

## A deleted app in the public iOS 12 image

The public iOS 12.4 CTF data gives us a clean example.

`com.tmfcn.dealerapp` exists in `applicationState.db`, but it has no `compatibilityInfo`, so it does not appear in iLEAPP's Application State output.

The Mobile Installation logs tell us what happened next. At `2020-03-23 12:57:02`, the retained log records:

- `Uninstalling identifier com.tmfcn.dealerapp`
- Destruction of its bundle container
- Destruction of its data container

The current mapping is gone. The uninstall sequence remains.

That is the practical value of using both sources. If we searched only the current-state report, we could miss the bundle ID. If we searched only for leftover application data, we could miss it again because the data container was destroyed. The historical log preserves the lead.<sup><a href="#note-8">[8]</a></sup>

## One install, three clocks

The public iPhone 12 image running iOS 18.7 gives us a clean sequence for `com.google.Keep`.

The Mobile Installation log shows the familiar pair: a placeholder installation at `2025-12-20 15:28:54`, then the customer application installation at `2025-12-20 15:29:12`, both in the log's unzoned, device-local presentation.

Two other sources recorded the same install in UTC. The `_DKEvent.App.Install` Biome record carries an event time of `2025-12-20 20:29:00 UTC` and a write time of `2025-12-20 20:29:12 UTC`. The `storeUser.db` current-app row carries an install timestamp of `1766262552`, which is `2025-12-20 20:29:12 UTC`.

Apply the five-hour offset and all three agree to the second. December places the device in Eastern Standard Time. The Biome event time is rounded down to the minute while its write time is not, which is the reason to reach for the write time when you need precision.

The sibling `App.Install` stream holds one record for this bundle carrying a bundle ID and a single integer, reported as stored. Before this work those records were never decoded at all, because one layout had been applied to both streams.

The version strings line up too. The Mobile Installation log records `2.2025.50100` on the customer install, and the App Store cache records the same version for the current app.

That is what corroboration looks like when each source is read with its own conventions. Nothing here required choosing a winner between them.<sup><a href="#note-8">[8]</a></sup>

## The sources do not cover the same window

Four bundle IDs on that same device sit in App Store purchase history and appear nowhere else. They are absent from the current-app table, and they have no rows in the retained Mobile Installation log at all, not even container activity.

Purchase history reached back past the retained log window. If the examination had relied on the installation log alone, those four applications would not have appeared, and the reason would not have been that they were never there. It would have been that the log no longer went back that far.

A retained log is a window, not a lifetime.<sup><a href="#note-8">[8]</a></sup>

## What one removal actually looks like

The Cellebrite CTF23 Felix image, an iPhone 8 Plus on iOS 16.5, shows why the installed count in that table fell so far.

Its retained log holds eighteen uninstall rows. Seventeen of them land in a nine-second window on 2023-07-01. At `07:38:14`, ten rows: `com.facebook.Facebook` and nine of its app extensions, including the share, widget, notification-service and broadcast-upload extensions. At `07:38:23`, seven rows: `com.facebook.Messenger` and six of its extensions.

Two applications were removed. The log recorded seventeen container destructions, because every extension owns a container of its own and each one is torn down separately.

Count those rows as applications and this device looks like it shed seventeen apps in nine seconds. It shed two. That is the same arithmetic, running in the other direction, that made the old installed summary report 3,981 rows where the corrected one reports 791.

The eighteenth row is older, from 2023-02-08, and its identifier is a long hexadecimal string followed by a UUID rather than a reverse-domain bundle ID. It is reported as stored. Not every container carries a name you can read.<sup><a href="#note-8">[8]</a></sup>

## A deletion record that outlives the app

The Cellebrite CTF Otto image, an iPhone 11 Pro on iOS 17.5.1, is the public image that carries `UninstalledApplications.plist`. It holds five rows.

<div style="max-width:100%;overflow-x:auto;">
<table>
<thead>
<tr><th>Deleted (UTC)</th><th>Bundle ID</th><th>In current apps</th><th>In purchase history</th></tr>
</thead>
<tbody>
<tr><td>2024-06-20 01:26:17</td><td><code>com.kik.chat</code></td><td>no</td><td>yes</td></tr>
<tr><td>2024-06-21 03:28:40</td><td><code>com.moxco.bumble</code></td><td>no</td><td>yes</td></tr>
<tr><td>2024-06-21 03:28:48</td><td><code>com.cardify.tinder</code></td><td>no</td><td>yes</td></tr>
<tr><td>2024-07-09 14:42:51</td><td><code>Pototskiy.PotoHEX</code></td><td>yes</td><td>yes</td></tr>
<tr><td>2024-07-09 14:43:08</td><td><code>com.codespaceapps.aichat</code></td><td>yes</td><td>yes</td></tr>
</tbody>
</table>
</div>

Two things stand out.

The first three are gone from the App Store current-app table and still sit in purchase history. The property list preserved when they went, and purchase history preserved that the account had them. Two of those removals are eight seconds apart, which reads as one cleanup session rather than two unrelated decisions.

The last two carry a deletion date while still appearing in the current-app table, each with an install timestamp three days earlier than its own deletion. That is worth reporting as observed. The data here does not establish whether the App Store cache is simply not updated on deletion or whether something else accounts for it, and a report should not pick one.

None of the five appears anywhere in the retained Mobile Installation log. It is the same window limitation seen from the other end: the deletions are recorded, and the installations they refer to fell out of the log long ago.<sup><a href="#note-8">[8]</a></sup>

## One dead end worth documenting

Biome paths named `tombstone` looked promising. Maybe they preserved deleted app events or reached farther back than the local stream.

They did neither.

Across 51 Biome streams and 7,043 written tombstone records from two devices, the fields described retired SEGB files: a numeric filename, byte size, record count, the daemon that wrote the record, and sometimes a maintenance-job name. Not one record contained a bundle ID or application event. The 2,882 deleted SEGB records we checked also had zeroed payloads, leaving only timestamp, slot size, and offset.

That is Biome bookkeeping, not hidden app history. iLEAPP continues to skip those paths, and the artifact notes now explain why.<sup><a href="#note-8">[8]</a></sup>

## A practical workflow

When application presence matters, I would work it this way:

1. Start with the bundle ID. Apple calls it a bundle ID, so that is the term we should use.<sup><a href="#note-9">[9]</a></sup>
2. Use Application State to locate current bundle and sandbox paths where available.
3. Read **Apps - Installed** and **Apps - Uninstalled** as retained installer outcomes, not a lifetime inventory.
4. Read **Apps - Container Activity Only** as a lead, then use **Apps - Historical Combined** to see the actual lines and sequence.
5. Normalize the Mobile Installation log's unzoned local timestamps carefully and compare them with UTC sources.
6. Check `storeUser.db` for current and purchased App Store history. Keep those populations separate.
7. Check `storeSystem.db` for App Store install, update, and download details. Do not count package rows as applications.
8. Check the Biome event streams for recent activity and the Biome Set for installed-app records. Do not turn a set-record timestamp into an install time without validation.
9. Check `UninstalledApplications.plist` when present.
10. Corroborate with application containers, backups, network-usage artifacts, notifications, snapshots, Unified Logs, and application-specific data.
11. Report the source and the boundary with the conclusion.

The final wording should be specific. “The bundle ID appears in a retained uninstall event” is stronger than “the app was on the phone” because it tells the reader exactly why we said it. “The current Application State mapping was absent” is better than “the app was not installed” because it does not claim more than the source can establish.

## What changed since 2018

The old work was not wrong to use `applicationState.db`. It answered the directory-mapping question I had at the time.

What changed is our ability to separate the questions:

- Application State maps current application containers where the required record exists.
- Mobile Installation provides retained lifecycle history, explicit outcome summaries, and a separate view for container-only activity.
- `storeUser.db` adds current and purchased App Store history.
- `storeSystem.db` adds install, update, and download context.
- Biome adds recent events, an installed-app Set, and a separate `App.Installation` stream with version and digest data.
- `UninstalledApplications.plist` can preserve last-deletion records.

More sources do not remove the need for judgment. They give us more chances to test the same proposition from different directions.

That is good stuff.

The fixes described here are merged into iLEAPP and will be available through the [LEAPPs releases page](https://leapps.org/releases#section-ileapp).

## Thank you

Thank you to [Sarah Edwards](https://www.sans.edu/profiles/sarah-edwards) for correcting the original `applicationState.db` approach and pointing me toward Mobile Installation logs; to [Kevin Pagano](https://www.stark4n6.com/2025/04/tracking-ios-app-installs-and-purchase.html) for documenting `storeUser.db` and contributing its iLEAPP artifacts; to [Christopher Vance](https://blog.d204n6.com/2022/09/ios-16-breaking-down-biomes-part-2.html) for the application-install Biome research; to [Mattia Epifani](https://blog.digital-forensics.it/2026/07/84-streams-later-part-2-inside-apple.html) for contributing the `App.Installation` parser and documenting the wider Biome landscape; and to [North Loop Consulting](https://northloopconsulting.com/blog/f/ready-sets-go) for the research behind the Biome Set artifacts.

The best part of revisiting old research is seeing how much of the current answer came from people sharing one useful observation at a time.

The app can be gone. The story can still be there.

## Endnotes

<ol class="blog-endnotes">
<li id="note-1">Alexis Brignoni, <a href="https://abrignoni.blogspot.com/2018/12/identifying-installed-and-uninstalled.html">Identifying installed and uninstalled apps in iOS</a> (2018), <a href="https://abrignoni.blogspot.com/2018/12/update-on-identifying-installed-and.html">Update on identifying installed and uninstalled apps in iOS</a> (2018), and <a href="https://abrignoni.blogspot.com/2019/01/ios-mobile-installation-logs-parser.html">iOS Mobile Installation Logs Parser</a> (2019). The posts document the original question, the correction to key-name lookup, Sarah Edwards's contribution, and the first standalone parser.</li>
<li id="note-2">iLEAPP source at merged commit <code>36a1c0ea66ca7192fb665abe4e865551e49ef6f0</code>: <a href="https://github.com/abrignoni/iLEAPP/blob/36a1c0ea66ca7192fb665abe4e865551e49ef6f0/scripts/artifacts/applicationStateDB.py"><code>applicationStateDB.py</code></a>, <a href="https://github.com/abrignoni/iLEAPP/blob/36a1c0ea66ca7192fb665abe4e865551e49ef6f0/scripts/artifacts/mobileInstall.py"><code>mobileInstall.py</code></a>, <a href="https://github.com/abrignoni/iLEAPP/blob/36a1c0ea66ca7192fb665abe4e865551e49ef6f0/scripts/artifacts/biomeAppinstall.py"><code>biomeAppinstall.py</code></a>, <a href="https://github.com/abrignoni/iLEAPP/blob/36a1c0ea66ca7192fb665abe4e865551e49ef6f0/scripts/artifacts/biomeAppInstallation.py"><code>biomeAppInstallation.py</code></a>, and <a href="https://github.com/abrignoni/iLEAPP/blob/36a1c0ea66ca7192fb665abe4e865551e49ef6f0/scripts/artifacts/uninstalledApplications.py"><code>uninstalledApplications.py</code></a>. These implementations define the paths, parsed event types, state rules, output labels, and interpretation notes discussed here.</li>
<li id="note-3">Kevin Pagano, <a href="https://www.stark4n6.com/2025/04/tracking-ios-app-installs-and-purchase.html">Tracking iOS App Installs and Purchase History with StoreUser DB</a> (2025), and iLEAPP <a href="https://github.com/abrignoni/iLEAPP/blob/36a1c0ea66ca7192fb665abe4e865551e49ef6f0/scripts/artifacts/storeUser.py"><code>storeUser.py</code></a>. The research distinguishes <code>current_apps</code> from <code>purchase_history_apps</code> and cautions that purchase history does not establish local installation.</li>
<li id="note-4">Christopher Vance, <a href="https://blog.d204n6.com/2022/09/ios-16-breaking-down-biomes-part-2.html">iOS 16 Breaking Down the Biomes Part 2: AppInstalls, AppLaunch, &amp; AppIntents</a> (2022). The article documents the <code>_DKEvent.App.Install</code> location, 28-day metadata setting, fields, timestamp behavior observed in testing, and retention limitations.</li>
<li id="note-5">North Loop Consulting, <a href="https://northloopconsulting.com/blog/f/ready-sets-go">Apple Did Your Homework: Pre-Analyzed Data in Biome Databases</a>, and iLEAPP <a href="https://github.com/abrignoni/iLEAPP/blob/36a1c0ea66ca7192fb665abe4e865551e49ef6f0/scripts/artifacts/biomeSetsStores.py"><code>biomeSetsStores.py</code></a>. The iLEAPP artifact reports the Set record's modified or written timestamp and does not label it as an installation timestamp.</li>
<li id="note-6">Mattia Epifani, <a href="https://blog.digital-forensics.it/2026/07/84-streams-later-part-2-inside-apple.html">84 Streams Later, Part 2: Inside Apple Biome</a> (2026). The article identifies <code>App.Installation</code>, describes it as apparently tracking updates, reports 28-day retention, and lists event timestamp, app timestamp, bundle ID, app UUID, version, build version, and two 16-byte values. LEAPPs testing independently decoded the same field groups from 232 records and leaves the undocumented event type raw.</li>
<li id="note-7">Christopher Vance, <a href="https://blog.d204n6.com/2019/09/ios-tracking-traces-of-deleted.html">iOS: Tracking Traces of Deleted Applications</a> (2019). The article documents the property-list path, last-deletion behavior observed during reinstall cycles, and inconsistent presence across devices.</li>
<li id="note-8">LEAPPs real-data validation completed August 25, 2026, for <a href="https://github.com/abrignoni/iLEAPP/pull/2059">iLEAPP PR #2059</a>. Raw-log census covered all 24 registered iOS corpora, and finished iLEAPP reports covered 16. Regression checks accounted for every prior Mobile Installation event, eliminated malformed bundle IDs and Biome decode skips in the tested populations, and left unrelated Application State and reboot outputs unchanged. All 10 CI checks passed before merge. A post-merge focused rerun reproduced the article's current counts. The comparison table's iOS 18.7 column, the three-clock sequence and the purchase-history-only bundles come from the public iPhone 12 iOS 18.7 image (MSAB Mobile Forensics Digital Summit CTF 2026); the removal arithmetic from the public Cellebrite CTF23 Felix image on iOS 16.5; and the deletion property list from the public Cellebrite CTF Otto image on iOS 17.5.1. Each archive's SHA-256 was checked against the corpus registry before its run, and every run was confirmed complete with a clean sweep for SQLite error vocabulary.</li>
<li id="note-9">Apple, <a href="https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleidentifier"><code>CFBundleIdentifier</code></a>. Apple defines it as the unique identifier for a bundle and uses “bundle ID” throughout its documentation.</li>
</ol>
