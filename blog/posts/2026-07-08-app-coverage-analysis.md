---
title: The Apps We Are Not Parsing (Yet)
date: 2026-07-08
author: Alexis Brignoni
tags: [iLEAPP, ALEAPP, LAVA, batch, coverage, tools]
excerpt: Batch LEAPP now answers a question I have wanted answered for years. Out of all the apps installed on our test devices, which ones do the LEAPPs actually parse, and which ones are we missing? One flag, one database, and a data-driven module-writing roadmap.
---

# The Apps We Are Not Parsing (Yet)

Here is a question I have wanted a real answer to for years: **out of all the apps installed on our test devices, which ones do the LEAPPs actually parse, and which ones are we missing?**

We all have a feel for it. Everybody knows there is no Snapchat module. But a feel is not a list, and a list is what you need when you are deciding what to build next. So Batch LEAPP can now produce that list, measured against real test images instead of guesses.

**Short version:** run your test images through Batch LEAPP with one new flag, get a database of every installed app, every file each app owns, and every file the LEAPP modules actually touched. Open it in LAVA, sort the "Apps Not Parsed" report, and there is your module-writing roadmap, ranked by how much evidence is sitting on disk unread.

**Long version:** keep reading.

## One flag

```
python3 batch_leapp.py ~/test_images ~/reports --leapp ~/iLEAPP/ileapp.py --coverage
```

The `--coverage` flag does two things. First, it turns on a set of developer-only App Inventory artifacts that now ship with iLEAPP and ALEAPP. They inventory the installed apps and every file in the extraction, and they never run for regular users. Second, when the batch finishes it aggregates everything into a single `batch_apps.sqlite` at the output root, next to a `batch_apps.lava` project file so the whole analysis opens in LAVA like any other case.

The master index gets a new button at the top, so the analysis is one click away from the reports:

![The master index with the App Coverage Analysis button](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-08-app-coverage-analysis/index-coverage-button.png)
*Figure 1: The batch report index. The gold button opens the coverage analysis in LAVA.*

## What five iPhones told us

I ran it against five iOS full filesystem test images, from an iPhone 8 on iOS 17.6.1 to an iPhone 16 on iOS 18.3.2. The inventory counted 1.3 million files across more than six thousand app containers, and every container resolved to its owning app.

![App parsing coverage per test image](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-08-app-coverage-analysis/coverage-per-image.png)
*Figure 2: Installed apps per image, and the slice app-specific modules parsed.*

Before anyone gasps at the percentages: most of the 800 apps on any phone are keyboards, stickers, and single-purpose junk nobody will ever write a module for. The percentage is not the point. The point is what is IN the unparsed list, and that is where it gets interesting:

![Apps Not Parsed rollup in LAVA](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-08-app-coverage-analysis/lava-apps-not-parsed.png)
*Figure 3: The Apps Not Parsed rollup in LAVA, sorted by files on disk.*

- **Snapchat:** unparsed in 5 of 5 images, with 29,482 files sitting on disk. No iLEAPP module exists.
- **Facebook:** unparsed in 4 of 4 images it appears in.
- **Twitter and YouTube:** same story.
- **Instagram:** present in all five images but unparsed in only ONE. Read that again: the modules work, but something about that one image (app version? a migration? a moved database?) broke the search patterns. That is a bug report waiting to be filed, and it is a different kind of finding than "no module exists."

![Top unparsed apps across the corpus](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-08-app-coverage-analysis/top-unparsed-apps.png)
*Figure 4: The target list across all five images, ranked by evidence volume.*

And one more thing it caught that I did not ask it to: an extraction filed in my Android folder came back with no Android inventory at all. No packages.xml, no build.prop. Because it was an iPhone 8 the whole time. The coverage report flagged the mislabeled image on its first run.

## Android too

Same command, ALEAPP instead. On a Pixel 8 Pro running Android 16, the tooling inventoried 385 installed packages and put **Instagram, Signal, Kik, and Telegram** at the top of the unparsed list. If you have ever wanted a data-backed argument for which Android chat module the community needs next, there it is.

## Keeping the verdicts honest

Two things make this measurement trustworthy instead of naive. Modules that touch nearly every app on the phone without decoding anything, the preference-plist sweeps and the container metadata readers, are classified as *generic* and do not make an app count as parsed. And on iOS, shared group containers (`group.com.kik.chat`) are folded into the app that owns them, so WhatsApp, Telegram, and Kik get proper credit for the parsing that happens in their group data. Both of those decisions came out of testing against real images, and both are documented.

## Get it

- 🔗 Get Batch LEAPP here: [leapps.org/releases#section-batch-leapp](https://leapps.org/releases#section-batch-leapp)
- 📖 How to run it (both uses): [Batch LEAPP guide](https://github.com/abrignoni/batch-leapp/blob/main/docs/batch-leapp-guide.md)
- 📊 How to read the reports in LAVA: [Coverage analysis guide](https://github.com/abrignoni/batch-leapp/blob/main/docs/coverage-analysis-lava.md)

Coverage mode needs source checkouts of iLEAPP or ALEAPP, since the inventory artifacts ship in the repos. Everything is free and open source, and now the "what should we build next?" conversation has data behind it. When the first modules born from this list land, I will re-run the corpus and show you the before and after.

Feedback and pull requests are welcome. You can reach me at [abrignoni.github.io](https://abrignoni.github.io) or email abrignoni[at]duck[dot]com.
