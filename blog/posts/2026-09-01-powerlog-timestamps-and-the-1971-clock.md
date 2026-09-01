---
title: Powerlog Timestamps, Offsets, and a Clock That Thinks It's 1971
date: 2026-09-01
author: Alexis Brignoni
tags: [iLEAPP, iOS, PowerLog, timestamps, DFIR, research]
excerpt: A powerlog row does not store the time. It stores a stopwatch, and a second table tells you how far off it is. Here is why the offset is 69 seconds on one phone and 54 years on another, why forensic tools disagree, and which columns actually need the correction.
---

# Powerlog Timestamps, Offsets, and a Clock That Thinks It's 1971

![A wall clock and a stopwatch side by side, with a plus offset arrow running from the stopwatch to the clock and the equation stopwatch value plus offset equals real time below them.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-09-01-powerlog-timestamps-and-the-1971-clock/powerlog-timestamps-header.webp)
*Figure 1: A powerlog timestamp is a stopwatch reading. The offset table turns it into real time.*

A collaborator was looking at powerlog data in iLEAPP this week and asked a fair question: the Time Offset column on their extraction held a number with ten digits in it. Ten digits of seconds. What is that about?

Here is the short version, and I promise it is simpler than it looks.

## Two clocks, not one

Your iPhone has the clock you know, the one on the lock screen that says what time it is. Powerlog, the database that quietly records app usage, battery level, screen state and a pile of other activity, does not write that clock into its rows. It writes a stopwatch.

Think of it that way. A stopwatch does not know what time it is. It only knows how long it has been running, and it only moves forward. Ian Whiffin dug into this a while back and identified it as a monotonic clock, which is the formal name for exactly that: a counter that ticks forward at a steady rate and does not care if you change the time zone, fix the date, or let the network adjust the clock.<sup><a href="#note-1">[1]</a></sup>

So every powerlog row says "the stopwatch read X when this happened." Useful, but not a date.

## The offset table is the translation

The same database keeps a small side table where iOS periodically writes a check-in: right now, the stopwatch is this many seconds away from real time. That number is the offset.

Real time = stopwatch value + offset. That is the whole trick.

## Why the offset can be tiny or enormous

The offset is just the distance between the stopwatch and the wall clock, and that distance depends entirely on where the stopwatch happened to start. On the images we validated against, we measured all of these:

- 69 seconds on an iOS 12.4 device
- about 32 days on an iOS 18.7 device
- about 54.7 years on an iPhone 16 running iOS 26

That last one is the ten digit number that started this post. The stopwatch on that phone reads like a calendar from 1971, so the correction is half a century of seconds. Nothing is broken. Add the offset and every row lands exactly where it should, right up against the date the data was collected. We checked.

## Why tools disagree with each other

Two reasons, and both are ordinary.

One, some tools show the stopwatch value and some show the corrected time. When the offset is 69 seconds, both outputs look right and nobody notices. When the offset is 54 years, the difference is suddenly impossible to miss. The tools did not change. The size of the offset did.

Two, the offset itself drifts. The phone keeps checking in, and the recorded correction creeps as the clocks slide against each other. One phone we measured wrote 32 check-ins across about a week and the offset moved by 5 seconds. A tool that applies one fixed offset and a tool that applies the correction in effect at each row will land a few seconds apart. Neither is lying. They are answering slightly different questions.

## Three things worth keeping

First, not every column needs the offset. Some powerlog tables also store regular dates right next to the stopwatch values, and those are already real time. Correct a column like that and now you have broken it.

Second, durations never need the offset. The gap between two stopwatch readings is the same gap no matter what time it is, which is pretty neat.

Third, whatever tool you use, check its work. iLEAPP applies the correction per row and then shows you the offset it applied in its own column, so you can always get back to the value as stored and redo the math yourself. That is on purpose. Verify and validate, always.

Thanks to Kevin Pagano for the sysdiagnose research and for putting the powerlog output through its paces, and to Ian for the research that put a name on the stopwatch.

<ol>
<li id="note-1">Ian Whiffin, "CurrentPowerLog &amp; the Monotonic Clock", DoubleBlak, 28 June 2025, <a href="https://doubleblak.com/powerlog">doubleblak.com/powerlog</a>.</li>
</ol>
