---
title: The VLEAPP Revival. Reading the Whole Head Unit.
date: 2026-08-31
author: Alexis Brignoni
tags: [VLEAPP, vehicle forensics, QNX, qnxprobe, filesystems, raw images]
excerpt: VLEAPP sat mostly still for twenty-one months because it could only take logical extractions, and vehicle evidence does not arrive that way. This month it came back. Raw head unit images and native Berla iVe exports now go straight in, read through seven filesystem families plus QNX boot images, most of which no mainstream open source tool could touch. Here is what landed, how it was validated, and what we need from you.
---

# The VLEAPP Revival. Reading the Whole Head Unit.

Have you looked at VLEAPP's commit history lately? For a long stretch there was not much to look at. The last pull request that added new parsing capability landed in November 2024, a set of Chrysler and Ford scripts contributed by JaysonU25.<sup><a href="#note-1">[1]</a></sup> After that, twenty-one months where the vehicle side of the LEAPPs family mostly sat still.

The honest reason was the input. VLEAPP could only parse logical extractions: files somebody else had already pulled out of the vehicle. But vehicle evidence does not usually arrive as a folder of files. It arrives as a raw image of a head unit's storage, or as a Berla iVe export with that raw image inside it. And head units do not run filesystems your regular tooling knows. Ford Sync units are QNX6. When we checked, file(1), libblkid, and The Sleuth Kit had no support for QNX6 at all.<sup><a href="#note-2">[2]</a></sup> So the raw image sat there, unreadable, and the tool sat with it.

Twenty-one months is a long time for a tool to stand still. This is the revival.

**Short version:** VLEAPP now takes a raw head unit disk image with `-t raw` and a native Berla iVe export with `-t iva`. It reads QNX6, QNX4, ETFS, EFS, ext2/3/4, FAT32 and exFAT volumes, and QNX IFS boot images, identifying each by its own on-disk structure. No mounting, no administrator rights, pure standard library Python, and the image is opened read-only. The reading is done by qnxprobe, a single-file MIT tool that VLEAPP vendors and that is well worth having on its own. Then VLEAPP runs its 103 artifact definitions against whatever it finds. New artifacts landed too, across Ford and BMW head units. And we need two things from you: test data and parsers.

**Long version:** keep reading.

## The revival started with parsers

Before the input problem got solved, the artifact library got a real push. August brought new artifacts for Ford Sync Gen3 and G4 and for BMW head units: Bluetooth paired devices with their contacts and call logs, installed software inventories, power and reset histories that read like a vehicle usage timeline (ignition, door ajar, door unlocked, with timestamps), diagnostics, positioning logs, navigation analytics, SiriusXM data, and user profiles pulled out of the HMI's IndexedDB stores. VLEAPP now carries 103 artifact definitions across 50 modules.

A reminder that matters in this domain: a vehicle carries data about more than one person. Paired phones, synced contacts, and call logs may belong to passengers rather than the driver. VLEAPP's artifact descriptions say what the record contains and leave attribution to the examiner, where it belongs.

## Then the input problem fell

