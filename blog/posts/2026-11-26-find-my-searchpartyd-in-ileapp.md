---
title: Find My in iLEAPP, building on Josh Hickman's Lost Apples
date: 2026-11-26
author: Alexis Brignoni
tags: [iLEAPP, iOS, Find My, searchpartyd, AirTag, Lost Apples, DFIR, open source]
excerpt: Josh Hickman worked out how the encrypted Find My files in searchpartyd fit together. We checked the findings we could test against nine extractions, and they held. iLEAPP now reads those stores too, with a few more artifacts, the write-ahead log read state by state, and the daily addresses each item broadcasts.
---

# Find My in iLEAPP, building on Josh Hickman's Lost Apples

![Headline: Read every state. On the left, an AirTag, a glossy white disc with a silver rim and labelled AirTag, sends out green signal arcs. A dotted line runs to a padlock in the middle, its shackle open and its body covered in small squares, with a green key turned in from below. Another dotted line runs to a stack of map sheets fanned out on the right, one behind the other. The front sheet has a green frame and two green pins. The sheets behind it are crowded with red pins. Under the stack: 2 at the head. 840 across the log.](/blog/images/2026-11-26-find-my-searchpartyd-in-ileapp/find-my-searchpartyd-hero.webp)

If you have looked at an AirTag case on an iPhone, you have probably read Josh Hickman. Over four posts on The Binary Hick he worked out where Find My keeps its data in `/private/var/mobile/Library/com.apple.icloud.searchpartyd/`, how it is encrypted, where the keys live and what the records say. Then he wrote Lost Apples, a free tool that does the decrypting for you. If you have not read the posts, start there:

