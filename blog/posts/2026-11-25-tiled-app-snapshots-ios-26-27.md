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

At first it looked as if all 324 had failed, the plain ones included. They had not. As it turned out, the 193 plain ones really are a single colour, and iLEAPP was showing them correctly all along (more on how we know under Results). The 131 streaky ones, the snapshots with real content, are the ones that were broken, and nothing in the report said so.

When Alexis Brignoni later tested the fix described below against his own collection of test images, the same problem turned up on iPhone 14 and iPhone 15 Pro images on **iOS 26.3 and 26.5**. iOS 18 images were fine. So this is not an iOS 27 change, and the iOS version alone does not tell you which kind of file you have. The numbers in this post come from the iOS 27.2 extraction the work started on.

## What Apple changed

Two things changed inside the snapshot files.

**The extra compression layer is gone.** Older snapshots wrapped the image in a second layer of compression (LZFSE) that squeezed it down to a few kilobytes. The new ones drop that layer and are about 3.2 MB each. The image itself is still stored in the same compressed texture format (ASTC) as before, so the bytes are not raw pixels. That on its own did no harm: iLEAPP already knew how to read both kinds.

**The pieces of the image are stored in a different order.** This is what broke the pictures.

Think of the snapshot as a jigsaw puzzle. The picture is cut into small square pieces, each 4x4 pixels, and the file stores the pieces one after another. In the older files the pieces are stored the way you read a page: the whole top row, left to right, then the next row, and so on. iLEAPP's image decoder expects exactly that.

The new files store the pieces in **tiles** instead. The image is first divided into large squares, each 32 pieces wide and 32 pieces high (128x128 pixels). Each tile is stored complete before the next one starts. Inside a tile, the pieces follow a zig-zag path called **Morton order** or **Z-order**: two pieces across, then two below them, then the next pair of pairs, and so on.

![Row-by-row order compared with Morton order](/blog/images/2026-11-25-tiled-app-snapshots-ios-26-27/block-order.svg)

In words, counting pieces as (across, down) from the top-left corner: row by row, in the four-piece-wide image on the left of the diagram, the first pieces stored are (0,0), (1,0), (2,0) and (3,0), and only then (0,1) at the start of the second row. In a real 1170-pixel-wide snapshot the first row is 293 pieces long, so (0,1) comes only after all of them. Inside a tile they go (0,0), (1,0), (0,1), (1,1), and then (2,0), (3,0), (2,1), (3,1): two across, two below, then on to the next square of four.

Graphics chips like this layout because pieces that are close together on screen are close together in memory. It is a common way to store textures, but we have not seen Apple document it for these files. Everything here was worked out from the files themselves.

Hand the decoder a tiled file while it expects rows, and it lays every piece in the wrong place. That is where the streaks came from. A snapshot that is one colour all over is the exception: every piece looks the same, so putting them in the wrong place changes nothing, and it still comes out right.

## How the change was spotted

**There were too many pieces.** A 1170x2532 snapshot needs 185,469 pieces. The iOS 27.2 files held 204,801. Rounding the picture up to whole tiles explains it exactly, plus one extra piece at the end. The older files we compared held exactly as many pieces as the picture needs.