The fix is a small tool called [qnxprobe](https://github.com/abrignoni/qnxprobe), vendored into VLEAPP and also usable on its own.<sup><a href="#note-3">[3]</a></sup> Point it at a raw image and it identifies every volume by reading the volume's own on-disk structures, superblocks and boot records and file tables, instead of trusting a partition type byte. Then it walks each filesystem it recognizes and extracts the logical files into a zip, with a provenance manifest that ties every extracted path back to its exact location on the disk. It never mounts anything, needs no administrator rights, and is standard library Python from top to bottom.

VLEAPP hands the raw image to the vendored copy, stages what it extracts, and from there the run behaves exactly like a zip input:

```text
python3 vleapp.py -t raw -i mmcblk0.img -o report_folder
python3 vleapp.py -t iva -i CASE.iVa -o report_folder
```

The `-t iva` route is worth a sentence. A Berla iVe export carries the raw image it acquired. VLEAPP reaches through the export to that image and reads the vehicle data from the image itself, so the export becomes a one-command input instead of a container you unpack by hand.

## The filesystems

This is the part worth emphasizing, because it changes what you can do with a bare image.

| Filesystem | Where you meet it | How it was validated |
| --- | --- | --- |
| QNX6 | Ford Sync storage volumes | Real Ford Sync Gen3 and G4 images; row counts reproduced across three extraction routes |
| QNX4 | Older QNX systems | Round trip against the Linux kernel's own qnx4 driver as the oracle, 17 of 17 entries; synthetic test image only |
| ETFS | QNX transaction filesystem on NAND flash | Round trip against the Netherlands Forensic Institute's qnxmount test images, 32 of 32 entries; synthetic only |
| EFS | QNX flash filesystem (F3S) | Same qnxmount round trip, 31 of 31 entries; synthetic only |
| QNX IFS | QNX boot images | Byte-exact decompression of the three real boot volumes on a Ford Sync G4 image |
| ext2/3/4 | BMW MGU head units, among others | Real BMW image |
| FAT32 and exFAT | Removable media in the vehicle | Independent fixtures written by different tools, exact path and content hash round trip |

Every walker was validated against something a different implementation wrote. The ETFS and EFS readers were transcribed from the Kaitai format specifications in the Netherlands Forensic Institute's qnxmount project and then required to reproduce, entry for entry and byte for byte, the reference archives that project ships.<sup><a href="#note-4">[4]</a></sup> The QNX4 reader was built from the Linux kernel's read-only qnx4 driver and then made to match that same driver's view of a populated test image, every name, mode, owner, timestamp, and byte.<sup><a href="#note-5">[5]</a></sup> The IFS reader decompresses QNX boot images (the compression turned out to be UCL, not zlib, which cost us a wrong guess before the sources settled it) and was proven byte-exact on the three real boot volumes of a Ford Sync G4.

Our test set holds no real ETFS, EFS, or QNX4 vehicle extraction yet. Those three readers are validated against known data that an independent implementation produced, which is real validation, but it is not the same as reading a volume off an actual head unit. That gap is the first thing on the list below.

## qnxprobe is useful on its own

Worth saying plainly, because it is easy to miss: qnxprobe is a separate tool that VLEAPP vendors, not a part of VLEAPP. One Python file, about 3,500 lines, MIT licensed, no dependencies past the standard library. Grab it from [github.com/abrignoni/qnxprobe](https://github.com/abrignoni/qnxprobe) and run it. It opens the image read-only and never writes to it.

Even if you never run VLEAPP, it answers questions you have on any vehicle image.

**What is on this disk?** With no flags you get the report: the partition table, every partition with its size and starting sector, which ones carry a filesystem it confirmed, which ones it could not identify, and per-filesystem detail like QNX6 superblock generations and how much of its partition the volume fills. That last number matters. A volume that fills 99.9% of the partition containing it is a very different claim than a chance magic-number match.

```text
python3 qnxprobe.py mmcblk0.img
```

**What is inside those volumes?** `--list` walks each filesystem it recognizes, with `--depth` and `--list-max` to control how far it goes.

```text
python3 qnxprobe.py --list --depth 4 --list-max 3000 mmcblk0.img
```

**Give me the files.** `--extract` copies the logical files out of every filesystem it found into a zip, with a manifest recording which volume each path came from and where that volume sat on the disk. It is an ordinary zip. Feed it to VLEAPP, or to whatever you already use. `--only` narrows to one partition by name or label, and `--exclude` skips paths you do not want, which is how you leave out an encrypted subtree or a bulk payload no parser is going to read.

```text
python3 qnxprobe.py --extract sync_g4.zip mmcblk0.img
python3 qnxprobe.py --extract storage.zip --only storage mmcblk0.img
```

**Where do I start?** `--triage` ranks the volumes by how much each has been written and flags the ones that are probably not worth your time. It uses what the probe already read: the QNX6 superblock serial is a commit counter, ext exposes mount count and lifetime kilobytes written. It also samples filenames and says so when they are encrypted, because a volume with encrypted names is not going to yield to any parser without the keys. On a head unit with a partition measured in tens of gigabytes, knowing which volume to pull first is worth the ten seconds.

**Should I trust a negative?** `--self-test` builds throwaway positive and negative images, confirms the detector reports both ways, and deletes them. If it tells you a filesystem is not present, run that first, and you know the detector was working before you put the absence in a report.

```text
python3 qnxprobe.py --self-test
```

## Does the old stuff still work?

Yes, and we measured rather than assumed. After every filesystem landed, the Ford Sync Gen3 export was re-run end to end and reproduced its baseline extraction and its full artifact output at identical row counts, and the Ford Sync G4 image identified exactly as before, with no new filesystem claiming a volume that belongs to another. A detector that misfires on someone else's format is worse than no detector, so each new reader is also required to decline every other format's real bytes.

## What we need from you

Here is the call to action, and I mean it.

**Test data.** If you can lawfully share a vehicle extraction, we want it: raw head unit images from any make, chip-off images, iVe exports. The most valuable thing you could send right now is anything that carries ETFS, EFS, or QNX4, because those readers are waiting on real-world data to graduate from synthetic validation. Known-data captures are gold: a device you populated yourself, with documented actions, so parser output can be checked against what you actually did. Open an issue on the VLEAPP GitHub repository to start the conversation, or email me at abrignoni[at]duck[dot]com.

**Parsers.** VLEAPP has artifacts for Ford, BMW, Chrysler and FCA vehicles, Hyundai, Kia, Nissan, and Alfa Romeo. That list should be longer, and the head units those parsers cover should be deeper. If you have a vehicle system in front of you and a little Python, the artifact format is documented and there are 50 modules to crib from. Send a pull request. We will be happy to entertain it.

The LEAPPs are free and open source under the MIT license, and they stay that way. The tools get better when the community feeds them. That is not a slogan, it is literally how this revival happened.

## Thank you

Thank you to JaysonU25 for the 2024 Chrysler and Ford parsers that closed out the last active stretch,<sup><a href="#note-1">[1]</a></sup> and to Johann-PLW for the LAVA output support and the steady maintenance work that kept VLEAPP's plumbing modern while the parsing side stood still. Thank you to the Netherlands Forensic Institute for publishing qnxmount with its format specifications and test images under Apache-2.0; that work turned ETFS and EFS from a reverse engineering project into an engineering one.<sup><a href="#note-4">[4]</a></sup> The QNX4 reader stands on the Linux kernel's qnx4 driver, and the IFS work stands on the open QNX sources and Markus Oberhumer's UCL.<sup><a href="#note-5">[5]</a></sup>

A tool comes back when people give it something to work with. The head unit was always holding the data. Now the tools in your hands can read it.

One practical note on getting your hands on this. Everything described here is merged into VLEAPP's main branch, so you can use it today by running VLEAPP from the source code. It is not in a packaged release yet. When the next release is cut it will show up on the [LEAPPs releases page](https://leapps.org/releases#section-vleapp) like always.

## Endnotes

<ol class="blog-endnotes">
<li id="note-1">VLEAPP <a href="https://github.com/abrignoni/VLEAPP/pull/52">PR #52</a>, "Produced scripts for different Chrysler and Ford Vehicles", merged November 27, 2024. The next pull requests that added new parsing capability merged August 27, 2026.</li>
<li id="note-2">Checked against The Sleuth Kit's supported filesystem list (<code>fls -f list</code>) and the file(1) magic database; neither names QNX6, and libblkid does not identify it. See also <a href="https://github.com/sleuthkit/sleuthkit/wiki/FAQ">the TSK documentation</a> for its supported filesystems.</li>
<li id="note-3">qnxprobe lives at <a href="https://github.com/abrignoni/qnxprobe">github.com/abrignoni/qnxprobe</a> and is vendored verbatim into VLEAPP with a hash guard, so the copy in the tool is provably the reviewed upstream file. The design and validation detail for the raw image input is in VLEAPP's <a href="https://github.com/abrignoni/VLEAPP/blob/33296668d2f45e5a60a3c241eb20e1bdf7b3d676/admin/docs/raw_image_input.md"><code>admin/docs/raw_image_input.md</code></a> at the merged commit.</li>
<li id="note-4">Netherlands Forensic Institute, <a href="https://github.com/NetherlandsForensicInstitute/qnxmount">qnxmount</a> (Apache-2.0). Its Kaitai specifications are themselves sourced to QNX's <code>fs/etfs.h</code> and <code>fs/f3s_spec.h</code> headers, and its committed test images and reference archives are what the ETFS and EFS readers were required to reproduce.</li>
<li id="note-5">The Linux kernel's read-only <a href="https://github.com/torvalds/linux/tree/master/fs/qnx4"><code>fs/qnx4</code></a> driver served as both the format source and the validation oracle for the QNX4 reader. The IFS format was sourced from QNX's <code>dumpifs</code> and <code>sys/image.h</code> in the open QNX sources, with the NRV2B decompressor ported from <a href="https://www.oberhumer.com/opensource/ucl/">Markus Oberhumer's UCL</a>.</li>
</ol>