- [Where The Wild Tags Are & Other AirTag Stories](https://thebinaryhick.blog/2024/09/02/where-the-wild-tags-are-other-airtag-stories/) (2024)
- [Further Observations, More on iOS Search Party](https://thebinaryhick.blog/2025/08/19/further-observations-more-on-ios-search-party/) (2025)
- [Endtroducing Lost Apples](https://thebinaryhick.blog/2025/11/30/endtroducing-lost-apples/) (2025)
- [Old Dog, New Tricks, Lost Apples 2.0](https://thebinaryhick.blog/2026/03/22/old-dog-new-tricks-lost-apples-2-0/) (2026)

This post does two things. It says what we found when we checked Josh's work against our own extractions, and it walks through what iLEAPP now reports from the same files, with a focus on what you can do with each one.

## What we checked, and what held

We ran nine iOS full file system extractions, iOS 16.5 to 26.5.2, each with its keychain. Most of them are public: Cellebrite CTF images from 2023 to 2026 and Josh's own iOS 17 image. Everything below was measured on those nine.

The `.record` files are what Josh said they are. Each one is a binary plist holding a nonce, a tag and the ciphertext, and it opens with AES-GCM using the BeaconStore key from the keychain. Every record of the types iLEAPP reads opened, on all nine. Josh also said the key moved: older iOS keeps it in the item's GenericAttribute, and iOS 17.5 and later keep it in the item's data. Our images split the same way. The key was in the attribute on 16.5, 17.1.1 and 17.3, and in the data from 17.5.1 on.

The databases are SQLite Encryption Extension stores, AES-256 in OFB mode, as Josh worked out. Pages are 4096 bytes, the last 12 bytes of each page hold its IV, and bytes 16 to 23 of the first page are not encrypted. Every one of the 37 database files on the nine images decrypted that way and passed SQLite's integrity check. Each store has its own key in the keychain. Most are named after the file, with two exceptions: `ItemSharingKeys.db` uses the KeyDatabase item, and `CloudStorage_CKRecordCache.db` uses CloudKitCache.

Josh said to read `Observations.db` with its write-ahead log, because the log holds records the main file does not. That held on every image that had advertisements at all. He also said the database throws records away fast, and the data agrees. Take the CTF 2024 Otto image. Opened the usual way, with the log applied, its location table shows 2 rows. Opened without the log, it shows 834. Reading every committed state in the log, one at a time, gives 840. So the advice goes one step further: read the database with its log, without it, and at every state in between.

And the times are UTC. The `scanDate` in `Observations.db` is stored as text with no zone. Read as UTC, it matched the time in a BeaconEstimatedLocation record of the same beacon to the millisecond on 22 advertisements across six images. None matched a whole number of hours off.

Plenty of what Josh found we did not test, so this post does not vouch for it either way. That includes when the MAC addresses rotate, the nearby and separated key states, the ItemSharingKeys values that may predict a shared tag's future MAC addresses, how long unwanted tracker alerts stay on the phone, and what the rssi value says about distance.

## What iLEAPP reports

All of this sits in one iLEAPP module. You need a full file system extraction and the keychain. If the keychain ships inside the extraction (UFED does this), iLEAPP finds it. If it comes as a separate file, as GrayKey's does, pass it with `--keychain`. Without the keychain the files stay encrypted, and the log says which ones were not read.

### Where were the items?

Find My Beacon Estimated Locations has one row per location record of each item on the account, with the item's name next to it. This is the item's own location history, and it is often the first table to look at. Josh's caution applies here: a location for the owner's item does not show that this phone was there, since another device on the account may have seen it.

Find My Owned Beacons lists the items paired to the account, with the pairing date, the model, the latest estimated location time and how many location records each item has.

### Who shared an item with this person?

Find My Shared Beacons lists the items shared with the account, with the share date and the owner handle, which Josh reads as the person who shared it. Josh noted that shared items are not in the BeaconNamingRecord folder, and on our images they were not. Their names were in `ItemSharingKeys.db`, in a table called BeaconAttributes. iLEAPP now reads that table, so a shared item shows its name and emoji instead of a blank. On Josh's iOS 17 image that filled in 7 of 14 shared items. The same names now reach the location artifacts.

### Did an unknown tracker travel with this phone?

Find My Unwanted Tracker Alerts has one row per alert record, with the trigger time and the first and last location times. Find My Unwanted Tracker Locations lists every location in those records, one row each, ready for the map. Josh's warning about the first location stands: the tracker may have been with the person before the phone started counting.

Find My Observed Advertisements lists the Find My advertisements the phone recorded that have a location. Josh reads that location as where the phone was when it recorded the advertisement. A row that names a beacon is an item on the account. For a row that names no beacon, the database records no beacon, and what sent it is not something the database tells us. Josh's advice for those rows is to look for the same MAC address over a day or so, since the address rotates. The MAC address, the raw advertisement bytes and the rssi value are all in the table for that.

### What came back from the log

This is the biggest change from reading the database once with its log. iLEAPP reads every committed state in the write-ahead log, one at a time. An advertisement that an older state holds and the current one does not comes back as a Recovered row, and the Recovery Location column says which states held it. On the Otto image above, that is 838 Recovered rows next to 2 Live ones.

### When the phone recorded the owner's own items

`Observations.db` also fills up with the owner's own items, recorded over and over, often with no location. On the CTF 2024 Felix image, 1,833 of its 1,856 advertisements had no location, and every one of those 1,833 named one of the owner's items. Listed one by one, rows like that bury the rest. So iLEAPP counts the advertisements without a location per item per UTC day in Find My Observed Advertisement Days: the first and last time recorded, how many, and the rssi range. Advertisements with a location stay one row each.

### What addresses did the owner's items broadcast?

This one builds directly on Lost Apples 2.0. Find My Beacon Daily Addresses takes each owned item's record and works out the MAC address and advertisement key the item broadcasts each day when it is away from its owner. It follows the key chain Josh lays out from Apple's accessory specification, and lists one row per item per day, from pairing to the latest time the store holds. Only those derived values go in the report. The item's private key and shared secrets do not.

We checked the math against what the phones themselves stored. On the CTF 2025 Dexter image, all 59 addresses the phone stored for two of its items equal addresses derived from their records, and the stored advertisement data matches the derived keys byte for byte. Most of those 59 came from the 15-minute keys an item uses near its owner, and 3 were daily ones.

The dates are estimates counted from the pairing date. Josh notes the secret can be replaced after pairing, and on Dexter the recorded keys ran 2 days ahead of the estimate. Where the phone did store an address, the row shows when, and that is the time to trust.

What it is for: take the list from a suspect's phone and search the victim phone's Observed Advertisements or Unwanted Tracker Alerts, or a Bluetooth detector export, for those MAC addresses or keys. The matching is yours to do, and a match or no match on its own does not show the item was there. Only items that hold a daily secret get rows: 6 of the 37 owned items on our nine images. Josh notes iPhones have none.

### The Find My caches

iLEAPP also opens the caches Find My keeps under `Library/Caches/com.apple.findmy.fmipcore` and `com.apple.findmy.fmfcore`, which newer iOS writes encrypted. Find My Devices Cache, Find My Safe Locations Cache and the rest of that family read them with the decryption PnutCN published in findmy-cache-decryptor. Devices.data lists the devices on the account, with a location on the records that hold one, so it is worth reading next to the searchpartyd artifacts.

## A short checklist

1. Isolate the phone at seizure. Josh's tests showed `Observations.db` clearing out records while Bluetooth stayed on.
2. Get a full file system extraction and the keychain. Josh found that backups and advanced logical extractions do not have this data.
3. Run iLEAPP with the keychain, then read the log. A line saying a file was not read usually means no key opened it. It does not mean the file was empty.
4. Start with Beacon Estimated Locations and the two Unwanted Tracker artifacts, then Observed Advertisements for the times and places the phone recorded other devices.
5. Check Record Origin in Observed Advertisements. A Recovered row is one the current database no longer holds.
6. If you have the suspect's phone too, run Beacon Daily Addresses on it and search the victim's report for those addresses.
7. For your own queries, the decrypted copies of the stores are in the report folder, under Decrypted searchpartyd.

## What iLEAPP does not do

Lost Apples 2.0 derives an item's keys and compares the resulting MAC addresses across phones for you. That is how Josh found a powered-off iPhone in a victim phone's `Observations.db`. iLEAPP lists the daily addresses, but it does not do the comparison, and it does not list the 15-minute keys an item uses near its owner. Those are what an iPhone has, since it has no daily key. Use Lost Apples for that.

We also do not say what sent an advertisement that names no beacon, or what the rssi value measures. Those columns are reported as stored. `CachedUnifiedBeacons.data` is not read yet.

## Thanks

All credit for the research goes to Josh Hickman, and to Ian Whiffin, who Josh credits with helping on the write-ahead log. The record layout was also published by denysvitali in searchparty-keys. iLEAPP cites both at a pinned commit.

These artifacts are in iLEAPP's main branch now and will be in the next release. iLEAPP is free and open source under the MIT license. If you have an extraction that does not parse the way you expect, or a test device with a shared item or an unwanted tracker alert on it, open an issue or send a pull request. We will be happy to take a look.
