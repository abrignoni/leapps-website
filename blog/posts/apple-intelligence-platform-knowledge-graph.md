---
title: Reading the iPhone Knowledge Graph, and Checking Its Work
date: 2026-09-23
author: Alexis Brignoni
tags: [iLEAPP, iOS, knowledge graph, Intelligence Platform, location, DFIR, research]
excerpt: Your iPhone quietly builds a knowledge graph about you: who you know, where you go, what you run. iLEAPP now reads it, and the inferred locations line up with a documented activity log on Josh Hickman's public iOS 17 image.
---

# Reading the iPhone Knowledge Graph, and Checking Its Work

![A dark diagram. An iPhone running the knowledged daemon emits coded facts labeled SB104, PS33, SB152, and SB764. They pass through a glowing panel labeled ontology.db and come out as the words person, name, place, and location visit, which form a small graph of Person, Place, Location visit, and Software nodes. One place node carries a check mark reading confirmed against known data.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/apple-intelligence-platform-knowledge-graph/knowledge-graph-header.webp)
*Figure 1: The phone stores the graph as coded facts. The on-device ontology turns the codes into words, and the resolved places can be checked against known data.*

Your iPhone runs a daemon called knowledged. It sits in the background and does exactly what the name suggests. It builds knowledge. Not files, not logs, but a graph of things the phone has decided are true about you. Who your contacts are. Where you have been. Which apps you run and who made them. It ties all of that together and stores it on the device.

