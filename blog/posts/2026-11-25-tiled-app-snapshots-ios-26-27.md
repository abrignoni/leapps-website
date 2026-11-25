---
title: Tiled App Snapshots in iOS 26 and 27
date: 2026-11-25
author: charpy4n6
tags: [iLEAPP, iOS, images, artifacts, snapshots, research]
excerpt: On recent iPhones, many App Snapshots in iLEAPP came out as horizontal streaks. Apple had changed how the images are stored inside the files. Here is what changed, in plain terms, and how iLEAPP now puts the pictures back together.
---

# Tiled App Snapshots in iOS 26 and 27

When you leave an app on an iPhone, iOS saves a picture of its screen. That picture is what you see in the app switcher, and while the app is starting up again. These **App Snapshots** can show what was on screen in an app at some point, and iLEAPP has reported them for years in the **App Snapshots** artifact, turning Apple's `.ktx` image files into ordinary PNGs you can view in the report and in LAVA.

On a recent extraction, many of those pictures came out scrambled.

## What went wrong

The extraction was a full file system extraction of an iPhone on iOS 27.2. iLEAPP found all 324 snapshots, in the usual place (`Library/SplashBoard/Snapshots/`), and listed every one with its app, path and dates. The pictures were another matter:

- **131** came out as horizontal streaks of colour, with nothing recognisable in them;
- the other **193** came out as a single plain colour, mostly white or black.

At first it looked as if all 324 had failed, the plain ones included. They had not. As it turned out, the 193 plain ones really are plain launch and placeholder screens, and iLEAPP was showing them correctly all along (more on how we know under Results). The 131 streaky ones, the snapshots with real content, are the ones that were broken, and nothing in the report said so.

When Alexis Brignoni later tested the fix described below against his own collection of test images, the same problem turned up on iPhone 14 and iPhone 15 Pro images on **iOS 26.3 and 26.5**. iOS 18 images were fine. So this is not an iOS 27 change, and the iOS version alone does not tell you which kind of file you have. The numbers in this post come from the iOS 27.2 extraction the work started on.

## What Apple changed

Two things changed inside the snapshot files.

**The image is no longer compressed.** Older snapshots were squeezed down to a few kilobytes. The new ones are stored uncompressed, at about 3.2 MB each. That on its own did no harm: iLEAPP already knew how to read both kinds.

**The pieces of the image are stored in a different order.** This is what broke the pictures.

Think of the snapshot as a jigsaw puzzle. The picture is cut into small square pieces, each 4x4 pixels, and the file stores the pieces one after another. In the older files the pieces are stored the way you read a page: the whole top row, left to right, then the next row, and so on. iLEAPP's image decoder expects exactly that.

The new files store the pieces in **tiles** instead. The image is first divided into large squares, each 32 pieces wide and 32 pieces high (128x128 pixels). Each tile is stored complete before the next one starts. Inside a tile, the pieces follow a zig-zag path called **Morton order** or **Z-order**: two pieces across, then two below them, then the next pair of pairs, and so on.

![Row-by-row order compared with Morton order](/blog/images/2026-11-25-tiled-app-snapshots-ios-26-27/block-order.svg)

In words, counting pieces as (across, down) from the top-left corner: row by row, the first pieces stored are (0,0), (1,0), (2,0) and (3,0), and only then (0,1) at the start of the second row. Inside a tile they go (0,0), (1,0), (0,1), (1,1), and then (2,0), (3,0), (2,1), (3,1): two across, two below, then on to the next square of four.

Graphics chips like this layout because pieces that are close together on screen are close together in memory. It is a common way to store textures, but we have not seen Apple document it for these files. Everything here was worked out from the files themselves.

Hand the decoder a tiled file while it expects rows, and it lays every piece in the wrong place. That is where the streaks came from. A snapshot that is one colour all over is the exception: every piece looks the same, so putting them in the wrong place changes nothing, and it still comes out right.

## How the change was spotted

**There were too many pieces.** A 1170x2532 snapshot needs 185,469 pieces. The iOS 27.2 files held 204,801. Rounding the picture up to whole tiles explains it exactly, plus one extra piece at the end. Older files always held exactly as many pieces as the picture needs.

