---
title: Nineteen New Unified Log Artifacts for iLEAPP and DLEAPP
date: 2026-10-03
author: Alexis Brignoni
tags: [iLEAPP, DLEAPP, iOS, macOS, unified logs, artifacts, research]
excerpt: Six new unified log artifacts for iOS in iLEAPP and thirteen for macOS in DLEAPP, what each one was measured on, and what none of them can tell you. Also why the iOS queries could not simply be copied over to the Mac.
---

# Nineteen New Unified Log Artifacts for iLEAPP and DLEAPP

![A seismograph trace on a dark chart. Grey noise runs along the baseline, broken by nineteen sharp spikes: six in red labelled 6 iOS and thirteen in purple labelled 13 macOS. A recording arm rests at the end of the trace. Small text reads: it records the shake, not who shook it.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-03-unified-log-artifacts-ileapp-dleapp/unified-log-artifacts-hero.webp)

*Figure 1: nineteen new signals pulled out of the noise. The log records the shake, not who shook it.*

The Apple unified log is the noisiest witness on the device. Millions of entries, most of them a process talking to itself. Somewhere in there are the few lines that say a button was pressed, a passcode field came up, a disk was mounted or somebody ran sudo.

On October 3 two pull requests went in that pull more of those lines out for you:

- [iLEAPP #2326](https://github.com/abrignoni/iLEAPP/pull/2326) adds six iOS artifacts and updates two existing ones.
- [DLEAPP #521](https://github.com/abrignoni/DLEAPP/pull/521) adds thirteen macOS artifacts.

This post covers what they report, what they were tested on, and, just as important, what they do not establish. Tim Korver's [Anchored Log Reconstruction](https://thesisfriday.com/alr/) method opens with the premise I want you to carry the whole way down: "A log entry records that a process observed something, not what a person did."

## Credit where it is due

This work stands on Tim Korver's unified log research. Tim writes [Thesis Friday](https://thesisfriday.com/), and if you work with unified logs you should be reading it. The search terms behind the six new iOS artifacts are his, and so are the markers the macOS Screen Unlock artifact looks for. His posts on [volume buttons](https://thesisfriday.com/thesis-friday-8-aul-physical-buttons-volume/), [USB and charger connections](https://thesisfriday.com/thesis-friday-9-aul-connecting-a-usb-cable/), [screen orientation](https://thesisfriday.com/thesis-friday-2-aul-device-orientation/) and [touch events](https://thesisfriday.com/thesis-friday-14-aul-touch-events/) are a good place to start.

I compared his terms with what iLEAPP already collected, and the gaps became the new artifacts. He did the research. The counts, the misses and any mistakes in the artifacts are mine.

## iLEAPP: six new iOS artifacts

All six read the unified log that iLEAPP already imports, from the tracev3 data in an extraction or from a `log show` JSON export.

- **Biometric match results.** The kernel's match result entries for Face ID and Touch ID, plus the coreauthd no-match entry.
- **Passcode field input.** The passcode text field becoming, and ceasing to be, the keyboard input target, with the process that showed it. That process separates the lock screen from a passcode prompt shown for another authentication.
- **Hardware button presses.** Button events with the HID usage and how long the button was held, side button press counts, and the button combination recognizer's press type.
- **Device orientation and pick-up.** Orientation changes and wake gesture notifications. High volume, so it goes to LAVA only.
- **System edge gestures.** Touches taken over by a system gesture, and the recognizers for the app switcher, Control Center and the Cover Sheet.
- **USB host connections.** Entries that separate a cable to a computer from a cable to a power source.

They were run on five images, iOS 12.4 to 26.5.2. Three are public: the Magnet 2020 CTF iPhone (iOS 12.4), the Cellebrite 2025 CTF iPhone (iOS 18.3.2) and the MSAB 2026 CTF iPhone 12 (iOS 18.7), all listed on [The Evidence Locker](https://theevidencelocker.github.io/). The iOS 17.2.1 and 26.5.2 images are test phones that are not public downloads.

Do not expect every artifact on every phone. The kernel match result entries were on the iOS 12.4, 17.2.1 and 18.3.2 images and absent on iOS 18.7 and 26.5.2. The passcode field entries were absent on iOS 12.4, and none of the USB host entries appeared on iOS 26.5.2. That is five phones, not a rule about iOS versions. It may not even be about the version: Tim [measured](https://thesisfriday.com/thesis-friday-28-what-a-busy-phone-forgets/) the kernel lines of an unlock gone from a phone in daily use within 13.2 hours, so an entry can be missing because the log no longer holds it. I did not measure retention on these images. The counts for each image are in each artifact's notes.

The button usages are not guesses. The pair at the start of a button entry is a USB HID Consumer Page usage: 0x30 is Power, 0xE9 is Volume Increment and 0xEA is Volume Decrement, per section 15 of the [USB-IF HID Usage Tables 1.5](https://usb.org/sites/default/files/hut1_5.pdf). On the iOS 18.7 image the combination recognizer's three press types each appeared exactly twice per press of the matching usage: 80, 26 and 66 entries against 41, 13 and 33 presses.

### Two existing artifacts changed

**Unlock sessions and method** now also collects the kernel "is now UN-locked" entry and the "Unlock attempt succeeded" entry. The kernel entry appeared on all five images, including iOS 12.4 and 17.2.1 where the older "apfs is being UN-locked" form did not.

Its notes also got a correction that I want to call out. The "Processed authentication request (success=YES)" entry with type 1 reads like a successful passcode unlock. Lionel Notari's [own post](https://www.ios-unifiedlogs.com/post/ios-unified-logs-unlock) shows that same entry is also written when the wrong passcode is entered, and points to "Unlock attempt succeeded: yes" or "no" as the outcome. That outcome entry did not appear on any of the five images. So on them, success=YES alone does not establish that the phone unlocked.

**Touchscreen events** gained the "Touch entered" entry. It appeared only on the iOS 26.5.2 image, 1,237 times.

A same-day follow-up, [iLEAPP #2327](https://github.com/abrignoni/iLEAPP/pull/2327) and [DLEAPP #532](https://github.com/abrignoni/DLEAPP/pull/532), widened the unlock artifacts on both platforms. They now collect every keybag state transition, not only the ones leaving "locked", and the kernel's volume lock and unlock notification. That came straight out of reading Tim's method posts against my own notes.

## The iOS queries do not port to the Mac

My first idea for DLEAPP was the lazy one: take iLEAPP's queries and point them at a Mac's log. Same logging system, same message text, right?

No. iLEAPP's queries match on message text, and on a Mac the same text comes from different processes, or does not come at all. I ran three of iLEAPP's queries, as they stood in #2326 and unchanged, against the logs of two public Mac images.

| iLEAPP query | iOS 17.2.1 | macOS 14.6.1 | macOS 15.4 |
|---|---|---|---|
| Wi-Fi status | 11,465 entries, wifid on top with 3,960 | 304 entries, configd on top with 111 | 573 entries, 511 of them from configd |
| Lock status | 1,252 entries from 16 processes | 111 entries from 8 processes | 735 entries, 714 of them from mediaanalysisd |
| Unlock sessions | 115 entries | 0 entries | 2 entries |

On the phone the top writer for the Wi-Fi query is wifid. On both Macs it is configd. The lock status query on macOS 15.4 is almost all mediaanalysisd. The unlock query returns nothing on macOS 14.6.1, a Mac whose log holds 524 lock and unlock related entries once you ask for them the macOS way. So DLEAPP got its own queries, nearly all of them tied to the process or subsystem that writes the entry on a Mac.

## DLEAPP: thirteen new macOS artifacts

These read the unified log table DLEAPP imports with Mandiant's [unifiedlog_iterator](https://github.com/mandiant/macos-UnifiedLogs). If that import did not run, they report nothing and say so in the run log.

- **Screen Unlock.** Keybag lock transitions, Touch ID match results, loginwindow password attempts and failed password checks. The markers come from Tim's [Thesis Friday #26](https://thesisfriday.com/thesis-friday-26-same-unlock-three-different-stories/), which reads "locked -> inBioUnlock" as Touch ID and "locked -> unlocked" as a password on macOS 26.6.2.
- **Authorization Rights.** authd rights granted or refused to a program, and the account whose credentials satisfied a right.
- **TCC Access Requests.** One row per privacy request, rebuilt by joining tccd's AUTHREQ entries on the message ID within one tccd process. LAVA only.
- **Gatekeeper Scans.** What syspolicyd scanned and the result value it logged.
- **Disk Arbitration.** Disks created, probed, mounted, unmounted and removed.
- **XProtect and MRT Scans.**
- **Shutdown and Reboot Requests.** With the account that ran the command.
- **sudo Commands.** The account, working folder, target account and command, as sudo wrote them.
- **Screen Capture Launches.**
- **iOS Device Connections.** usbmuxd connections and pairing attempts.
- **Sleep and Wake.** With the wake reasons the kernel and powerd logged.
- **USB Mass Storage.** Kernel USBMSC identifier entries.
- **Login Window Sessions.** Logins with the user ID, and logouts, restarts and shutdowns with their type.

They were tested on three public images: Josh Hickman's [macOS Big Sur image](https://thebinaryhick.blog/2021/02/20/ios-14-macos-big-sur-lots-of-images/) (macOS 11.2.1), the "Apple macOS" image by Cody Bounds on The Evidence Locker (macOS 14.6.1), and the unified log store of the Hexordia MacBook Pro from the 2026 Magnet Virtual Summit CTF (macOS 15.4). Their logs hold 3,024,846, 7,195,263 and 27,030,315 entries.

Only the macOS 14.6.1 image had rows for all thirteen. On the other two, sudo Commands, Screen Capture Launches, USB Mass Storage and iOS Device Connections had none, and the macOS 15.4 log also had no shutdown or login window rows. A zero there is a fact about that Mac's log, not about what macOS writes. The per-image counts are in each artifact's notes.

## What these artifacts do not establish

Every artifact's notes carry its limits. Here are the ones I would not want you to miss.

- **A biometric match entry is a match attempt by the sensor stack.** It does not say who was in front of the phone. It is not an unlock either: on his Mac, Tim [recorded](https://thesisfriday.com/thesis-friday-27-backward-reasoning-from-a-provable-endpoint/) successful Touch ID matches with the machine already unlocked and nothing changing state. The macOS 14.6.1 image has 17 match entries. Do not read them as 17 unlocks.
- **An empty table is not a finding.** Tim's [stop rule](https://thesisfriday.com/the-stop-rule/) says an empty result only counts if the log covers your time window for that kind of line. These artifacts find the entries someone has already described. When they stay quiet, go to the raw log.
- **The passcode field entries say the field was on screen.** They do not record the digits or whether the code was right.
- **Rows are not events.** Several processes write the same orientation, gesture and lock transition entry for one event. On the macOS 15.4 image, one unlock produced two "locked -> unlocked" rows from two processes.
- **An edge gesture entry says a recognizer began.** Not that the gesture completed.
- **A computer connection and a button press are also what an examiner's own handling produces.** On the macOS 14.6.1 image one subject, named like an acquisition tool, made 24,744 of the 39,067 TCC requests.
- **A failed password check is not proof that somebody typed a wrong password.** They were 437 of the 524 Screen Unlock rows on macOS 14.6.1. Tim's macOS run in that same post held password verification and authentication failure lines in a block where no password was typed at all. I have not tested which of these rows are that kind.
- **A scan entry says a scan ran.** No detection entry is selected.
- **A screencapture entry says it started.** Not that an image was saved.
- **A sudo row is not always a person at a keyboard.** Five of the seven on macOS 14.6.1 had a working folder inside an installer sandbox.
- **Values with no documented meaning are reported as stored.** That includes TCC's authValue and authReason, the Gatekeeper result number, and match values other than the ones the research describes. I did not name what I could not source.
- **Thesis Friday #26 was measured on macOS 26.6.2.** None of my three images is that version. No "locked -> inBioUnlock" appeared on any of them, and "locked -> unlocked" appeared only on macOS 15.4. The macOS 14.6.1 log holds 37 keybag transitions in other forms, such as "locking -> inBioUnlock", and the artifact reports them. That same post notes most of these lines are written at the info and debug levels, so a log collected without them carries few.
- **Shutdowns from the Apple menu were not tested.** The artifact selects the shutdown and reboot commands.

## Fixes that fell out of testing

Running DLEAPP on Mac images it had not seen before broke a few things that had nothing to do with logs. All five are merged.

- [#522](https://github.com/abrignoni/DLEAPP/pull/522) and [#525](https://github.com/abrignoni/DLEAPP/pull/525): a Spotlight parent identifier and FSEvents event IDs above the signed 64-bit range could not be written to the LAVA database, so those artifacts failed. They are now passed as text. FSEvents went from no table to 668,539 rows on the macOS 14.6.1 image.
- [#523](https://github.com/abrignoni/DLEAPP/pull/523), [#524](https://github.com/abrignoni/DLEAPP/pull/524) and [#526](https://github.com/abrignoni/DLEAPP/pull/526): a logical Mac extraction can hold the same file under the root, under System/Volumes/Data and under System/Volumes/Update/mnt1. Modules that read every copy reported records twice. A byte-identical copy is now read once. On the Magnet 2021 CTF macOS image the Install Log went from 39,741 rows to 19,890. Copies that differ are still all read.

## Try it

Both sets are on the main branch of [iLEAPP](https://github.com/abrignoni/iLEAPP) and [DLEAPP](https://github.com/abrignoni/DLEAPP) now. Run them against an image where you know what happened, compare, and tell me where they are wrong. If you have a log from an iOS or macOS version not listed here, I would like to know what the zeros look like on yours.

Thanks to Tim Korver for the research and for Thesis Friday, to Lionel Notari for the unlock research, and to everyone who publishes test images the rest of us can check our work against.