Until now, no iLEAPP artifact read it. It does now. Three artifacts read it, in [intelligencePlatformGraph.py](https://github.com/abrignoni/iLEAPP/blob/main/scripts/artifacts/intelligencePlatformGraph.py), added in iLEAPP PR #2260 and extended in PR #2262.

## What the store looks like

The graph lives here:

```text
/private/var/mobile/Library/IntelligencePlatform/
```

The interesting file is `graph.db`. It stores facts as short three-part sentences: a subject, a link, and an object, plus a relationship id, a confidence score, and a timestamp. "This thing is a person." "This person has this name." "This person was at this place on this date."

The catch is that the phone does not write those sentences in English. It writes codes. The links and the categories come out as short strings (PS.., SB.., CS..) that tell you nothing on their own.

That is where the second file earns its place. Sitting in the same folder is `ontology.db`, and it is the decoder ring. It maps every code to a human-readable label:

- `PS33` = name
- `PS1` = is a
- `SB104` = person
- `SB152` = place
- `SB764` = location visit activity

and so on down the list. Because that mapping is read from the same device that produced the graph, it is exact for whatever built that store. We are not guessing what a code means. We are asking the phone that wrote it, which is pretty neat. Working out what those codes mean is the core of 0x11 Forensics and Consulting's research on this store, which walks through the same resolution in detail.

## Three artifacts

**Intelligence Platform Knowledge Graph - Entities** gives you one row per inferred entity. Entity types resolve to person, organization, place, and software.

- People carry a resolved name, first and family name, aliases (an "also known as" gathered from several signals), phone numbers, emails, contact labels, and external identifiers.
- Places carry a street address plus latitude and longitude. The artifact writes KML, so the places plot on a map.
- Software carries a bundle id and a developer.

**Intelligence Platform Knowledge Graph - Events** gives you a dated timeline of inferred events, mostly location-visit activities and calendar events, each with an estimated start and end time.

**Intelligence Platform Knowledge Graph - Interactions** reads a separate store in the same area, `view.db`, under `Artifacts/siri/remembers/`. This is the graph's own record of messages and calls: the contact handle or handles, the app bundle id, the direction (as stored), and the call duration. On the Hickman iOS 17 image it holds 559 messages and 20 calls, out of 2,835 interaction rows in all. It sits next to the per-app message and call databases, so it can back them up, and it can outlast them.

## What outlives the live record

The graph does not only keep what it believes right now. It also keeps a set of expired tables, `expired_stable_graph` and `expired_event_graph`, holding entries it has retired or replaced. The Entities and Events artifacts read those tables too, and tag each row with an "Expired" column so you can tell a live entry from a retired one.

That is where a full filesystem acquisition earns its keep. Across five public corpora the expired tables gave up 508 events and 40 entities the live tables no longer show, and one public iOS 18 image alone held 478 historical location visits in the expired set. Inferred people, places, and visits can survive there after the device has dropped them from what it shows today.

## Say the boundary out loud

Two things, plainly.

First, availability. The `graph.db` file starts showing up on iOS 16, but on the images we tested it is empty there. It is populated on iOS 17 and later. If you are on iOS 16 and the store is empty, that is expected, not a parsing failure.

Second, and this is the one that matters. Everything in here is worked out by the system. A row is not a statement that the user created something, confirmed it, or was present for it. The phone decided it, from signals, with a confidence score attached. Treat it as a lead, not a finding. Values are reported as stored.

That caution is not decoration.

## Checking the work

A guess is only worth as much as what you can check it against.

Josh Hickman publishes research images, with documentation, for exactly this kind of work. His iOS 17 image is public: an iPhone 11 acquisition running iOS 17.3, available on [Digital Corpora](https://digitalcorpora.org/corpora/mobile/ios_17). Better still, he writes down what he actually did on the device while creating it, in a [documentation PDF](https://thebinaryhick.blog/wp-content/uploads/2024/08/iOS17-ImageCreation.pdf). That gives us known data to check the graph against.

On that image, the Events artifact reports 49 events, almost all location-visit activities, with named places resolved to coordinates. It tells a story. Home in the Holly Springs, North Carolina area, then a trip to Washington DC across mid and late July 2024, with transit points on I-95 N and Garrisonville Rd along the way, and stops at the Capital Hilton, Pennsylvania Ave NW, F St NW, H St NW, and Arlington National Cemetery.

The graph's inferred places, set beside what Josh documented by hand:

| Artifact place entity (latitude, longitude) | Hickman's documented activity |
|---|---|
| Ancient Oaks Dr (35.661, -78.879) | "516 Ancient Oaks Drive, Holly Springs, NC" (Home) |
| Grand Hill Pl (35.660, -78.851) | Starbucks, "185 / 100 Grand Hill Pl, Holly Springs, NC" |
| Purfoy Rd (35.589, -78.773) | "7629 Purfoy Road, Fuquay-Varina, NC" |
| Starbucks (38.780, -77.235) | "Starbucks (8408 Old Keene Mill Rd, Springfield, VA)" |
| Best Buy (38.774, -77.170) | "Best Buy (6555 Frontier Drive, Springfield, VA 22150)" |
| 16th St NW (38.903, -77.036), event names it "Capital Hilton" | navigation to "1001 16th St NW, Washington, DC 20036" (the Capital Hilton's address) |

The phone independently recorded where it had been, resolved those places to street addresses and coordinates, and those inferred locations line up with an activity log a human wrote down separately. The Best Buy and the Springfield Starbucks match Josh's notes down to effectively the same street address. His notes describe the DC trip in words ("personal travel to DC", "I have DC twice this month") and a navigation to 1001 16th St NW, which is the address of the Capital Hilton, the very place the graph's event names.

This is a validation-against-known-data example you can reproduce. The module is in the iLEAPP repo. The image is public. Run one against the other and check the coordinates yourself.

A match backs up that the phone was at that place. It does not, on its own, prove the person was. The graph is the phone's best guess, and guesses get things wrong. What the match buys you is confidence that the graph is recording something real, plus a documented case where its output held up against known data. That is not the same as proof, and keeping the two apart is the examiner's job.

## Why this is worth having

Location visits, resolved people and places and software, messages and calls, and a set of retired entries a full acquisition can still reach. All of it inferred by the operating system, sitting in one store. That is a rich source, and it was going unread. Now it is not.

Grab the [module](https://github.com/abrignoni/iLEAPP/blob/main/scripts/artifacts/intelligencePlatformGraph.py), point it at the Hickman image or your own data, and check its work. Verify and validate, always. If you find edges where a code does not map cleanly, or one the lookup file does not cover, that is exactly the kind of thing worth a pull request.

0x11 Forensics and Consulting reached this same store on their own and documented it well in ["That is one smart Apple"](https://0x11forensicssc.com/f/that-is-one-smart-apple): the ontology resolution, the expired tables, and the `view.db` interactions. I came across their write-up while this work was underway, and it lines up with what these artifacts pull, so read it alongside this. There is more in that folder than these artifacts read today, such as `lifeEventView.db` and `behaviors.db`, so consider this ongoing work. Thanks to them, and to Josh Hickman, whose public image and documented activity make the check above possible. Open source DFIR works because people share both the data and the notes behind it.
