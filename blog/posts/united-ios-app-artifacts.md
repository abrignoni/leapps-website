---
title: A Trip Through the United iOS App
date: 2026-07-15
author: James Habben
tags: [iLEAPP, iOS, artifacts, United, travel, research]
excerpt: A look at United Airlines iOS app research in iLEAPP, including where the data lived, which rabbit holes mattered, and why nearby app/plugin data can change the shape of the parser.
---

# A Trip Through the United iOS App

If you spend enough time in mobile forensics, you eventually notice the same pattern. Someone asks, "Do we have a parser for this app?" The answer is a shrug, a sticky note, and then someone opens a backup "just to look around."

This was one of those looks.

United Airlines' iOS app turned out to be a good example of how app research typically goes. It was not a straight line from "app exists" to "build a module." It was more of a wandering tour through Core Data, preferences, DRM leftovers, a misnamed log file, and a few rabbit holes I deliberately walked away from.

That is part of why I like working in the LEAPPs ecosystem. We are not just writing artifact modules for a tool. We are sharing the research notes behind them so the next person has a better place to start. The module is at [united_airlines.py in iLEAPP](https://github.com/abrignoni/iLEAPP/blob/main/scripts/artifacts/united_airlines.py).

## Starting where the data lives

I usually start app research by getting my bearings. What bundle names exist? Which containers are present? Are the interesting files in the app container, the App Group, plugins, or somewhere else entirely?

In this case, the United customer app shows up under the bundle name:

```text
com.united.UnitedCustomerFacingIPhone
```

That is easy enough to confirm in LAVA by filtering the iLEAPP installed apps output.

![LAVA installed apps output filtered to the United iOS app](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/united-ios-app-artifacts/lava-united-installed.png)
*Figure 1: United app metadata in LAVA's installed apps output*

From there, I opened the extraction in [Crush Forensics](https://github.com/kalink0/crush-forensics). Crush has become really handy for this kind of first-pass app research because it can recognize encrypted and decrypted logical extractions and show logical path names instead of making you work backward from SHA1 backup filenames.

That saves a lot of time when you are searching broadly. Instead of searching the Manifest database, finding a file ID, and then jumping to the physical filename, you can search for the bundle name and inspect the app paths directly.

![Crush Forensics search results for the United app bundle name](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/united-ios-app-artifacts/crush-united-search.png)
*Figure 2: Searching for the United bundle name in Crush Forensics*

For most iOS app research, the common places to check are the AppDomain and AppDomainGroup folders. The app container usually has the noisy stuff: settings, preferences, caches, frameworks, analytics, marketing content, and whatever else the app brings along for the ride.

![Crush Forensics showing the United AppDomain folder](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/united-ios-app-artifacts/crush-united-app-folder.png)
*Figure 3: The United AppDomain folder*

Sometimes it helps to step back and look for the folders that tend to produce useful artifacts instead of trying to parse every shiny thing at once.

![Crush Forensics showing notable folders in the United app container](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/united-ios-app-artifacts/crush-united-app-folder-2.png)
*Figure 4: A second look at potentially useful United app folders*

The App Group was smaller, but it mattered. That is where the better structured data was hiding.

![Crush Forensics showing the United App Group folder](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/united-ios-app-artifacts/crush-united-group-folder.png)
*Figure 5: The United App Group folder*

The main file I focused on was a Core Data SQLite database:

```text
UnitediPhoneCoreData.sqlite
```

It was only about two megabytes in my test data, which is small enough to be friendly and large enough to be interesting. That is usually the moment the research shifts from "what files are here?" to "which tables are worth caring about?"

Account and loyalty fields were there, as expected: name, MileagePlus number, elite status, club membership, and the kinds of profile facts you would expect from an airline app. Useful. Necessary. Not the part that made me sit up.

## Saved travelers and trip passengers

This was the fun part.

When you use an app, you get a feel for the features before you ever look at the database. Then, when you start digging, you can ask better questions. In my [Home Depot app post](https://leapps.org/blog-post?post=home-depot-ios-artifacts), for example, I knew the app showed purchase history, so I went looking for it locally. I did not find it, which was its own useful finding.

With United, saved traveler data was something I hoped would be local because it is available in multiple places in the app. It was. United keeps a **saved travelers** list on the user profile, stored in the `ZUACDUSER` table in a column named `ZSAVEDTRAVELERSJSON`.

In my data, that included names, dates of birth, and traveler types.

![Crush Forensics showing United saved traveler JSON](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/united-ios-app-artifacts/crush-united-saved-travelers.png)
*Figure 6: Saved traveler data in the United Core Data store*

Then I looked at an active wallet reservation in `ZUACDWALLETRESERVATION` and pulled apart the larger `ZJSON` blob attached to the trip.

I had a small laugh when I saw an `isCEO: false` value in there. It is a good reminder that this is client-side data. That field is not a magic server-side authority switch. It is data the app can use to change behavior or presentation locally after it receives a response from the service.

![Crush Forensics showing United trip passenger JSON](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/united-ios-app-artifacts/crush-united-trip-passengers.png)
*Figure 7: Trip passenger data inside reservation JSON*

That JSON is basically an API-shaped PNR payload. Inside `pnr.passengers[]`, the app had a richer picture of who was actually on that trip. In the samples I reviewed, the trip passenger data could include MileagePlus IDs and Known Traveler Numbers when the app had them for those passengers.

So the module keeps those as two related artifacts on purpose:

- **Saved Travelers**: people stored in the user's profile for future booking
- **Trip Passengers**: people attached to a reservation, with trip-specific identifiers when present

That distinction matters. A saved traveler list can help answer "who has this person stored or booked for before?" A trip passenger list answers "who was on this itinerary, and what identifiers were carried with that reservation?"

If we only parsed the obvious saved-traveler data, we would leave part of the story on the table. That is the kind of finding that makes parser work feel worth it. The schema was not exotic. The important part was noticing that two nearby objects looked similar but did not mean the same thing.

## Trips, searches, and travel-day leftovers

Once you are in the Core Data store, the rest of the travel story starts filling in.

The module pulls several expected airline-app artifacts, including:

- Active and past wallet reservations
- Trip segments
- Mobile boarding passes
- Cached PNR documents
- Recent booking searches
- Flight status, or FLIFO, lookups

None of that is especially shocking, but it is solid travel context: routes, dates, flight numbers, record locators, and the other details you would expect to matter when reconstructing travel.

I also found Apple Watch complication data in the group preferences. In my testing, I did not have a paired Apple Watch sample to lean on, so I am treating that as an early note rather than a full story. Even so, those compact trip summaries may become useful corroboration when the phone and Watch have been talking.

And then there was this file:

```text
Documents/logFile.txt
```

Spoiler: it is not really a text log.

In my sample it was roughly nine megabytes of concatenated JSON boarding and travel-day status snapshots. Gates, boarding times, flight numbers, record locators, and the whole travel-mode pulse of the app were sitting in there.

It was also repetitive. Very repetitive. On this backup, much of it circled around one older PNR, which is both useful and a warning. It can be great for timeline context, but it is not a clean "one row per flight" kind of source.

In an older 2022 extraction I checked, this file did not exist. In this sample, the dates in the file were current and went back to 2024. Will it stick around forever? Who knows. That is app research. If the source is useful and present in the data, I would rather parse it with appropriate caveats than pretend it was not there.

![Crush Forensics showing the United logFile.txt JSON data](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/united-ios-app-artifacts/crush-united-logfile.png)
*Figure 8: The misnamed United logFile.txt source*

## Rabbit holes I left alone

This is the part that rarely makes polished release notes, and it is half the fun of app research.

### DRM bins

Deep under the app Library folder, I found a hash-named tree with `BLACK/` and `GREY/` `.bin` files. Dozens of them. Opaque names. Serious-looking layout. You can see that folder structure in Figure 4.

They turned out to be Intertrust ExpressPlay / Marlin DRM license objects for inflight entertainment and protected media. Not trip data. Not passenger data. Not something a travel parser should pretend to decode.

Same story for related Inplay DRM proxy caches. Interesting from a "what is this app doing?" perspective, but not useful enough for this module.

### Empty wallets and missing files

There were Couchbase Lite mobile wallet databases present in the app data, but they were empty in my sample. `Documents/Consumer.sqlite` appeared in the Manifest but was missing from the decrypted output.

That happens sometimes. Schema without rows. Paths without payloads. A little forensic confetti, but not something worth turning into an artifact yet.

### Car rentals, maps, and marketing data

I also saw CarTrawler cache data, facility map tiles, carousel tables, and catalog-style content. They were real, but they were low value for the questions I cared about while building a United travel artifact module.

Parsing all of that would make the output larger without making the case any clearer. That is usually a good sign to put the shovel down.

## A side quest worth keeping

One rabbit hole did earn a seat on the plane: inflight movies.

If you have ever wondered whether the United app remembers what someone watched through the inflight entertainment stream, the answer in my sample was: kind of, yes.

Preferences stored resume keys, including truncated `.mpd` and `MOV_*` asset names mapped to playback positions in seconds. Core Data also had an inflight media table with title, media ID, and timestamp data.

Put together, those sources can give a usable watched-or-resumed picture without trying to reverse DRM license blobs.

Is that the headline forensic artifact? Probably not. But it can be a useful supporting detail when you are reconstructing a travel day, especially if you are trying to understand what the app was doing while someone was in motion.

## One more find while writing

This is why I like writing these posts while the research is still fresh.

While reviewing the screenshots and file listings for this blog post, I noticed the United iMessage extension data. That sent me back into the extraction to look at the MobileSMS plugin metadata cache.

The useful source was a plist under `Library/SMS/PluginMetaDataCache` for the United iMessage balloon plugin:

```text
com.united.UnitedCustomerFacingIPhone.UnitedCustomerFacingIMessageExtension
```

That cache can include phone numbers for people the United iMessage plugin has been used with, such as when sharing flight information through Messages. It is not message content, and it is not proof of what was sent. It is a cached set of handles tied to that plugin.

Even so, it is a good example of how app research tends to grow sideways. The main app container and App Group told one part of the story. The Messages plugin left a smaller, related trace nearby. I added it as **United - iMessage Recipients** because it can provide useful context without pretending to be more than it is.

## What the module provides

The result lives in iLEAPP as:

```text
scripts/artifacts/united_airlines.py
```

The current module includes artifacts for:

- **United - Account**
- **United - Saved Travelers**
- **United - Trips**
- **United - Trip Passengers**
- **United - Boarding Passes**
- **United - PNR Documents**
- **United - Booking Searches**
- **United - Flight Status Searches**
- **United - Boarding Status Log**
- **United - IFE Watch History**
- **United - Watch Complications**
- **United - iMessage Recipients**

The account profile is there because examiners expect it. The pieces I was most interested in were the traveler/passenger split, the trip JSON mining, the misnamed boarding status log, the inflight media history, and the late-discovered iMessage plugin cache.

![iLEAPP finish screen showing United artifact record counts](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/united-ios-app-artifacts/ileapp-united.png)
*Figure 9: iLEAPP finish screen showing United artifact record counts*

Once parsed, the data can be reviewed in [LAVA](https://leapps.org/releases) like any other iLEAPP output.

![LAVA showing United trip artifact output](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/united-ios-app-artifacts/lava-united-trip.png)
*Figure 10: United trip details shown in LAVA*

## Why share it this way

Open source DFIR works better when the research notes travel with the code.

I have looked at tool output plenty of times and wondered where a parsed value came from. I have also wondered what might be missing. This kind of post is one way to answer both questions in the open. Here is what I found, here is what I chose to parse, and here is what I chose not to parse yet.

I have not personally found another tool parsing this United app data yet. If you know of one, I would be happy to compare notes.

For now, take this module as a head start. You can review the [module code](https://github.com/abrignoni/iLEAPP/blob/main/scripts/artifacts/united_airlines.py). Test it against more samples, find the weird edges, and contribute back when you can. Airline apps are busy little things, and I am sure this one still has a few layovers left in it.