**A second decoder complained.** Running the same files through an independent decoder, [texture2ddecoder](https://github.com/K0lb3/texture2ddecoder), put error marks into many of the pictures, including ones iLEAPP showed as plain colour. That was a sign the pieces were not in the order either decoder expected. It did not mean the plain-looking snapshots were hiding anything: once the pieces were back in order, they were still plain, pixel for pixel the same as before.

## Two zig-zags, not one

The zig-zag inside each tile can go two ways: across first, then down, or down first, then across. Get it backwards and every tile comes out flipped along its diagonal.

The iOS 27.2 phone and the iOS 26 phones above all went across first. While reviewing the fix, **Alexis found an iPhone 11 on iOS 26.2.1 whose snapshots go down first**, and fixed it in a follow-up change ([abrignoni/iLEAPP#2893](https://github.com/abrignoni/iLEAPP/pull/2893)).

Nothing inside the file was found that says which order it uses. What he did find is that the snapshot's file name does. Snapshot names end in `@2x` or `@3x`, the screen's scale, and the `@2x` snapshots were the ones going down first. The scale in the name matched the scale iOS records for each snapshot in every record he checked, so iLEAPP now uses it: a name ending in `@2x` gets the down-first order, and every other name gets across-first.

That rule rests on one 2x device. Whether the order really follows the screen scale, or something else such as the phone's chip, is not established yet.

## How iLEAPP handles it now

Before the picture goes to the decoder, iLEAPP now checks whether the file is tiled. If it is, iLEAPP puts every piece back in row order, using the zig-zag that matches the file name. The decoder then gets exactly what it always expected. If the file is stored in rows, iLEAPP passes it on untouched, so snapshots from older iPhones come out exactly as they did before. If the file is neither, for example because it was cut short, iLEAPP no longer decodes it at all (more on that below).

Three changes, all merged into iLEAPP:

- [abrignoni/iLEAPP#2887](https://github.com/abrignoni/iLEAPP/pull/2887) recognises tiled files and puts them back in order.
- [abrignoni/iLEAPP#2893](https://github.com/abrignoni/iLEAPP/pull/2893), from Alexis, adds the second zig-zag for `@2x` snapshots.
- [abrignoni/iLEAPP#2895](https://github.com/abrignoni/iLEAPP/pull/2895), from Alexis, refuses cut-short files instead of turning them into a full-size picture.

The code is in `KTX_reader`, in [`scripts/ktx/ios_ktx2png.py`](https://github.com/abrignoni/iLEAPP/blob/b3c837a954c7659df67f2b25e9d3d2cf89cd66fe/scripts/ktx/ios_ktx2png.py#L228), a reader originally written by Yogesh Khatri.

**Cut-short files.** Before #2895, a snapshot file that had been cut short still decoded to a full-size picture with no warning, part of it missing or scrambled. A cut-short file of the older, compressed kind did worse: it stopped the App Snapshots artifact, and the report had no App Snapshots rows at all. Now iLEAPP accepts a snapshot file only at the sizes every snapshot we measured had, and refuses anything else. A refused snapshot gets no row in App Snapshots or in Widgets; the log records it with a line starting "Left out" and the file name. Messages previews keep their row, and the row records that the decode failed. No cut-short snapshot has turned up in a real extraction so far; the ones we tested were made by cutting real files.

## Results

Every snapshot was decoded twice, once by iLEAPP and once by the independent decoder, and the two pictures compared:

| extraction | snapshots | stored as | result |
| --- | --- | --- | --- |
| iOS 27.2 | 324 | tiles | 131 corrected; 193 plain screens identical before and after; both decoders agree |
| iOS 17 | 106 | rows | unchanged; both decoders agree |
| an older iOS extraction | 262 | rows | unchanged; both decoders agree |

Alexis also ran App Snapshots with #2887 and #2893 against four iOS 26 images, from iOS 26.2.1 to 26.5.2, and an iOS 18.7 image, whose snapshots stayed unchanged.

About the plain images: 193 of the 324 iOS 27.2 snapshots are a single colour, and they come out pixel for pixel identical before and after the fix. So iLEAPP showed them correctly all along. They may be launch or placeholder screens, but the files do not say what put them on screen; all we measured is that they are one colour. The 131 with real content are the ones the fix corrects.

Widget snapshots and the Messages preview cache use the same reader. All the widget snapshots we checked, including the iOS 27.2 ones, were stored in rows, so the widget artifact was not affected on those devices. We had no tiled Messages previews to test.

## What examiners should know

- **Re-run reports made before the fix if their snapshots look streaky.** Tiled snapshots did not decode correctly in older iLEAPP builds. Snapshots stored in rows were always fine. A build that includes #2887 and #2893 puts tiled App Snapshots back together, for both zig-zags. A build with only #2887 still gets the `@2x` ones wrong.
- **A re-run that still looks scrambled is not a corrected image.** The `@2x` rule comes from a single device, so a 2x snapshot that still looks wrong may be a limit of the decoder, not what the file holds. The same goes for the cases listed under "What we have not tested".
- **Plain snapshots were not the problem.** In the files we tested, every snapshot that came out as a single colour before the fix came out exactly the same after it, because a picture of one colour looks the same whatever order its pieces are in. The failures showed up as streaks. That is what we measured on these files, not a guarantee for every device.
- **For tiled snapshots, the rows, paths and dates were never affected.** Only the pictures were. Cut-short files are the exception described above.
- **A missing row does not mean a missing file.** With a current build, a snapshot file that is cut short gets no row in App Snapshots or Widgets. Check the iLEAPP log for "Left out" lines before concluding a snapshot was not on the device.
- **A snapshot shows a screen iOS saved, nothing more.** Apps can hide or replace their content before the snapshot is taken, so a snapshot does not by itself show that someone viewed what is in it.

## What we have not tested

- Tiled snapshots under `Library/Caches/Snapshots`, and tiled snapshots whose names have no `@2x` or `@3x`.
- Widget snapshots and Messages previews from a 2x phone. Those artifacts always use the across-first order.
- What decides between the two zig-zags, and which iOS release first used tiles. Other models and releases may differ again.
- Cut-short files from a real extraction. The refusal described above was tested on files we cut short ourselves.
- Some header fields in the file. One is used as a tie-breaker in a rare case (see below); we do not know what Apple calls it.

If you have iOS 26 or 27 extractions where App Snapshots still look wrong with a current build, please open an issue on [iLEAPP](https://github.com/abrignoni/iLEAPP/issues). The file counts and sizes are enough to start; we do not need the pictures.

## For the technically curious

Despite the `.ktx` extension, these files are not Khronos KTX. They start with `AAPL\r\n\x1a\n`, followed by chunks, each a 4-byte little-endian length and a 4-byte tag. The pieces are 16-byte ASTC blocks, each covering 4x4 pixels.

| | older (iOS 17 compared) | tiled (iOS 27.2) |
| --- | --- | --- |
| chunks | `HEAD`, `FILL`, `LZFS`, `END ` | `HEAD`, `FILL`, `astc`, `END ` |
| texture data | ASTC blocks inside LZFSE | ASTC blocks, no LZFSE |
| data starts at | 0x100 | 0x4000 |
| blocks | one per 4x4 pixels | rounded up to whole 32x32-block tiles, plus one |

**Morton order.** Inside a tile, a block's position comes from interleaving the bits of its x and y block coordinates. With bits numbered from 0, the across-first order puts **x in the even bits and y in the odd bits**: x = 3 (`011`) and y = 5 (`101`) give `100111`, position 39. The `@2x` order swaps them, with y in the even bits.

**Is a file tiled?** First, the texture chunk has to hold all the bytes its length field declares; a chunk that ends early is refused. Then `untile_astc_4x4` decides from the block count:

1. Work out the blocks the image needs, rounding each side up to whole 4-pixel blocks (293 x 633 for 1170x2532), and the padded count, rounding those up to whole 32-block tiles (320 x 640).
2. Exactly the blocks the image needs, when that is fewer than the padded count: the older row layout. Passed on as it is. When the two counts are equal, step 4 decides instead.
3. Exactly the padded count plus one block: tiled.
4. When the image is already a whole number of tiles, the padded count equals the blocks the image needs, and the count cannot tell the layouts apart. Then `HEAD` word 12, the 13th 32-bit word, decides: 1 means tiled, anything else means rows. That word was 1 in every tiled file and 0 in every older file we compared, but its meaning is not known. A file holding exactly the padded count with word 12 set to 1 is also read as tiled. No real snapshot we have needed this step.
5. Any other size, or a size that is not a whole number of 16-byte blocks, is refused. Every one of 10,628 snapshot files in 24 images, iOS 15 to 27, had the size in step 2 or step 3.

A tiled file is put back in order by copying each block from tile `(y // 32) * tiles_across + (x // 32)`, at the Morton position of `(x % 32, y % 32)` inside it.

## Credits

- **Alexis Brignoni** tested the fix across his corpus of images, found the same layout on iOS 26, found and fixed the second zig-zag order for `@2x` snapshots in [abrignoni/iLEAPP#2893](https://github.com/abrignoni/iLEAPP/pull/2893), and made iLEAPP refuse cut-short snapshot files in [abrignoni/iLEAPP#2895](https://github.com/abrignoni/iLEAPP/pull/2895).
- **Yogesh Khatri** wrote the original iOS KTX-to-PNG reader that iLEAPP builds on.
