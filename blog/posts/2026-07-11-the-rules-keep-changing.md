---
title: The Rules Keep Changing
date: 2026-07-11
author: Alexis Brignoni
tags: [iLEAPP, iOS, Biome, LLM, research]
excerpt: The first fully LLM-generated set of artifacts lands in iLEAPP: fourteen Biome parsers built from public community research and test data, 3,668 rows of previously unparsed data on the first clean pass. If coding is now accessible to everyone, what does that mean for tooling in digital forensics?
---

# The Rules Keep Changing

## Summary

Today I added the first fully LLM-generated set of artifacts to iLEAPP, built from test data and public community research. If coding is now accessible to everyone, what does that mean for software development, and for tooling, in digital forensics?

## Long Story

Yesterday, during the Digital Forensics Now Podcast (S3E3), we highlighted the work of Charlie Rubisoft on SEGB files from iOS. With iLEAPP being the first general open implementation of SEGB parsing (thanks to John Hyla, Geraldine Bly, and Alex Caithness), I was happy to showcase North Loop Consulting's tooling and reporting on the format. See the show for details. In short: really good stuff.

During the show we discussed how Charlie noticed that recent iOS hardware and software versions now keep SQLite databases inside the Biome directory. Any examiner worth their salt knows there is nothing more exciting than a new data structure in a known operating system. Lots of relevant data might be living in there. Being the expert examiner that he is, Charlie promised an article explaining the artifacts and their relevance. A well-placed Happy Gilmore reference on the show motivated him to publish the very next day. Read his research here: [Ready, Sets, Go](https://northloopconsulting.com/blog/f/ready-sets-go).

Earlier today I was doing app coverage research on iLEAPP (which apps get parsed versus which don't) using [Batch LEAPP](https://leapps.org/releases#section-batch-leapp). Batch LEAPP was coded with Claude.

What? Brigs using an LLM? Yes. From the beginning I have said these technologies will have a place in our workflows, as long as:

1. They are not used to generate analytical conclusions in matters that affect life, liberty, or safety.
2. They are used by experts.
3. Accountability for LLM output is clearly defined and understood by the expert using the tool.

My experience using Claude throughout the LEAPP modernization effort deserves a blog post of its own. The short version: I use LLMs and I find real value in them, including the generation of deterministic code that can be verified and validated. As a side note, I find this fascinating from a philosophical standpoint. In the same way that order is just a subset of randomness, stochastic methods can produce useful deterministic outcomes. Ironic, isn't it? Also true.

Back on topic. As I was working through Batch LEAPP coverage reports, tracebacks, and Claude-assisted fixes for failing artifacts, an idea presented itself: ask Claude to generate a complete iLEAPP artifact on its own and see what comes out. The data store to target was obvious: the newly documented SQLite databases in the Biome directory.

## How did Claude do?

I pointed it at Charlie's article and at test data from a public iOS 18.7.8 image in my corpus. It came back with fourteen artifacts covering both storage locations from the research: the pre-aggregated Biome databases (per-launch app openings, hourly launch counts, cable plug events, backlight events, daily button clicks, minimum battery, CarPlay activity, and the Intelligence Platform entity graph) and the protobuf-based Set.db stores (installed apps, contacts, FindMy devices, significant locations, and per-app Shortcut phrases and entities). Every table lookup is guarded because these schemas change between iOS versions, timestamps are stored as UTC, unmapped protobuf fields are preserved instead of dropped, and every artifact credits the original research in its notes.

All fourteen ran clean against the test image on the first full pass. That is 3,668 rows of previously unparsed data. The work is up as [iLEAPP PR #1693](https://github.com/abrignoni/iLEAPP/pull/1693). See for yourself:

![Per-launch app openings from the ApplePay.Security.Features Biome database](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-11-the-rules-keep-changing/Biome_DB_-_App_Openings.png)
*Figure 1: Per-launch application activity from the ApplePay.Security.Features Biome database. 407 launch records with bundle ID, UTC event time, and launch type.*

![Installed apps from the App.InstalledApp Set.db store](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-11-the-rules-keep-changing/Biome_Sets_-_Installed_Apps.png)
*Figure 2: Installed application records recovered from the App.InstalledApp Set.db store, with per-record modified timestamps.*

![A significant location decoded from a protobuf payload](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-11-the-rules-keep-changing/Biome_Sets_-_Significant_Locations.png)
*Figure 3: A significant location (label, street, area, city, and country) decoded from a protobuf payload inside the Location.SignificantLocation Set.db store.*

![Siri and Shortcuts phrases registered per application](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-11-the-rules-keep-changing/Biome_Sets_-_App_Shortcut_Phrases.png)
*Figure 4: Siri/Shortcuts phrases registered per application, showing which intents installed apps exposed to the system.*

Was it hands-off? No, and that is exactly the point. I reviewed the schemas it inferred against the actual databases, checked the timestamp conversions, and validated row counts against manual queries of the source data. The LLM wrote the code; the examiner owned the verification. That division of labor is the only version of this workflow I will vouch for.

## What does this new reality mean?

Research automation through coding is a skill that built billion-dollar companies. It is also a skill gap that made most examiners dependent on tool providers for parsing. With the advent of LLMs, coding has been democratized to a large extent. Anyone can now vibe code a tool that produces accurate results. Even a LEAPP artifact.

I foresee both good and bad.

The days of waiting for vendors to parse the artifacts you need will eventually be a thing of the past. My hope is that labs and practitioners learn from foresight, not from painful experience, that only an expert can and should be generating code with LLMs for casework. Experts will be the ones using these tools well, because they are the ones with the skills necessary to verify every output.

In that near future, artifact parsing will not be a differentiator for tooling companies. If a software vendor's value doesn't include proprietary access methods, they risk being substituted by an average programmer with a $100-a-month Claude license.

The rules keep changing. Keep up.
