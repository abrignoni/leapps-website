---
title: Every Step You Take, Eight Years Later: Android UsageStats and Recent Tasks
date: 2026-08-03
author: Alexis Brignoni
tags: [ALEAPP, Android, UsageStats, Recent Tasks, Pattern of Life, DFIR]
excerpt: Android's pattern-of-life evidence grew from readable XML into tokenized protobufs carrying app lifecycle, lock state, notifications, services, task roots, and more. We went back to the source, updated ALEAPP, and came away with better data—and better warnings about what it actually proves.
---

# Every Step You Take, Eight Years Later: Android UsageStats and Recent Tasks

Android keeps receipts.

Not one perfect diary. Not one magical timestamp that answers every question. It keeps a collection of system records that, when interpreted together, can tell us when the screen became interactive, when the keyguard disappeared, which activity resumed, what task sat in Recents, and sometimes what the screen looked like.

That is a lot of pattern-of-life information hiding in directories most users will never see.

I first wrote about [Android UsageStats](https://abrignoni.blogspot.com/2019/02/android-usagestats-xml-parser.html) and [Recent Tasks](https://abrignoni.blogspot.com/2019/02/android-recent-tasks-xml-parser.html) in February 2019. Those posts grew out of Jessica Hyde's excellent *Every Step You Take: Application and Network Usage in Android* research. At the time, the evidence was XML, the event vocabulary was much smaller, and the parsers were standalone scripts.

Android did what Android does. It changed the format, moved the files, added fields, added event types, and made the whole thing more interesting.

So we went back.

**Short version:** current ALEAPP source now parses the modern UsageStats protobufs in considerably more depth, understands all event values currently defined by Android, and reads the protobuf metadata beside Recent Tasks snapshots. That last part matters because Android can tell us whether an image is a real snapshot of the app or a theme-generated substitute.

**Long version:** keep reading. The good stuff is in the details—and so are the traps.

## Two related sources, two different jobs

UsageStats and Recent Tasks overlap, but they are not the same artifact.

**UsageStats** records application and system events across time. Depending on the Android version, those records can describe:

- Activities resuming, pausing, stopping, and being destroyed
- User and system interaction with packages
- Screen interactive and non-interactive transitions
- Keyguard shown and hidden transitions
- Foreground services starting and stopping
- Notification activity
- Device startup and shutdown bookkeeping
- User unlock and stop events
- App standby changes, shortcuts, task roots, and components used

**Recent Tasks** is the system's persisted view of tasks it may need to restore or show in the Recents interface. A task record can carry the package, activity, calling package, task ID, and several activity times. The task ID also ties the record to snapshot images and snapshot metadata.

UsageStats is the broader timeline. Recent Tasks gives selected tasks richer context and, when available, a picture.

Put them together and they become much more useful than either one alone.

## Where the evidence lives

On older Android versions, UsageStats commonly appears under:

```text
/data/system/usagestats/<user>/
```

Modern Android places the user's UsageStats under credential-encrypted storage:

```text
/data/system_ce/<user>/usagestats/
```

Inside are interval directories named `daily`, `weekly`, `monthly`, and `yearly`. Their files are named with the interval's starting time in Unix epoch milliseconds.

Recent Tasks and its related data live nearby:

```text
/data/system_ce/<user>/recent_tasks/
/data/system_ce/<user>/recent_images/
/data/system_ce/<user>/snapshots/
```

That `system_ce` location is not trivia. CE means credential encrypted. Android moved sensitive recent-task data there specifically so it would not be available before the user unlocked the profile. [The AOSP change that moved it](https://android.googlesource.com/platform/frameworks/base/+/4bccb46554d9fd0d7de44e069d67af970d178a0b) says exactly that.

Acquire the complete directories. A loose task XML without its matching snapshot directory is only half an answer.

## The XML grew up and became protobuf

The 2019 UsageStats article worked with readable XML. You could open a file, see a package name, identify an event type, and do the timestamp arithmetic yourself.

Modern Android uses protobuf.

Android 10 introduced a protobuf form with a shared string pool. Android 11 moved to a second protobuf generation that uses tokenized package mappings. The interval record may say package token `12` and class token `4`; the separate `mappings` file is what turns those values back into a package and class name.

This is a good example of why searching a modern extraction for a package name can miss relevant evidence. The event file may not contain that name at all. It contains a number that only becomes meaningful after another file is parsed.

ALEAPP already understood both protobuf generations. The revisit showed that understanding the container was not the same as exposing everything inside it.

## Four event types became thirty-two values

The original post centered on four useful events: move to foreground, move to background, configuration change, and user interaction.

Current Android defines values `0` through `31` in [`UsageEvents.java`](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/app/usage/UsageEvents.java). That is 32 possible values, including internal bookkeeping events.

Here are the ones I expect examiners will reach for most often:

| Value | Android name | What it tells us |
|---:|---|---|
| 1 | `ACTIVITY_RESUMED` | An activity entered Android's resumed lifecycle state |
| 2 | `ACTIVITY_PAUSED` | An activity entered the paused state |
| 7 | `USER_INTERACTION` | Android recorded some form of user interaction with the package |
| 10 | `NOTIFICATION_SEEN` | A notification was viewed |
| 12 | `NOTIFICATION_INTERRUPTION` | The app posted a visually or audibly interruptive notification |
| 15 | `SCREEN_INTERACTIVE` | The screen became fully interactive, not merely ambient |
| 16 | `SCREEN_NON_INTERACTIVE` | The screen became non-interactive |
| 17 | `KEYGUARD_SHOWN` | The lock-screen keyguard was shown |
| 18 | `KEYGUARD_HIDDEN` | The keyguard was hidden, typically during an unlock |
| 19 / 20 | `FOREGROUND_SERVICE_START` / `STOP` | A foreground service started or stopped |
| 23 | `ACTIVITY_STOPPED` | An activity became invisible |
| 26 / 27 | `DEVICE_SHUTDOWN` / `STARTUP` | Android recorded shutdown/startup bookkeeping |
| 28 | `USER_UNLOCKED` | The user's CE storage became available for the first time after startup |
| 30 | `LOCUS_ID_SET` | An activity received a Locus ID used for contextual activity |
| 31 | `APP_COMPONENT_USED` | A package component such as a service, receiver, or provider was used |

Value 31 was the first concrete bug this revisit found. Android defined `APP_COMPONENT_USED`; ALEAPP stopped its named mapping at 30. The data was not discarded, but examiners saw an unexplained `31` instead of a useful name. Fixed.

ALEAPP now maps the complete current list, including the internal rollover and persistence events that are easy to misread when left as bare numbers.

## The fields we were leaving on the table

The protobuf definitions contain more than package, class, timestamp, and event type. Both current schemas can carry details that help explain what kind of use Android recorded.

As part of this revisit, ALEAPP now exposes:

- Last time active
- Total time active
- Last and total foreground-service use
- Last and total visible time
- Last time a package component was used
- App launch count
- Event flags, including instant-app identification
- Shortcut ID
- App standby bucket and the separate reason value
- Notification channel
- Activity instance ID
- Task-root package and class
- Locus ID
- User-interaction category and action when newer Android data provides them

Why do the task-root fields matter? Because the package generating an event is not always the package that started the task. Android stores both relationships. That can help separate an activity launched directly from one reached through another application.

The current schemas are documented in AOSP's [UsageStats protobuf](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/proto/android/server/usagestatsservice.proto) and [tokenized UsageStats v2 protobuf](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/proto/android/server/usagestatsservice_v2.proto). We refreshed ALEAPP's bundled definitions from those sources instead of guessing at the wire format.

## Recent Tasks had another file waiting for us

The task XML and JPG are only two pieces of the Recent Tasks puzzle.

For a persisted snapshot, modern Android can create three related files using the same task ID:

```text
123.jpg
123_reduced.jpg
123.proto
```

The JPG is the high-resolution image. The reduced image is the smaller version Android can load quickly. The protobuf explains the snapshot.

ALEAPP now parses that protobuf and reports:

- Snapshot ID and its corresponding capture time
- Top activity component
- Whether Android says it is a real snapshot
- Orientation and rotation
- Original task dimensions
- Windowing mode
- Translucency
- Content and letterbox insets
- Appearance and UI mode values

Android's [`TaskSnapshotProto`](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/proto/src/windowmanager.proto) defines those fields. The current AOSP [`AbsAppSnapshotController`](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/wm/AbsAppSnapshotController.java) assigns the snapshot ID using the current wall-clock time in milliseconds, which gives us a capture-time value to surface alongside the task timestamps.

That capture time is an AOSP behavior, not a promise that every manufacturer has implemented every Android version identically. Validate it on the device family and version that matter to your case.

## “Is Real Snapshot” is the column I wanted

This is my favorite part of the update.

An image in the snapshots directory is not automatically a literal screenshot of the application. Android's `TaskSnapshot` documentation says the system may generate an app-theme representation when the window is secure or previews are disabled.

The protobuf stores that distinction in `is_real_snapshot`.

- **Yes:** Android identifies the image as a real task snapshot.
- **No:** Android identifies it as a generated substitute, such as an app-theme snapshot.

Without that field, both files look like “a snapshot.” With it, the report tells the examiner which kind Android says it created.

That does not solve every interpretation question. A real snapshot still needs to be correlated with its task, timestamps, file-system metadata, and the rest of the case. But it prevents us from treating a privacy-preserving placeholder as if it showed the user's screen. That is a meaningful improvement.

## The important warnings

Pattern-of-life artifacts are powerful. They are also excellent at producing confident mistakes when we ask them to prove more than they record.

### `ACTIVITY_RESUMED` does not mean “the user tapped the app”

It means an Android activity entered the resumed lifecycle state. A user may have launched it. Another app, a notification, a system process, restoration after a configuration change, or some other path may have caused the transition.

Use the package, class, task root, surrounding events, and application data to determine what happened.

### `SCREEN_INTERACTIVE` does not mean “unlocked”

Android defines it as the screen entering a state ready for full interaction rather than ambient display. The keyguard may still be present. `KEYGUARD_HIDDEN` is more closely associated with unlocking, but even that belongs in a sequence, not alone in a conclusion.

### A foreground service is not a foreground screen

The name is dangerously friendly. A foreground service is an Android service with elevated user awareness, commonly accompanied by a persistent notification. It does not mean the app's interface was visible.

### Daily, weekly, monthly, and yearly records overlap

Do not count the same event four times. Those directories are interval views, not four independent witnesses. For detailed timelines I normally begin with the daily event logs and use broader intervals for coverage and aggregate context.

### Shutdown is not an exact power-loss timestamp

Android's own source warns that `DEVICE_SHUTDOWN` represents the last time the UsageStats database was persisted before shutdown. Events between that write and the actual loss of power may not survive. Open activity or service events without a matching close around shutdown/startup should not be given an invented ending.

### Recent Tasks is recent, not complete

Tasks leave the list. Snapshot files are deleted. Devices impose limits. A missing task does not prove the application was not used, and an existing task does not tell us every time it was used.

Absence is not an alibi.

## Building a defensible sequence

Imagine a timeline showing:

```text
SCREEN_INTERACTIVE
KEYGUARD_HIDDEN
ACTIVITY_RESUMED        com.example/.MainActivity
USER_INTERACTION       com.example
Recent Task 123        com.example/.MainActivity
Snapshot 123           Is Real Snapshot: Yes
```

That is a strong sequence. It supports that the screen became interactive, the keyguard was hidden, the activity resumed, Android recorded user interaction with the package, and a real task snapshot was captured for the matching activity.

It still does not identify the human holding the device. It does not prove what they understood. It does not make the snapshot time equal to every task timestamp. Those conclusions require the rest of the evidence.

Good forensic interpretation is not making the artifacts say less. It is refusing to make them say more.

## Working it in ALEAPP and LAVA

The updated artifacts are in ALEAPP's current source and will be included in the next packaged release.

1. Process the full Android extraction with [ALEAPP](https://www.leapps.org/releases#section-aleapp).
2. Open **Usage Stats** in the HTML report or LAVA.
3. Filter `Usage Type` to `event-log` and begin with the `daily` interval for event-level work.
4. Filter by package, class, event type, or the time range that matters.
5. Open **Recent Activity** and correlate by package, component, task ID, and time.
6. Review the snapshot image together with **Is Real Snapshot**, **Snapshot Top Activity**, and **Snapshot Capture Time**.
7. Correlate the sequence with the application's own databases, notifications, logs, and other system artifacts.

LAVA is especially useful here because UsageStats can generate thousands of records. Filter first. Tag the sequence that matters. Export the subset instead of trying to make a human read the whole ocean.

## What changed since 2019

The old posts are still part of the story. The timestamp-offset explanation remains important. The task-ID correlation remains important. The warnings about incomplete attributes and missing images remain important.

What changed is the scale:

- XML became two protobuf generations.
- Plain strings became token mappings.
- Four headline event types became a vocabulary of 32 values.
- More lifecycle, lock-state, service, notification, task-root, and interaction details became available.
- Snapshot metadata gave us a capture time and a way to distinguish real images from generated substitutes.
- Two standalone scripts became maintained ALEAPP artifacts with HTML and LAVA output.

That is exactly why old research deserves a return visit. Sometimes the original conclusion survives. Sometimes the format changes underneath it. Sometimes the evidence has been carrying useful fields for years and all we needed to do was go back and ask better questions.

## Thank you

Thank you to Jessica Hyde for the research that started this path and to Sarah Edwards for setting such a high bar for pattern-of-life analysis. The original work did what good research should do: it gave the community something useful and made the next questions possible.

And thank you to everyone contributing test extractions to ALEAPP. The artifact currently produces data across Android 10 through Android 16 samples in our test corpus. That breadth is how we catch changes before they catch an examiner.

Free tools, open source, current research. Go test it, validate it, and tell us what Android changes next.
