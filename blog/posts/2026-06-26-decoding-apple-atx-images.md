---
title: Decoding Apple ATX Images in iLEAPP
date: 2026-06-26
author: James Habben
tags: [iLEAPP, iOS, images, artifacts, research]
excerpt: Wallpaper research led to a broader Apple image-cache problem: ATX texture files. Here is how iLEAPP now parses and decodes many of them, with a reusable parser that should be easy to port into other tools.
---

# Decoding Apple ATX Images in iLEAPP

This one started as a side quest from the wallpaper work.

While digging through SpringBoard and PosterBoard files, I kept running into image-like data that was not a normal JPG, PNG, HEIC, or cpbitmap. Some wallpaper pieces were easy enough to explain. Older SpringBoard files had `cpbitmap` data. Newer PosterBoard paths had things like `output.layerStack`. But then there were these `.atx` files sitting in image-heavy places, looking very much like they wanted to be pictures.

They were not just wallpaper files either. I started seeing ATX files around PosterBoard snapshots, runtime snapshots, avatar and Animoji resources, contact poster caches, and other Apple UI image caches. At that point it felt wrong to bury the work inside a SpringBoard parser. ATX needed to become its own thing.

So [iLEAPP](https://leapps.org/releases#section-ileapp) now has a new artifact:

- **Artifact:** Apple ATX Images
- **Category:** Images
- **Module:** `scripts/artifacts/apple_atx_images.py`
- **Reusable parser:** `leapp_functions/parsers/apple_atx.py`

![iLEAPP module selection showing the Apple ATX Images artifact](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-06-26-decoding-apple-atx-images/ileapp-atx-images-module.png)
*Figure 1: iLEAPP GUI showing Apple ATX Images artifact*

## What ATX is

ATX files are Apple `AAPL` texture containers. The files I looked at used a chunked layout with a magic header and chunks such as:

```text
AAPL magic header
HEAD
FILL
astc / ASTC
LZFS
END
```

The `HEAD` chunk holds useful metadata: width, height, depth, array layer count, mipmap count, a texture UUID, and pixel format discriminator values. The actual image payload is ASTC compressed texture data.

That last part is what made this interesting. It was not enough to find the payload and write it out. The payload needed to be interpreted as texture data first.

Here is one of those ATX files previewed in [Crush Forensics](https://github.com/kalink0/crush-forensics), which made it a lot easier to poke around the source paths and decoded image metadata while testing.

![Crush Forensics previewing an Apple ATX image and metadata](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-06-26-decoding-apple-atx-images/crush-atx-image.png)
*Figure 2: Crush Forensics showing decoded Apple ATX image*

## The jumbled-image problem

The first decoder attempt was close enough to be encouraging and wrong enough to be annoying.

Images were coming out, so ASTC decompression was working. But many of them were visually shuffled, like the right little blocks were present but sitting in the wrong places. That usually means the problem is not the pixels themselves. It means the block order is wrong.

The fix was in the ATX `astc` payload layout. The blocks were macro-tiled rather than stored as a simple linear ASTC stream. After adjusting the Morton block de-tiling logic, including swapping the local X/Y interpretation, those previously shuffled images reconstructed correctly.

That was the satisfying moment in this parser: not a huge rewrite, just the right small correction that made the image snap into place.

## Pixel formats and honest guesses

The initial assumption was that pixel format discriminator `(3, 5)` meant ASTC 4x4. That worked, but it was not the whole story.

In testing, a lot of valid ATX files used other discriminator pairs:

```text
(1, 1)
(3, 1)
```

Those decoded correctly as ASTC 4x4 when the payload type and payload size matched what ASTC 4x4 should look like. The parser now reports `(3, 5)` as confirmed ASTC 4x4, and treats `(1, 1)` and `(3, 1)` as inferred ASTC 4x4.

That distinction matters. I do not want the output to pretend we know more than we do. If something is inferred from successful decoding and payload shape, the parser says so.

## LZFS chunks

Some ATX files use `LZFS` chunks instead of a plain `astc` or `ASTC` payload. In the samples I tested, those chunks contained LZFSE-compressed ASTC payload data. Once decompressed, the data could be decoded as ASTC 4x4 too.

I saw this especially around avatar and Animoji-style resources. That was one of the clues that this needed to be more general than a wallpaper artifact.

## What iLEAPP reports

The Apple ATX Images artifact searches globally for:

```text
**/*.atx
```

When decoding succeeds, it checks the decoded PNG into the media output. It also reports metadata so the file is still useful even when image decoding does not work.

![LAVA showing decoded Apple ATX image previews and metadata](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-06-26-decoding-apple-atx-images/lava-atx-image.png)
*Figure 3: LAVA showing decoded Apple ATX images*

The artifact currently reports:

- Image preview when decoding succeeds
- Filename
- Width and height
- Depth
- Array layers
- Mipmap count
- Pixel format
- Texture UUID
- Payload type
- Payload byte size
- Declared payload byte size
- Chunk list
- Status and warnings
- File created and modified timestamps
- Source path

One important boundary: this artifact reports ATX images and metadata. It does **not** claim that a file is the active wallpaper just because it appeared in a PosterBoard-ish path. Paths like temporary PosterConfigurations, PosterSnapshots, `PRBPosterExtensionDataStore`, and `output.layerStack` can be very useful image sources, but path alone is not proof of current assignment.

## Built for two

I wrote the parser module so it would be usable in both iLEAPP and Crush. After discovering [Crush Forensics](https://github.com/kalink0/crush-forensics) a few weeks back, it's quickly become one of my favorite tools.


## One framework wrinkle

There was also a small iLEAPP framework issue hiding in the middle of this.

Some decoded ATX files were generating PNGs correctly, but the images did not show up in [LAVA](https://leapps.org/releases#section-lava). The parser was not the problem. The issue was path resolution during media check-in when filenames contained glob metacharacters, especially brackets.

For example:

```text
Snapshot-[PRPosterLevelBackground-...].atx
```

Those brackets can confuse `Path.match()`-style matching. A local framework fix now handles the single-basename case directly and adds normalized exact/suffix matching while keeping the older match behavior for compatibility.

There is already an [open RLEAPP issue](https://github.com/abrignoni/RLEAPP/issues/286) and PR for this, identified and sent in by [OneSixForensics](https://github.com/OneSixForensics). We will have this merged into all the tools very soon.

## What is next

This is initial ATX support, and there is still plenty to learn.

The next useful research steps are probably:

- Classifying where ATX files appear: wallpapers, contact posters, avatars, runtime snapshots, switcher or gallery previews
- Learning more about the pixel format discriminator pairs
- Parsing nearby plist or JSON configuration files for context
- Figuring out what metadata, if any, can prove active wallpaper assignment
- Porting or adapting the parser for other open source tools

The nice part is that the hard first step is done. iLEAPP can now find these ATX containers, parse their metadata, decode many of them, and put the result where examiners can actually see it.

As with the SpringBoard wallpaper work, this came from following one thread and letting it lead to the next question. Those are my favorite kinds of artifacts.
