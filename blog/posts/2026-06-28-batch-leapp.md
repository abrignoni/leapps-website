---
title: Introducing Batch LEAPP
date: 2026-06-28
author: Alexis Brignoni
tags: [iLEAPP, ALEAPP, RLEAPP, VLEAPP, tools, batch]
excerpt: Batch LEAPP runs any LEAPP tool across an entire folder of extractions and builds one report index that links every result, with hashing and a manifest for your case file. Here is what it does and how to get it.
---

# Introducing Batch LEAPP

If you have ever had a folder full of extractions and needed to run them through [iLEAPP](https://leapps.org/releases#section-ileapp) one at a time, this is for you. Batch LEAPP takes a directory, finds every extraction inside it, and runs the LEAPP tool of your choice against each one. You walk away and come back to a set of finished reports ready for review.

It works with iLEAPP, [ALEAPP](https://leapps.org/releases#section-aleapp), [RLEAPP](https://leapps.org/releases#section-rleapp), and [VLEAPP](https://leapps.org/releases#section-vleapp). They share the same command line, so the same tool drives any of them.

![Batch LEAPP running a batch of extractions](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-06-28-batch-leapp/batch-leapp-gui.webp)
*Figure 1: Batch LEAPP processing a folder of iOS extractions*

## What it does

- Recursively finds every extraction archive (zip, tar, tar.gz) and runs the LEAPP tool on each into its own output folder.
- Computes the SHA-256 of each input and writes a manifest (CSV and JSON) for your case file.
- Runs several extractions in parallel, with a live progress log.
- Skips things that are not extractions, like prior report folders and stray cache files, so you do not get garbage runs.
- Flags corrupt or mislabeled archives instead of crashing on them.
- Lets you preview the whole plan with a dry run before committing hours of processing.

## One index for everything

When the batch finishes you get a single index.html at the root of the output folder. One row per extraction, with links to the report, the [LAVA](https://leapps.org/releases#section-lava) project, and the input hash. It is styled to match the LEAPPs reports, and every link is relative so you can zip the whole output folder and hand it off.

![The master report index](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-06-28-batch-leapp/report-index.png)
*Figure 2: The master index, one row per extraction*

## Straight into LAVA

If LAVA is installed, the LAVA button opens a dialog with the exact path to the project so you can load it in a couple of clicks. If LAVA is not installed, the button points you to where to get it.

![Open in LAVA dialog](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-06-28-batch-leapp/lava-modal.png)
*Figure 3: Opening a parsed project in LAVA from the index*

## Built for casework

Hashing is on by default. The manifest records what was processed, each input SHA-256, the status, and where each report and LAVA file landed. Stop means stop: closing the app or clicking Stop terminates the running LEAPP processes instead of leaving them going in the background.

## Get it

Batch LEAPP is free and open source. There is a graphical app and a command line version, with prebuilt downloads for macOS and Windows so you do not need Python installed.

- Download: [github.com/abrignoni/batch-leapp/releases/latest](https://github.com/abrignoni/batch-leapp/releases/latest)
- Source and docs: [github.com/abrignoni/batch-leapp](https://github.com/abrignoni/batch-leapp)

Point it at the LEAPP command line tool (for example ileapp.py or the CLI binary), not the interactive GUI build. Feedback and pull requests are welcome.