**A second decoder complained.** Running the same files through an independent decoder, [texture2ddecoder](https://github.com/K0lb3/texture2ddecoder), put error marks into many of the pictures, including ones iLEAPP showed as plain colour. That was a sign the pieces were not in the order either decoder expected. It did not mean the plain-looking snapshots were hiding anything: once the pieces were back in order, they were still plain, pixel for pixel the same as before.

## Two zig-zags, not one

The zig-zag inside each tile can go two ways: across first, then down, or down first, then across. Get it backwards and every tile comes out flipped along its diagonal.

The iOS 27.2 phone and the iOS 26 phones above all went across first. While reviewing the fix, **Alexis found an iPhone 11 on iOS 26.2.1 whose snapshots go down first**, and fixed it in a follow-up change ([abrignoni/iLEAPP#2893](https://github.com/abrignoni/iLEAPP/pull/2893)).

Nothing inside the file was found that says which order it uses. What he did find is that the snapshot's file name does. Snapshot names end in `@2x` or `@3x`, the screen's scale, and the `@2x` snapshots were the ones going down first. The scale in the name matched the scale iOS records for each snapshot in every record he checked, so iLEAPP now uses it: a name ending in `@2x` gets the down-first order, and every other name gets across-first.

That rule rests on one 2x device. Whether the order really follows the screen scale, or something else such as the phone's chip, is not established yet.

## How iLEAPP handles it now

Before the picture goes to the decoder, iLEAPP now checks whether the file is tiled. If it is, iLEAPP puts every piece back in row order, using the zig-zag that matches the file name. The decoder then gets exactly what it always expected. If the file is not tiled, iLEAPP passes it on untouched, so snapshots from older iPhones come out exactly as they did before.

Two changes, both merged into iLEAPP:

- [abrignoni/iLEAPP#2887](https://github.com/abrignoni/iLEAPP/pull/2887) recognises tiled files and puts them back in order.
- [abrignoni/iLEAPP#2893](https://github.com/abrignoni/iLEAPP/pull/2893), from Alexis, adds the second zig-zag for `@2x` snapshots.

The code is in `KTX_reader`, in [`scripts/ktx/ios_ktx2png.py`](https://github.com/abrignoni/iLEAPP/blob/a6d7456133c4f3e7a219ee94390534de9a264b2c/scripts/ktx/ios_ktx2png.py#L202), a reader originally written by Yogesh Khatri.

## Results

Every snapshot was decoded twice, once by iLEAPP and once by the independent decoder, and the two pictures compared:

| extraction | snapshots | stored as | result |
| --- | --- | --- | --- |
| iOS 27.2 | 324 | tiles | 131 corrected; 193 plain screens identical before and after; both decoders agree |
| iOS 17 | 106 | rows | unchanged; both decoders agree |
| an older iOS extraction | 262 | rows | unchanged; both decoders agree |

Alexis also ran App Snapshots with both changes against four iOS 26 images, from iOS 26.2.1 to 26.5.2, and an iOS 18.7 image, whose snapshots stayed unchanged.

About the plain images: 193 of the 324 iOS 27.2 snapshots are a single colour, and they come out pixel for pixel identical before and after the fix. So iLEAPP showed them correctly all along; they are plain launch and placeholder screens. The 131 with real content are the ones the fix corrects.

Widget snapshots and the Messages preview cache use the same reader. All the widget snapshots we checked, including the iOS 27.2 ones, were stored in rows, so the widget artifact was not affected on those devices. We had no tiled Messages previews to test.

## What examiners should know

- **Re-run reports made before the fix if their snapshots look streaky.** Tiled snapshots did not decode correctly in older iLEAPP builds. Snapshots stored in rows were always fine. A build that includes both changes above puts tiled App Snapshots back together, for both zig-zags.
- **A re-run that still looks scrambled is not a corrected image.** The `@2x` rule comes from a single device, so a 2x snapshot that still looks wrong may be a limit of the decoder, not what the file holds. The same goes for the cases listed under "What we have not tested".
- **Plain snapshots were not the problem.** In the files we tested, every snapshot that came out as a single colour before the fix came out exactly the same after it, because a picture of one colour looks the same whatever order its pieces are in. The failures showed up as streaks. That is what we measured on these files, not a guarantee for every device.
- **The rows, paths and dates were never affected.** Only the pictures were.
- **A snapshot shows a screen iOS saved, nothing more.** Apps can hide or replace their content before the snapshot is taken, so a snapshot does not by itself show that someone viewed what is in it.

## What we have not tested

- Tiled snapshots under `Library/Caches/Snapshots`, and tiled snapshots whose names have no `@2x` or `@3x`.
- Widget snapshots and Messages previews from a 2x phone. Those artifacts always use the across-first order.
- What decides between the two zig-zags, and which iOS release first used tiles. Other models and releases may differ again.
- Damaged files. A truncated snapshot still decodes to a full-size picture without any warning, part of it missing or scrambled ([abrignoni/iLEAPP#2894](https://github.com/abrignoni/iLEAPP/issues/2894)). No truncated snapshot has turned up in a real extraction so far.
- Some header fields in the file. One is used as a tie-breaker in a rare case (see below); we do not know what Apple calls it.

If you have iOS 26 or 27 extractions where App Snapshots still look wrong with a current build, please open an issue on [iLEAPP](https://github.com/abrignoni/iLEAPP/issues). The file counts and sizes are enough to start; we do not need the pictures.

## For the technically curious

Despite the `.ktx` extension, these files are not Khronos KTX. They start with `AAPL\r\n\x1a\n`, followed by chunks, each a 4-byte little-endian length and a 4-byte tag. The pieces are 16-byte ASTC blocks, each covering 4x4 pixels.

| | older (iOS 17 compared) | tiled (iOS 27.2) |
| --- | --- | --- |
| chunks | `HEAD`, `FILL`, `LZFS`, `END ` | `HEAD`, `FILL`, `astc`, `END ` |
| texture data | LZFSE-compressed | uncompressed |
| data starts at | 0x100 | 0x4000 |
| blocks | one per 4x4 pixels | rounded up to whole 32x32-block tiles, plus one |

**Morton order.** Inside a tile, a block's position comes from interleaving the bits of its x and y block coordinates. With bits numbered from 0, the across-first order puts **x in the even bits and y in the odd bits**: x = 3 (`011`) and y = 5 (`101`) give `100111`, position 39. The `@2x` order swaps them, with y in the even bits.

**Is a file tiled?** `untile_astc_4x4` decides from the block count:

1. Work out the blocks the image needs, rounding each side up to whole 4-pixel blocks (293 x 633 for 1170x2532), and the padded count, rounding those up to whole 32-block tiles (320 x 640).
2. Fewer blocks than the image needs: the file is incomplete, which is a separate problem from the layout. It is passed on as it is, and the decoder still produces a picture from it with no error, so part of that picture will be missing or wrong. A truncated tiled file that holds at least as many blocks as the image needs but fewer than the full tiled count falls into step 3: it is passed through as rows without its layout being confirmed, and comes out scrambled. One that loses only its final extra block still reaches the full count and is put back in order correctly. Neither case is flagged in the report yet; that is tracked in [abrignoni/iLEAPP#2894](https://github.com/abrignoni/iLEAPP/issues/2894).
3. Fewer blocks than the padded count: the older row layout. Passed on as it is.
4. Exactly the blocks the image needs, when that also equals the padded count (the image is already a whole number of tiles): the count cannot tell the layouts apart. Passed on as it is unless `HEAD` word 12, the 13th 32-bit word, is 1. That word was 1 in every tiled file and 0 in every older file we compared, but its meaning is not known. No real snapshot we have needed this step.
5. Anything else is tiled: each block is copied from tile `(y // 32) * tiles_across + (x // 32)`, at the Morton position of `(x % 32, y % 32)` inside it.

## Credits

- **Alexis Brignoni** tested the fix across his corpus of images, found the same layout on iOS 26, and found and fixed the second zig-zag order for `@2x` snapshots in [abrignoni/iLEAPP#2893](https://github.com/abrignoni/iLEAPP/pull/2893).
- **Yogesh Khatri** wrote the original iOS KTX-to-PNG reader that iLEAPP builds on.
