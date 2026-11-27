---
title: Website Update - Search, Better Docs, and More
date: 2026-06-07
author: Alexis Brignoni
tags: [announcement, website, updates]
excerpt: The LEAPPs website got a big update. Here is a rundown of everything that changed, from site-wide search to improved docs and a more consistent footer across every page.
---

# Website Update - Search, Better Docs, and More

Over the past few days the LEAPPs website received a large set of improvements. This post walks through what changed and why each piece matters.

---

## Site-wide Search

The biggest addition is search. Every page now has a search bar in the navigation. Type anything and you will get results grouped into three categories:

- **Blog posts** from this blog
- **Artifacts** from the [iLEAPP](https://leapps.org/releases#section-ileapp), [ALEAPP](https://leapps.org/releases#section-aleapp), [RLEAPP](https://leapps.org/releases#section-rleapp), and [VLEAPP](https://leapps.org/releases#section-vleapp) repositories
- **Pages** from across the site

Search works on both desktop and mobile. On mobile, open the menu and the search bar is right at the top.

This is useful when you know the name of an artifact and want to find it quickly, or when you are looking for a specific topic and do not know which tool covers it.

---

## Blog Tag Filtering and Pagination

The blog page now has a tag filter dropdown. If you are only interested in posts about a specific topic, you can filter by tag and see only those posts.

Posts also load in groups of eight instead of all at once. A "Load more" button lets you page through additional posts as the blog grows.

---

## Docs Improvements

The Quick Start page was updated in a few places:

- **Executables note**: a callout now appears at the top of the Install and Run section pointing to the Releases page. If you do not want to run Python scripts directly, pre-built executables are available and no Python installation is needed.
- **CLI example fix**: the command line example now correctly uses `iLEAPP.py` instead of the GUI launcher.
- **Report entry point**: the Read Your Report section now mentions that the output folder opens with `index.html`.
- **Extraction table**: GrayKey was added for ALEAPP. References to tools that no longer apply were removed. VLEAPP now correctly lists logical acquisitions.

---

## About Page Updates

Several things changed on the About page:

- **Core contributors**: Johann-PLW, stark4n6, ydkhatri, JamesHabben, and snoop168 are now listed with their roles and links to their GitHub profiles. These are the people who have contributed significantly to the LEAPPs tools over the years.
- **Comparison table**: a table was added showing how LEAPPs compares to commercial tools and manual review across several criteria. It gives new visitors a quick sense of where the tools fit.
- **Quote update**: the pull quote on the page now reads: *"Tool reports are not the data. The data is the data. Validate everything that matters."*

---

## Social Links and Footer

The footer is now consistent across every page. All thirteen pages share the same navigation links and the same set of social links.

New additions to the footer:

- **LinkedIn**: the LEAPPs company page at linkedin.com/company/leapps
- **YouTube**: the @AlexisBrignoni channel where tool walkthroughs and forensics content live

All social links now have icons to make them easier to identify at a glance.

A Google Translate link is also in every footer. It opens the site through Google Translate so readers who prefer a different language can access the content.

---

## SEO and Technical Improvements

A number of improvements were made under the hood to help search engines understand the site better:

- Schema.org structured data was added to all pages. This gives Google more context about what each page contains. The releases page now describes each tool as a free software application with download links and licensing information.
- The Organization schema on the home page now includes the LinkedIn and YouTube pages as verified references for the LEAPPs project.
- A Google Search Console verification tag was added, allowing search performance to be monitored directly.
- Preconnect hints were added for external resources the site uses, which helps pages load faster.
- Open Graph tags including image alt text and locale were standardized across all pages.
- The blog now has RSS autodiscovery so feed readers can find the feed automatically without you needing to hunt for the link.

---

## Back to Top Button

A small gold arrow appears in the bottom right corner of long pages once you scroll down. Clicking it scrolls you back to the top. Useful on pages like Artifacts or Changelog where there is a lot of content.

---

## What Is Next

These updates focused on usability and discoverability. The tools themselves keep moving forward with new parsers and artifact support. Watch this blog and the Changelog page for updates as they land.

If you have suggestions for the website or want to contribute a blog post, open a pull request on the [leapps-website repository](https://github.com/abrignoni/leapps-website).
