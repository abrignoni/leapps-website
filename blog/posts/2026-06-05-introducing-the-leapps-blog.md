---
title: Introducing the LEAPPs Blog
date: 2026-06-05
author: Alexis Brignoni
tags: [announcement, community, contributing]
excerpt: The LEAPPs project now has a blog — a place for artifact deep dives, tool updates, and community write-ups. Here's how it works and how you can contribute.
---

# Introducing the LEAPPs Blog

The LEAPPs project has always been community-driven. Researchers contribute parsers, translators submit language support, and forensic practitioners share feedback that shapes the tools. What's been missing is a dedicated space to go deeper — to explain *why* an artifact matters, walk through a forensic scenario, or document a new tool capability in detail.

That's what this blog is for.

## What you'll find here

- **Artifact deep dives** — detailed breakdowns of what a specific artifact contains, where it lives on the device, and what it reveals during an investigation
- **Tool updates** — when a major feature lands in iLEAPP, ALEAPP, RLEAPP, VLEAPP, or LAVA, we'll explain the context behind it
- **How-to guides** — walkthroughs for parsing, filtering, and interpreting output from the tools
- **Community write-ups** — forensic researchers sharing their own findings and workflows

## How the blog works

Posts are plain Markdown files stored directly in the [leapps-website GitHub repo](https://github.com/abrignoni/leapps-website). There's no CMS, no third-party platform — just a file in a folder and a pull request.

The blog is served through the LEAPPs Cloudflare worker, which caches content at the edge so GitHub rate limits are never an issue.

## How to contribute a post

Anyone can submit a post. Here's how:

### 1. Fork the repo

Fork [abrignoni/leapps-website](https://github.com/abrignoni/leapps-website) on GitHub.

### 2. Create your Markdown file

Add a file to `blog/posts/`. The filename (without `.md`) becomes the post's slug and public URL, so use lowercase letters, digits, and hyphens:

```
your-post-title.md
```

Dating the filename (`2026-06-05-your-post-title.md`) is an optional convention — it keeps the folder sorted — but it isn't required.

Start the file with YAML frontmatter:

```markdown
---
title: Your Post Title
date: 2026-06-05
author: Your Name
tags: [forensics, android, artifacts]
excerpt: A one or two sentence summary shown on the blog index.
---

Your content starts here...
```

### 3. The index generates itself

You do **not** edit `blog/posts/index.json` — it's generated automatically from each post's frontmatter after your post is merged. The `title`, `date`, `author`, `tags`, and `excerpt` fields above become the blog listing. (Maintainers can also add `pinned: true` to keep a post at the top.)

### 4. Open a pull request

Submit your PR against the `main` branch. All posts are reviewed before merging.

## Markdown support

Posts support standard Markdown: headings, bold, italic, lists, links, images, code blocks with syntax highlighting, tables, and blockquotes. Write it the same way you'd write a GitHub README.

## Adding images

Store images in the repo alongside your post — create a folder for your post under `blog/images/` named after your slug:

```
blog/images/2026-06-05-your-post-title/screenshot.png
```

Include the image files in the **same pull request** as your Markdown file, so the post and its images are reviewed and merged together. Then link to them in your post using the jsDelivr CDN, which serves the files straight from the repo. We prefer to have a numbered figure label with a short description below the image. 

Example
```markdown
![Description of the image](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-06-05-your-post-title/screenshot.png)
*Figure 1: example of image in blog post*
```

A few rules:

- **Use the full jsDelivr URL.** Relative paths like `images/screenshot.png` will not work — posts are rendered from a shared page, so image paths must be absolute.
- **Always include alt text** (the part in square brackets) for accessibility.
- Compress images so posts stay fast to load — aim for under ~300 KB each.

---

If you've done forensic research with any of the LEAPPs tools and want to share it, this is the place. Open a PR.

— Brigs
