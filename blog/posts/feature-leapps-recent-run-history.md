---
title: Feature Highlight: Recent Run History in LAVA
date: 2026-07-20
author: James Habben
tags: [LAVA, iLEAPP, ALEAPP, RLEAPP, VLEAPP, features]
excerpt: A quick look at the new opt-in LEAPPs recent run history feature and how LAVA can use it to put recent parser outputs right on the welcome screen.
---

# Feature Highlight: Recent Run History in LAVA

This is the first in what I hope becomes a small series of LEAPPs and [LAVA](https://leapps.org/releases#section-lava) feature highlights. Not every useful update is a brand-new artifact parser. Sometimes the nice stuff is a workflow improvement that quietly removes a few clicks from your day.

Recent run history is one of those. The short version: the LEAPP runners can now save recent run information, and LAVA can read that shared history so recent LEAPP outputs show up on the welcome screen. It is a LAVA feature from the user's point of view, but it is powered by the LEAPP tools doing a little extra bookkeeping after a successful run.

![LAVA welcome screen showing Watched Folders populated with recent LEAPP runs](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/feature-leapps-recent-run-history/lava-watched-folders.webp)
*Figure 1: Recent LEAPP runs shown in LAVA's Watched Folders section*

## The welcome screen gets smarter

When LAVA starts, the welcome screen already gives you a place to open a project. With recent run history, it can also show LEAPP outputs that were recently created by [iLEAPP](https://leapps.org/releases#section-ileapp), [ALEAPP](https://leapps.org/releases#section-aleapp), [RLEAPP](https://leapps.org/releases#section-rleapp), or [VLEAPP](https://leapps.org/releases#section-vleapp). Those entries appear in the **Watched Folders** section with tool labels, so a recent iLEAPP run can sit next to a recent ALEAPP or VLEAPP run without you needing to remember exactly where the report landed.

That matters because report folders are easy to lose track of during normal casework. You run a parser, check something else, come back later, and suddenly you are spelunking through output folders trying to find the right output. LAVA can now do more of that remembering for you.

## It is opt in

The history feature is intentionally opt in. Each LEAPP runner has a setting for saving paths as recent history. That matters for a forensic tool. Some people want workflow memory. Some people do not want tools saving recently used paths on a workstation. Both are reasonable positions, so the feature waits for the user to enable it.

Once enabled, the runner can save recent input paths, recent output paths, and successful LAVA project outputs. There is also a clear-history option from the runner settings if you want to wipe the shared history later.

![iLEAPP settings window showing the recent history opt-in setting](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/feature-leapps-recent-run-history/ileapp-settings.webp)
*Figure 2: Recent history is enabled from the LEAPP runner settings*

## What gets saved

For the curious, this is stored in a small shared LEAPP directory in the user's application-data area. The shared folder is:

```text
Windows: %APPDATA%\LEAPP
macOS: ~/Library/Application Support/LEAPP
Linux: ~/.config/LEAPP
```

There are two JSON files involved:

```text
settings.json
history.json
```

`settings.json` stores whether history is enabled and the limits for saved paths and runs. The defaults are intentionally modest: 10 recent input/output paths and 20 recent runs.

```json
{
  "schema_version": 1,
  "history_enabled": true,
  "path_history_limit": 10,
  "run_history_limit": 20
}
```

`history.json` stores the actual recent values. It can include shared input paths, shared output paths, and recent successful runs. A run entry records which LEAPP tool created it, the LEAPP version, when it was recorded, and the LAVA project path.

```json
{
  "schema_version": 1,
  "input_paths": [
    "C:\\Cases\\Phone01"
  ],
  "output_paths": [
    "\\\\?\\C:\\Cases\\Reports"
  ],
  "runs": [
    {
      "leapp_id": "ileapp",
      "leapp_version": "2.6.0",
      "recorded_at": "2026-07-20T18:00:00Z",
      "lava_file_path": "\\\\?\\C:\\Cases\\Reports\\Phone01\\_lava_data.json"
    }
  ]
}
```

The LEAPP code normalizes paths before saving them, deduplicates repeated entries, and keeps the newest values at the top. On Windows, output and LAVA paths may be stored with the extended-length `\\?\` prefix so long paths behave better.

## How LAVA reads it

LAVA does not need a special import step for this. On startup or when closing an open project, LAVA reads the shared LEAPP `history.json` file from the same application-data location. It looks at the `runs` list, pulls out the `lava_file_path` values, validates that the files still exist, and then adds the valid entries to the welcome screen.

If a path no longer exists, LAVA skips it instead of showing a dead project link. If the history file does not exist, nothing dramatic happens. The welcome screen just behaves like it did before.

## A small feature with a nice payoff

The LEAPP tools have traditionally provided static output in various forms. Now that we have a dynamic review tool, we can do a lot more to integrate the tools together. Our hope is to make open source forensics smoother and easier to use.

In the next feature highlight, we can look at the other side of this same history feature: how the LEAPP runners use recent input and output paths for the path dropdowns.

And, because this is forensics and we just talked about recent history, maybe the next artifact parser should be for the LEAPP tool history itself.
