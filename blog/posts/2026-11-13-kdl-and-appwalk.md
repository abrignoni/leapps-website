---
title: KDL and AppWalk, two tools that work with the phone itself
date: 2026-11-13
author: Alexis Brignoni
tags: [KDL, AppWalk, Android, known data, validation, DFIR, open source]
excerpt: KDL writes down what you do on a test phone, so a forensic tool can be checked against known data. AppWalk documents what an app shows on a phone under examination, screen by screen, from your computer. Both keep a hash-chained log. Free and open source.
---

# KDL and AppWalk, two tools that work with the phone itself

![Headline: Log it. Walk it. On the left, a phone with a red frame labelled KDL, on a test phone. Its screen says Recording and lists log rows: Sent message, Mark, Received message, Incoming call, Missed call, each with a time, and a red MARK button sits in the corner. On the right, a phone with a teal frame labelled AppWalk, on a phone under examination. Its screen shows chat bubbles inside capture brackets, with a stack of earlier screenshots fanned out behind it. A metal chain runs from one phone to the other, red on the KDL side and teal on the AppWalk side, and a paper tag hangs from its lowest link reading Write it down.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-11-13-kdl-and-appwalk/kdl-appwalk-hero.webp)

The LEAPPs read files out of an extraction. KDL and AppWalk work with the phone itself. They go on different phones and do different jobs, but they share one idea: write down what happened while it happens, in a record somebody else can check.

## KDL: known data without the notepad

If you have made test data for a parser, you know the routine. Phone in one hand, notes in the other. Send a message, write down the time. Take a picture, write down the time. Joshua Hickman's test images, which so many of us lean on, come with that kind of document, and it is great work. It is also typed by hand, with times to the minute.

KDL (Known-data logger) is an Android app for test phones that does the writing for you. Turn on capture and use the phone as you normally would. KDL logs what you did and when: taps, typed text, screens, incoming messages and calls, and a screenshot each time you tap the red MARK button.

![Three KDL screens from a test emulator. First, Google Messages right after a text was sent, with the red MARK button floating over the thread. Second, the Label this mark form, showing the marked screenshot, the text that was on that screen, and buttons for Sent message, Received message, Outgoing call, Incoming call, Took photo and Deleted message. Third, the Timeline on the Check tab, listing Session stopped, Deleted message, Missed call, Incoming call, Received message, Mark and Sent message, each with its time to the second.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-11-13-kdl-and-appwalk/kdl-mark-label-timeline.webp)
*Figure 1: MARK over the app under test, labelling a mark from the text on its screen, and the Timeline.*

When you stop the session, the Check tab lists what KDL inferred or could not label, and you confirm or fix it. Edits never overwrite. Each one is a new revision, and the action keeps its time.

Then export. Every row is hashed with the one before it, so a changed or removed row breaks the chain. A script turns the export into a spreadsheet with a sheet per app, and that goes in the documentation folder next to the extraction. Now anyone validating a tool can check each action against what the tool reports.

Two more scripts come with it. `kdl_locate.py` is for an app no LEAPP parses yet: give it the export and an extraction, and it looks for where the app stored what you logged. `kdl_check.py` grades a LEAPP's output against the log.

KDL ships rules for Google Messages and the AOSP Camera. For other apps you can teach it a rule from a capture, or log by hand. Rules can be exported and shared, so if you teach it an app, send the rule my way.

Test phones only, with test accounts. Never install it on an evidence device.

<video controls preload="none" playsinline poster="https://leapps.org/videos/kdl-intro.jpg?v=20261109" style="width:100%;height:auto;aspect-ratio:16/9;background:#000">
  <source src="https://leapps.org/videos/kdl-intro.mp4?v=20261109" type="video/mp4">
</video>

*KDL in under a minute.*

## AppWalk: document what the app shows

AppWalk is for the other phone, the one you are examining with the owner's consent or other lawful authority. Sometimes the job is to show what an app displays, and the old way is to photograph the screen one swipe at a time. AppWalk does that part for you.

It runs on your computer and drives the phone over a USB cable. You open the app on the phone. AppWalk scrolls through it, or opens the conversations you choose and walks each one, and saves a screenshot of every screen with the text the app reported for it.

![The AppWalk window on macOS, on step 3, Run. The left panel reads Documenting (555) 123-0015, with 4 screenshots, row 1 of 2, and a progress bar, Start, Pause and Stop after this step buttons, and a log of what AppWalk is doing, step by step. The right panel shows the latest screenshot: a Google Messages thread with three test messages.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-11-13-kdl-and-appwalk/appwalk-run.webp)
*Figure 2: AppWalk walking a conversation. The latest screenshot shows on the right as it goes.*

Everything it does goes into a hash-chained log in KDL's export format, so KDL's spreadsheet script reads it too. At the end you get a PDF report with each screenshot next to its text. The report shows the latest row hash, and that hash covers every row and every picture. Write it down, and the export can be checked against it later.

![A page of an AppWalk PDF report for a test conversation. On the left, each message from the screen as text, with whether it was received or sent. On the right, the screenshot the text came from, with its number, time and a short hash under it. The page footer shows the run name and the latest row hash.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-11-13-kdl-and-appwalk/appwalk-report-page.webp)
*Figure 3: A report page. Each screenshot sits beside the messages read from it.*

Profiles tell AppWalk which lines are messages, times and pictures, and who sent them. They ship for Google Messages, Fossify Messages, WhatsApp, Signal and Discord. For any other app, Teach this app builds one from a few clicks on a screenshot.

AppWalk does not unlock anything or get around any lock. If a lock screen or a password prompt comes up, it stops and waits for you. Builds are there for macOS, Windows and Linux, or you can run it from the source.

<video controls preload="none" playsinline poster="https://leapps.org/videos/appwalk-intro.jpg?v=20261113" style="width:100%;height:auto;aspect-ratio:16/9;background:#000">
  <source src="https://leapps.org/videos/appwalk-intro.mp4?v=20261113" type="video/mp4">
</video>

*AppWalk in under a minute.*

## Get them

Both are free and open source, MIT licensed, and both have a user manual with every screen in it.

- KDL: [leapps.org/device-tools](https://leapps.org/device-tools#section-kdl) and [GitHub](https://github.com/abrignoni/known-data-logger). There is also an iOS version in [its own repository](https://github.com/abrignoni/known-data-logger-ios) that you build yourself with Xcode.
- AppWalk: [leapps.org/device-tools](https://leapps.org/device-tools#section-appwalk) and [GitHub](https://github.com/abrignoni/appwalk).

Give them a try and tell me what you find. Issues and pull requests are always welcome.
