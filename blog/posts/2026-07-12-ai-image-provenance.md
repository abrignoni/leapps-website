---
title: Spotting AI Generated Images in iLEAPP and ALEAPP
date: 2026-07-12
author: Alexis Brignoni
tags: [iLEAPP, ALEAPP, C2PA, IPTC, AI, provenance]
excerpt: iLEAPP and ALEAPP can now flag AI generated images by reading content provenance two ways, C2PA Content Credentials manifests and the IPTC Digital Source Type in XMP. Pure Python, no new dependencies, and usable today straight from the source.
---

# Spotting AI Generated Images in iLEAPP and ALEAPP

**Short version:**

- [iLEAPP](https://github.com/abrignoni/iLEAPP) and [ALEAPP](https://github.com/abrignoni/ALEAPP) can now read content provenance from images and flag AI generated media.
- It covers two sources: C2PA Content Credentials manifests and IPTC Digital Source Type in XMP.
- Pure Python. No new dependencies. It runs on the images already in your extraction.
- It is not in a packaged release yet. It is merged into the code, it will ship in the next release, and you can use it today if you run from the scripts.

## Long version

Have you looked at a picture lately and wondered if a machine made it? I do it all the time now. The good news is that a lot of AI tools, and a growing number of cameras, write that answer right into the file.

There are two common ways that provenance shows up, and they are not the same thing.

**C2PA, also called Content Credentials.** This is a signed manifest tucked inside the file. It records the tool that created or edited the image, the actions that were taken, the digital source type, and often the prior images an edit was built from. Google, Adobe, and others write these today.

**IPTC in XMP.** This is a much simpler tag called Digital Source Type. Plenty of tools, Bing Image Creator among them, write only this little tag and no C2PA manifest at all.

Here is the catch. If you only read one of the two, you miss images. So the new artifact reads both, and it tells you which one the finding came from.

## What it pulls

- 🤖 AI generated? Yes, No, or Unknown
- 🧬 Digital source type, like trained algorithmic media, algorithmically enhanced, or digital capture
- 🏷️ Metadata source, so you know if the answer came from C2PA or from IPTC/XMP
- 🛠️ Claim generator or creator tool
- ✏️ Edit actions, such as created, edited, opened, and color adjustments
- 👤 Author or creator, credit, and copyright
- 🧾 Ingredients, the prior assets an edit was built from

## A quick test

I ran it over a small folder. Four of the images are real AI pictures made with Google's tooling that carry C2PA manifests. Then I added the sample image the good folks at IPTC published, a little robot drawing in a garden, created by Brendan Quinn using Bing Image Creator. That one carries the IPTC Digital Source Type and no C2PA at all. For good measure I dropped in a normal photo with no provenance.

Here is the HTML report. Eight C2PA rows up top, then the IPTC image at the bottom. The plain photo makes no row, exactly as it should.

![iLEAPP HTML report showing eight C2PA rows and one XMP/IPTC row, with a Metadata Source column](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-12-ai-image-provenance/report-html.webp)
*Figure 1: The iLEAPP HTML report. Eight C2PA rows up top, the IPTC image at the bottom, and no row at all for the plain photo.*

A closer look at the moment the report switches from C2PA to IPTC/XMP. Same AI answer, different source.

![Close up of a C2PA row above the XMP/IPTC row, showing the Bing Image Creator credit](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-12-ai-image-provenance/report-html-iptc-row.webp)
*Figure 2: The moment the report switches from C2PA to IPTC/XMP. Same AI answer, different source.*

The same data opens in [LAVA](https://leapps.org/releases#section-lava) too. Here are the C2PA images from Google's tooling.

![The C2PA Content Provenance artifact open in the LAVA viewer, showing the C2PA rows](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-12-ai-image-provenance/lava-c2pa.webp)
*Figure 3: The C2PA Content Provenance artifact open in LAVA, showing the images made with Google's tooling.*

Scroll to the bottom and the IPTC only image sits right next to the C2PA ones, clearly labeled.

![LAVA viewer scrolled to the XMP/IPTC row with the Bing Image Creator credit](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-12-ai-image-provenance/lava-iptc.webp)
*Figure 4: The IPTC only image in LAVA, sitting right next to the C2PA ones and clearly labeled.*

## Who signed it, and when

A quick follow up, because this part is fun. The artifact now reads the signature too, not just a note that one is present. For a C2PA manifest it pulls the stated signer, the issuing certificate, the certificate validity window, the signature algorithm, and the signing time from the trusted timestamp.

On the real Google images that means the report shows the signer as Google LLC (Google Media Processing Services), the algorithm as ES256, and a signing time that lines up with the minute the picture was made. That signing time is a proper timestamp column, so it drops right into your timeline like any other date. All of it is still pure Python, no new dependencies.

One caveat, and it matters. The signer, issuer, and time are read as stated in the file. The artifact does not cryptographically verify the signature, validate the certificate chain, or check revocation. So treat "Signed By" as a strong lead to corroborate, not proof of origin. The column literally says "stated" for that reason.

## Two honest notes

The signature details above are read as stated, not cryptographically verified. Full signature and certificate chain validation would be the natural next step.

It reads the modern IPTC that lives in XMP. That is on purpose. The Digital Source Type only exists in XMP, so that is where the AI answer is.

## Get it

Small heads up. This is not in a packaged release yet. It is already merged into the iLEAPP and ALEAPP code, and it will be part of the next release. When that drops you can grab it the usual way from [leapps.org](https://leapps.org/releases).

Do you want it today? You do not have to wait. If you run iLEAPP or ALEAPP straight from the source, pull the latest from the repo and the C2PA Content Provenance artifact is already there. Run the scripts the way you normally would and it shows up in your report. That is one of the good things about open source. The minute a thing is merged, you can put it to work.

---

Thank you to the IPTC for the sample image and for pushing metadata standards for synthetic media. Thank you to the C2PA and Content Authenticity folks. And thank you to everyone in the LEAPP community who keeps testing tools and sharing images. Free tools get better because you do.

<!-- cache-bust: force redeploy 2026-07-12 (phase-2 signature section) -->
