---
title: "Telegram on Both Sides: New iOS and Android Coverage in iLEAPP and ALEAPP"
date: 2026-08-04
author: Alexis Brignoni
tags: [iLEAPP, ALEAPP, Telegram, iOS, Android, Settings, DFIR]
excerpt: Telegram now has fifteen artifacts across iLEAPP and ALEAPP, covering accounts, chats, contacts, cached profiles, and the app settings that tell you whether media ever touched the device. Here is what we added, what it proves, and the parts we could not validate.
---

# Telegram on Both Sides: New iOS and Android Coverage in iLEAPP and ALEAPP

Telegram has a reputation for being the private one.

That reputation is doing a lot of work. For regular chats, the message history sits on the device in a local database that is not encrypted at rest, on both iOS and Android. The app protects things in transit and it protects secret chats differently, but the pile of records left behind on the phone is very much readable if you know the format.

So we went and learned the format. Both formats, because iOS Telegram and Android Telegram share almost nothing structurally. Same app, same icon, two completely different storage designs.

**Short version:** current iLEAPP source now has six Telegram artifacts for iOS and current ALEAPP source has nine for Android. Accounts, chats, contacts, cached profile details, and the app settings that tell you how media was handled. ALEAPP had no Telegram support at all before this. Not outdated support. None.

**Long version:** keep reading. The interesting parts are the settings and the things we deliberately did not ship.

## What is there now

On the iOS side, iLEAPP already had a messages parser, originally written by Stek29 (Victor Oreshkin) and updated over the years by James Habben and myself. Around it we added:

- **Accounts.** Which accounts are registered on the device, which one was active, the signed in user ID, production or test environment, and whether an app passcode lock was configured.
- **Chats.** The actual chat list, with the time of the last message, unread counts, whether a chat is pinned, and whether it sits in the main list or the archive.
- **Contacts and Peers.** Every cached peer, with a column that says whether the peer is genuinely in the user's contact list.
- **Cached Peer Details.** Profile bio or channel description, a contact's stored birthday, blocked state, common group count, and the per chat auto delete timer.
- **Settings.** Media auto download, Save to Photos, passcode, contact sync, notification, and privacy settings.

We also refreshed the message parser's action types. The list had gone stale at 44 entries while Telegram had moved on to 65, so twenty kinds of system event were being reported as "unknown." Those now have names. The payload fields have names too, so a call reads as a duration and an outcome instead of a couple of single letter keys.

On the Android side we started from nothing and shipped nine: Messages, Contacts, Users, Chats, Accounts, Peer Details, Chat Details, Auto-Download Settings, and Save to Gallery Settings.

## The settings are the part people sleep on

This whole line of work started because Geraldine Bly asked me a question. She wanted to know if we could find the Telegram settings that control auto download, and where images actually go once they are downloaded. Thank you, Geraldine. That question turned into a good chunk of this release, and it is a better question than it looks at first glance.

Here it is. A photo appears in a Telegram conversation. Did it ever land in the device gallery?

That is not a question the message record answers. It is a question the settings answer, and Telegram stores them per network type and per category of chat. Auto download can be on for contacts and off for channels. It can behave one way on Wi-Fi, another on mobile data, another on roaming, with separate size limits for photos, video, and documents. Save to Photos on iOS and Save to Gallery on Android are their own separate settings on top of that.

Both platforms now report all of it.

Now the part that matters more than the parsing, and this is my soapbox moment, I always have one.

**Telegram does not write a settings record until the user changes it.** On both platforms. If a user never touches the auto download screen, there is no key in the database at all. Zero. Nothing.

So if your tool sees no key and prints "off," your tool just invented evidence. The absence of that key means the app default was in effect, and the app default is not always off. Our artifacts say "not present in database (app default in effect)" and "not set (app default, off)" precisely because those two states are different and an examiner deserves to know which one they are looking at.

That distinction cost us nothing to implement and it is the single thing in this whole release I would most want people to take away.

## Cached is not the same as known

One finding worth calling out, and credit where it is due, this came out of reading Belkasoft's iOS Telegram research.

Telegram caches a peer record when it encounters an account. Global search results get cached. So a peer sitting in that table does not mean the user ever talked to them, and it does not mean the user saved them as a contact.

In one of our test images, 275 of 296 cached peers had zero messages.

Both platforms now separate this properly. On iOS we read the actual contact table and flag membership directly, so you can tell a saved contact who was never messaged apart from a name that showed up in a search result once. That is a meaningful difference if you are writing about who somebody knew.

## Android hands you a call log if you ask it nicely

Android stores system events as service messages inside the message table. Group created, screenshot taken, history cleared, auto delete timer changed, and phone calls.

Before this work those all rendered as one flat, useless label. Every one of them looked identical in the report.

We mapped all 107 action constructors, which cover 68 distinct event types, and read the detail fields for the ones that carry them. On one test image, five rows that previously said nothing at all became four phone calls with outcomes and durations, plus a contact joining Telegram.

If you want the whole catalog, every system event Telegram can record on either platform is written up in the companion piece, [Telegram System Events: The Cross-Platform Reference](https://www.leapps.org/blog-post?post=2026-08-04-telegram-system-events-reference). It exists because the two clients name the same events differently, and matching the lists by name alone pairs only 27 of roughly seventy.

Here is why I trust that result. The decoded call outcomes lined up with the conversation happening around them in the chat. The participants discuss making an audio call, then failing to reach each other, then giving up on video, and the decoded records show a completed call, then a missed one, then two busy ones. Two unrelated parts of the same database telling the same story.

That is verification and validation in practice. Not "the code ran without crashing." Two independent sources agreeing.

## Now the part nobody puts in a release announcement

Nobody tells you what they are missing. So let me tell you what we are missing.

There are five capabilities in this work that we could not validate against real data, because none of the eight test images we had contain the thing they parse:

1. **Drafts.** Both platforms store unsent drafts. Every draft field in every image we have is empty. We decoded the structure and shipped nothing, because a draft recovery feature we cannot demonstrate is a claim, not a capability.
2. **Deleted and edited messages.** We wrote the carver. We ran it. The free pages held no recoverable message records, and every prior version sitting in the write ahead log was read state churn with byte identical text. Zero deletions, zero edits. The logic works. The evidence to prove it does not exist in our corpus, so we did not ship a deletion recovery claim.
3. **Group membership events** on Android, which carry the user IDs added or removed.
4. **Group and channel detail records.** We have exactly one across six Android extractions.
5. **Blocked contacts.** The field is read correctly. No test image has anybody blocked.

Items three through five are implemented and covered by round trip tests that encode the structures per Telegram's own serializers and confirm we read back what was written. That verifies the code against the documented format. It does not verify it against a real phone, and the test file says so in plain language rather than implying otherwise.

If you are wondering why I am listing our own gaps in a post announcing the work, it is because a tool that only tells you what it found is half a tool. You need to know where the floor ends.

**And this is where I ask for help.** One Android extraction with real group activity and some known deleted messages would let four of those five graduate from "we believe this works" to "we have proven this works." If you have a research image like that and you can share it, please reach out. That is the actual bottleneck, not code.

## Go get it

Current source for both tools has everything above.

If you find something wrong, tell us. If you find a Telegram record we do not parse, send a pull request, we will be happy to entertain it. And if you have research images to share, that is the contribution that unblocks the rest of this.

Good stuff. Go validate your tools.
