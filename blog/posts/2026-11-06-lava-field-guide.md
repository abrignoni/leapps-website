---
title: Reviewing, Tagging, and Exporting LEAPP Cases with LAVA
date: 2026-11-06
author: Alexis Brignoni
tags: [LAVA, LEAPPs, DFIR]
excerpt: LAVA is the LEAPPs viewer. It opens the case that iLEAPP, ALEAPP and the rest of the family produce and turns millions of parsed rows into something you can filter, read as conversations, place on a timeline, tag, and hand to someone else. Here is the workflow, start to finish.
---

# Reviewing, Tagging, and Exporting LEAPP Cases with LAVA

The LEAPPs have always been good at getting artifacts out of an extraction. The problem was what came next. An HTML report is fine for a few hundred rows. It is useless for thirty million Unified Log records, or for a messaging database where you need to read one thread in order and then hand only part of it to a reviewer.

That is the job LAVA does. The extractor writes the case. LAVA reads it and gives you the tools to work it.

**Short version:** process the extraction with a current LEAPP, open the resulting `_lava_data.lava` file in LAVA, set your time zone, narrow with filters and the time window, read conversations in context, tag what matters, and export either a quick report or a subset project with provenance attached.

**Long version:** keep reading.

[Download the printable PDF edition](https://leapps-api.4n6-198.workers.dev/downloads/lava-field-guide.pdf).

> **New in 2026.1.0.** LAVA now numbers its releases the way the LEAPPs do, year first, so this release is 2026.1.0. LAVA keeps its own numbers, so do not pair LAVA and LEAPP releases by number. It adds a case-wide time window, a timeline of every artifact, tag roles for privilege review, a check for copies of withheld rows, HTML conversation exports that match what you see in the app, and Brazilian Portuguese. If a section below describes something your copy does not have, update to 2026.1.0 or later.

> **A word before we start.** LAVA is a viewer. It does not parse evidence and it does not change the artifact database. Everything it shows comes from what the extractor wrote. If an artifact looks empty, first clear its filters and the time window. If it is still empty, the question is what the extractor found, not what LAVA hid. Validate the findings that matter against the source data.

## What LAVA reads

A LEAPP run with LAVA output writes a small set of files into the report folder. LAVA needs them to stay together:

| File | Written by | What it holds |
|---|---|---|
| `_lava_data.lava` | The extractor | The project file you open. Run parameters, modules run, the artifact catalog by category, record counts, and how each artifact should be displayed. Older runs wrote `_lava_data.json`, which still opens. |
| `_lava_artifacts.db` | The extractor | The SQLite database with one table per artifact, plus the extractor's media and processed-files tables. This is the evidence-derived working set. Its name comes from the `.lava` file; `_lava_artifacts.db` is the usual one. |
| Media folders | The extractor | Images, video, audio and other files that artifact rows point to. |
| `_HTML` | The extractor | The LEAPP's own report, which holds the device info and run logs LAVA shows. |
| `_lava_work.db` | LAVA | Your work product: tags, tag roles, and the notes on tagged rows. Kept separate from the artifact database. |
| `_lava_filter_records` | LAVA | Term search reports, QC sample records and export records, as JSON and CSV files. |
| `_lava_project.state` | LAVA | Saved view state: column order, hidden columns, sorts and filters per artifact. |

Do not move the `.lava` file out of its report folder. Copy the whole folder if you need to move the case. If the folder is read-only, such as a case on write-protected media, LAVA still opens it but cannot save your work: tagging is off, and column, sort and filter changes are not saved.

LAVA never deletes or rewrites a `_lava_work.db` it cannot use. A tags file it cannot read, or one from an older LAVA build, is left as it is and the case opens with tagging off and a notice that says why. A tags file from a newer LAVA opens read-only with its tags shown. LAVA 0.15.0 and 0.16.0 delete a tags file they cannot read or whose schema version differs, when the folder is writable, so keep a copy of `_lava_work.db` before opening a tagged case in an older LAVA.

## Getting LAVA

### Install a release

For casework, use a packaged build from the [LAVA releases page](https://github.com/leapps-org/LAVA-releases). Builds are made for Windows (installer), macOS (disk image) and Linux (AppImage, and a snap on x64), on x64 and arm64, and already include everything LAVA needs, including its SQLite natural-sort extension. No Python, no Node.js, no compiler.

### Run from source

The source repository is private, so running from source needs access to it. You also need git, Node.js 22.12 or later for your machine's architecture, and a C compiler (Visual Studio Build Tools with **Desktop development with C++** on Windows, `xcode-select --install` on macOS, `build-essential` on Debian or Ubuntu). `npm ci` needs an internet connection.

```
git clone https://github.com/abrignoni/LAVA.git
cd LAVA
npm ci
npm run dev
```

Use the Electron window that opens, not the development URL in a browser; the browser cannot read case data. Press `Ctrl+C` in the terminal to stop. Do not copy `node_modules` between computers. If Electron complains about a SQLite module mismatch, run `npm ci` followed by `npm run postinstall`.

## Opening a case

1. Process the extraction with a LEAPP release that writes LAVA output.
2. Start LAVA and click **Open Project**.
3. Select the `_lava_data.lava` file in the report folder.

The home screen keeps a **Recent Projects** list, so reopening a case is one click. The trash icon (**Remove from this list**) only forgets the entry; it never touches the case. The X at the top right (**Close Project**) asks you to confirm, then returns you to the home screen.

### Check the project before you trust it

When a case opens, LAVA shows its project page, and the house icon at the top left brings you back to it. Start there. It is the run record, and it belongs in your notes:

- **Project Overview**: the case details entered in the LEAPP (case number, examiner and agency, when given), the tool and version, start and end times and duration, the input and output paths, and each module run with its file and record counts.
- **Device Info**: what the extractor learned about the device.
- **Processed Files Log**: every search pattern each module used and every file it matched, with path, kind, SHA-256 and file-system times. Times the source stored without a zone are labeled *as stored* rather than converted. Older LEAPP runs show the extractor's HTML processed-files log instead.
- **Screen Output**: the extractor's run log.

If a module reports zero files, check the Processed Files Log for its search patterns and what they matched.

## Set your display before you read

Open **Display Settings** (the gear icon) before you start reading timestamps. These settings change how values are shown, never what is stored in the case:

- **Timezone**: every date and time LAVA converts renders in this zone, including the run times on the project page, the time window, the timeline and the conversation heatmap. Date-only columns and times stored without a zone are shown as stored.
- **Date Format** and **Time Format**.
- **Phone Number Format**: the raw value (the default), national or international. Numbers are read with no default country, so a number stored without a leading + and country code is likely to stay as stored.
- **Theme Settings**: light or dark.
- **Language**: English, Spanish, French, German, Portuguese, Brazilian Portuguese and Italian, or use the system language. Artifact names and most column headers stay as the extractor wrote them in every language.

> Work in UTC unless the case requires a documented local-time presentation. When you do switch zones, write down which one your screenshots and exports used. HTML files, and conversation exports with the metadata header, name the zone. CSV, TSV, the Word/Outlook table, JSON, XML and the Timeline CSV do not. CSV, TSV and the Word/Outlook table show a UTC offset in each time only when your time format includes one (the default does); JSON and XML hold the stored values.

### Look inside a value

Columns the extractor typed as dates, times, phone numbers, coordinates or numbers get a small info icon. Hover it to see what LAVA knows about the value. Media details sit behind the Info button in the full-size preview. The detail panels are where you confirm a conversion instead of assuming it. Columns the extractor did not type show the stored value with no panel.

| Value type | What the detail panel shows |
|---|---|
| Date and time | ISO UTC, Unix epoch, the value in UTC, your configured zone and your local zone, whether daylight saving applies, day, week, quarter, leap year, and distance from today. Day, week, quarter, leap year and daylight saving are worked out in your configured zone. |
| Phone number | Raw value, country and country code, national and international formats. Values LAVA cannot parse show as stored, with no panel. |
| Coordinate | The stored decimal degrees, degrees and decimal minutes, and degrees, minutes and seconds, plus a warning when a value is outside the valid latitude or longitude range. |
| Number | As stored, with digit grouping. Whole numbers also show hexadecimal and binary. LAVA reads integers as JavaScript numbers, so an integer larger than 2^53 (about 9 quadrillion) is shown, copied and exported rounded, JSON and XML included. An artifact holding one says so in a line at the top. LAVA project exports keep the stored value. Check large IDs in the database. |
| Media | Images preview in the row. The full-size preview lists the Source Path (where the file was in the evidence), the Extraction Path (the copy in the report), type, and created and updated times. Video and audio, including AMR, open in a player when clicked. |

## Navigating artifacts

The artifact menu on the left groups artifacts by category, the same categories the extractor reported. Each category and artifact shows its counts in the menu; hover for the full wording. Type in **Search Artifacts** at the top of the menu to narrow it to matching artifact or category names.

An artifact whose view you customized shows a marker in the menu. Hover it to see what changed (filters, sort, hidden columns, column order). Right-click an artifact for **Copy artifact name**, **Artifact Information** and **Reset view to defaults**, which asks first and cannot be undone.

**Artifact Information** shows the module that produced it, the author, created and last-updated dates of the parser, its description and notes, and the source path, when the case carries the module's details. Otherwise it shows the module, name and record count. When someone asks how a row was produced, start there.

Your view state saves automatically when the case folder is writable. Use the arrow beside the save button in the toolbar to switch to manual saving, then click the save button when you want the view written.

## Working the table

Every artifact opens in the table view. It reads straight from SQLite one page at a time (100 rows by default, up to 5,000), so a very large table pages and sorts without loading it all into memory.

### Sorting and columns

- Click a column header to sort. Text sorts naturally: `item2` comes before `item10`. Hash columns sort as text, ignoring letter case.
- **Columns**, under the table, opens **Manage Columns**, where you hide, show and drag columns into order. A column with an active filter cannot be hidden until you remove its filter, so a filter is never silently in force on something you cannot see.
- Right-click a cell to copy the value or the whole row (the visible columns, as shown on screen). **View row details** opens one row as a vertical list, with Previous and Next to move through the rows on the current page.

### Column filters

Each column header has a filter. Filters on several columns combine, and **Clear All Filters** removes this artifact's filters and sort. It does not touch the time window.

| Filter | How it works |
|---|---|
| Values | Lists the distinct values in the column with a search box. Tick the ones to keep. `(Blanks)` covers empty cells. Long lists stop at 500 values and say so; search to narrow them. |
| Condition | Contains, does not contain, equals, does not equal, starts with, ends with (and their negatives), is empty, is not empty. Matching ignores A to Z letter case. With **Use wildcards**, `*` matches any text and `?` one character; type `\*`, `\?` or `\\` for a literal asterisk, question mark or backslash. Negative conditions exclude blanks. |
| Date range | On date columns, pick a first and last day (for time columns, whole days in your display time zone; for date-only columns, the stored date). **Move to Earliest** and **Move to Latest** set the start of the range to the first or last date in the column. |
| Phone number | On phone columns, numbers are grouped by country, and numbers that cannot be parsed go under Invalid Numbers. The search matches the text as stored, and the list holds only the first 500 distinct numbers, so use Find in all artifacts to match a number in any format. |
| Tags | Filters to rows carrying the tags you pick. |

## Reading conversations

When the extractor declares a conversation view for an artifact, such as SMS and iMessage or a third-party chat app, the **Conversation** and **Analytics** options of the Table, Conversation and Analytics switch become available. The conversation view groups the rows into threads and shows them as message bubbles, sent on one side and received on the other, with media inline.

- The left panel lists conversations. Sort it by name, total, sent or received count. Hover a conversation for its counts.
- **Filtered** is on by default whenever the table has filters, so the conversation list and threads follow those filters. Messages that are filtered out fold into markers such as *12 messages filtered out*, so you always see where the gaps are. Turn Filtered off to see every thread in full. The time window applies either way.
- **Columns** (beside Export PDF) adds more fields to each bubble, such as status or service center. A module's suggested list is on by default; **Use suggested list** puts it back after you change it.
- **View in table** on a message filters the table to that conversation's rows (remove the filter when you are done). **View in conversation** on a table row opens the thread and scrolls to that message.
- **Tag conversation** tags every message in the thread, including messages hidden by filters or the time window. From 2026.1.2, with the window on, the notice says how many of the tagged rows are outside it.

### Conversation analytics

**Analytics** summarizes the artifact's rows inside the time window and, while Filtered is on, the table filters: totals of conversations, messages, sent, received and messages with media; the busiest conversations; top senders (who sent the received messages) and top receivers (the conversations the device sent the most messages to); the most one-sided conversations in each direction (threads with at least 5 messages); the conversations with the most media; an **Activity by day and hour** heatmap (All, Sent or Received, with a Combined row) in your display zone; and an **Activity over time** chart across the full date range.

Patterns jump out here. A thread that is almost entirely one direction, or activity clustered at odd hours, is worth a closer read. Any message the module did not mark as sent counts as received, so check the direction column before you rely on the split.

### Export a conversation

Select a conversation and use **Export PDF**. The export matches the preview in the dialog: each bubble carries its tags and any additional columns you turned on, and the table filters apply only while Filtered is on. Choose the format:

- **PDF**: Letter or A4. PDFs always render in light colors for printing.
- **HTML**: one file with its styles inside it and the media copied into a folder beside it, so it stays small. Keep the file and folder together. Video and audio messages get a player with the file link below it; formats browsers cannot play (AMR, 3GP, CAF) keep the link only. Choose **As in LAVA** for your colors or **Light, for printing**. Copied files are renamed (numbered, unsafe characters replaced).

A media file the case does not hold shows as *File not found in the case* with its name, in the app and in both formats, and the dialog tells you how many were missing. A file LAVA finds but cannot show says *This file could not be shown*. From 2026.1.2, untick **Media** in the dialog to leave the media files out; the export says *Media not included in this export* where each attachment was.

Keep **Include Metadata Header** ticked (the default). The header records the project folder, module and artifact, the LAVA version (and the LEAPP version when the case has it), the export time, the conversation ID, participants (the senders seen in the thread), the date range and message total for the whole conversation, the number of messages in the export when filters or the time window narrow it, and the time zone and date format. The dialog's export language starts at English; change it if you need another. If the export was filtered, the header says so and lists the filters, because a filtered export may not represent the whole conversation. A progress count shows while media is copied.

## Narrowing by time

### The time window

**Time window** in the toolbar applies one time range to the whole case: every artifact table, every count in the menu, every conversation list, and Find in all artifacts. Inside a conversation, messages outside the window fold into filtered-out markers. A chip in the toolbar shows the active range; click it to change it.

Choose how each row is tested:

- **First timestamp**: tests each artifact's first datetime column. The LEAPPs put the event time first by convention; LAVA does not check it. This is the default and the one the timeline uses.
- **Any timestamp**: keeps a row when any of its datetime columns falls in the range.

Artifacts with no datetime column (an artifact with only date columns counts) cannot be tested, so they are shown in full and marked as untimed. Tick **Hide untimed artifacts** to show none of their rows instead. From 2026.1.2, such an artifact says it has no timestamp column and is hidden by the time window, where it used to show only *No data*.

> **Read this part carefully.** The time window does not apply to Tagged Rows, tag exports, the QC sample or the Timeline, which only shades it. The window tests the evidence times in each row, not when you tagged it. Rows with no time in the tested column drop out whenever the window is on, however wide it is. Tagging is the exception that goes the other way: **Tag hits** and **Select all N matching rows** tag across the whole case even with a window on, because a withhold export covers the whole case. LAVA says so before it tags.

### The timeline

**Timeline** draws one lane per category with events in view, each counting rows over time by their first timestamp column. Open a category to see a lane per artifact. Lanes with nothing in view are hidden unless you turn Hide empty lanes off.

- Drag across the lanes to zoom. Bar width follows the zoom, down to seconds. **Back** returns to the previous zoom, **Full range** to the whole case.
- Bars use the zone's offset at the start of the view, so across a daylight saving change later bars can sit an hour off. Zoom to either side of the change to read exact hours.
- Each lane has its own scale; compare bars within a lane, not across lanes. **Log scale** keeps small counts visible next to large ones.
- The opening view covers the middle of each artifact's events. In a case with 50 or more timed artifacts it also leaves out the few artifacts at the extremes, such as one holding only zero times (1601 or 1970) or future dates. Events outside the view are counted at the lane edges; click a count to go there. In a smaller case a stray time can stretch the opening view, so check **Full range** too.
- Click an artifact's bar to open those rows in the artifact. A category bar expands that category's artifact lanes. Opening a bar replaces that artifact's column filters with one date filter, which stays afterwards. If the time window is on, the table can show fewer rows than the bar. **Back to Timeline** returns you to the same place.
- Switch to **List** to read the events in view in time order, with artifact, timestamp column and a summary of each row (from 2026.1.2, a message row's summary leads with the sender and the message text). The list holds at most 100,000 events; if a view holds more, zoom in first.
- From 2026.1.2, **Leave out categories** above the List drops whole categories from the List and its export, for example unified log lines that bury the messages and calls around them. The 100,000 limit counts only the events listed. The HTML export names the categories left out, and its suggested file name ends in `_filtered`. The lanes still show every category.
- **Use as time window** sets the case-wide time window to the range on screen. It tests the first timestamp and does not hide untimed artifacts.
- In List, **Export** writes the events in view as CSV for Excel, or as HTML (up to 10,000 rows) to read and print. The HTML file records the range, time zone and basis; the CSV holds the rows only.

The panel below the lanes lists what is **not on the timeline**: artifacts with no datetime column, and artifacts that have one but no usable times. Absence from the timeline is not absence from the case.

## Find in all artifacts

**Find in all artifacts**, in the sidebar, searches every column of every artifact at once. It has two modes: **Search** and **Term lists** (below).

In Search, type a term and press Enter to make it a chip, and add as many as you need. Enter on an empty box runs the search. The results line reads like *2,037 matching rows in 94 of 541 artifacts*, and the table lists each artifact with its matching rows and how many hits each term had in it. Click **Open** to go to an artifact with the hits filtered in under a *Search:* chip (this replaces that artifact's column filters); **Back to search results** returns you to the same list.

How terms match:

- Matching ignores case for A to Z only. Accented and non-Latin letters match only as typed.
- A term made only of digits and phone punctuation, with seven or more digits, matches on digits alone, so `(555) 123-4567` also finds `+15551234567`. Only the last ten digits are used, and the term can also hit any longer number that contains those digits, such as an ID. Dates and IP addresses typed with dots or dashes get the same digits-only matching. Find matches stored values, not the displayed format, so a date typed as LAVA shows it will not find a stored epoch time.
- A term also matches a media row when the file's name, source path or extraction path contains it, so a folder name can hit every media row under it.

When the time window is on, only rows inside it are counted, and the results say so. Untimed artifacts are searched in full, unless Hide untimed artifacts is ticked, in which case they are skipped. Tagging the hits still covers the whole case: LAVA asks first, with the number of rows across the case and the number inside the window, and tags them all. The record it writes names every tagged row.

From 2026.1.2:

- The button you clicked shows the progress, as *Searching 42%*, *Tagging 42%* or *Saving 42%*, with a thin line under it. Progress moves through large tables instead of sitting on one. Hover the button to see the artifact being searched and its row count.
- Click the running button to cancel. A cancel stops before anything is written: a cancelled tagging tags nothing, a cancelled report saves nothing, and a cancelled search keeps the previous results.
- **Tag hits** and **Save report** run the search again before they write, so on a large case they take a while too.
- Leaving the page does not stop a run, and coming back shows it still going.
- Cases with very wide artifacts (two Photos.sqlite artifacts have 851 columns) no longer make a search with two or more terms, or a phone number, fail and return nothing.

### Term lists for privilege review

Switch to **Term lists** when you are filtering for privilege. Enter **Attorney terms** (lawyer names, email addresses, phone numbers, firm names; hits are presumed privileged) and **Generic terms** (words like *attorney* or *legal advice*; hits are for review), one per line. Example terms from a federal filter protocol can be added to start from.

From the results, tag attorney hits and generic hits separately (in plain search, **Tag hits** tags every hit). When you tag hits or click **Save report**, LAVA writes a record to the case's `_lava_filter_records` folder: the terms and how each matched, with the matching row IDs in the JSON file and the counts in the CSV. On a read-only case folder, hits cannot be tagged.

> Term hits are a starting point, not a decision. A hit can be a business conversation, and privileged rows can miss every term. Review the tagged rows before you export anything.

## Tagging rows

Tags are how you mark what matters. They live in `_lava_work.db`, next to the case, and never modify the artifact database.

### Create and apply

1. Tick rows in any artifact table, then use **Apply Tag**, **Remove Tag** or **Clear selection** in the bar above it.
2. Choose an existing tag or **New tag…**. A tag has a name, a color and a role.
3. To tag every row that matches the current filters, not only the ones on screen, use **Select all N matching rows** first. With a time window on, it selects the matching rows across the whole case, says how many are inside the window, and the bar then shows how many selected rows the window hides. **Remove Tag** on that selection removes from those rows too.

Each row shows its tags in a pinned **Tags** column. Click a row's tag cell to edit its tags; if the row is part of a selection, the edit applies to the whole selection. LAVA keeps, for each tag on a row, the time it was applied by this computer's clock. If a tag is removed and applied again, only the later time is kept.

### Roles

| Role | Use it for | Default in a withhold export |
|---|---|---|
| No role | General marking: items of interest, suspect communications. | Withhold |
| Privileged | Rows a reviewer must not see. | Withhold |
| Needs review | Hits nobody has decided on yet. | Blocks any withhold export while any row in the case still carries it, even when that tag is not part of the export |
| QC sample | Rows drawn by the QC sample. | Ignore |

### Examiner notes

Add a free-text note to a tagged row from its tag cell, or a note on a tag itself in **Manage tags**. A row note belongs to the row's tags: removing a row's last tag deletes its note, and LAVA asks before doing that. Deleting a tag removes it from every row but never changes evidence data.

### The Tagged Rows hub

**Tagged Rows** collects everything you tagged from every artifact in one place. The hub always lists every tagged row in the case. Filter by tag, then use **Open in artifact** to see an artifact's tagged rows in its table. That table applies the time window, so clear the window there to see them all. From here you start exports, conversation PDFs and the QC sample.

### QC sample

Terms and tags only catch what they catch. **QC sample** draws a random sample of untagged rows so you can check by hand what everything else missed. Set the number of rows, a minimum per artifact so small artifacts are not skipped, and a seed. Shares are rounded and capped per artifact, so the number drawn can come out above or below the number asked for. The seed and counts go into the tag note; the method and sampled row IDs go into a QC sample record in `_lava_filter_records`. The same seed draws the same rows only while the set of untagged rows is unchanged, and the draw itself tags the rows it picks.

### Tag integrity

When a row is tagged, LAVA stores a hash of its content. It also compares the artifact database's size and SQLite change counter with what it saw while you tagged. If either differs when you open the case, for example because `_lava_artifacts.db` was replaced or an edit to it was saved in another tool, LAVA warns that tagged rows may no longer match. That check is cheap, so it can miss a change that keeps both values the same. A LAVA project export checks the tagged rows it uses against their stored hashes before writing (when sharing, a row with no stored hash goes out unchecked). The HTML report and conversation PDFs are not checked.

## Exporting

### Quick exports from a table

The export button under an artifact writes rows to a file or the clipboard. Choose the rows (all, filtered, or selected), the columns (all or visible), and the format:

- To the clipboard: **TSV (for Excel)**, **CSV (as text)**, or **Table (for Word/Outlook)**.
- To a file: **CSV**, **JSON**, **XML** or **HTML**. Images go inside the HTML file itself; video and audio are not included. From 2026.1.2, untick **Media** to leave the pictures out of the HTML.

Only **Filtered rows** applies the column filters and the time window; **All rows** and **Selected rows** do not. JSON and XML hold the stored values, not the formatted values on screen (integers larger than 2^53 are rounded there too).

HTML is off for a table export of 10,000 rows or more and for a Timeline list or Tagged Rows report over 10,000, because larger files are slow or impossible to open. LAVA turns HTML off rather than cutting the file short, and a table export of 5,000 rows or more warns that it may be slow. CSV has no such cap, though the Timeline list itself holds at most 100,000 events. For more, use CSV or a subset project. Conversation HTML has no row cap, but the page must render within 60 seconds or the export stops with an error. HTML files also show the case information and agency logo recorded at extraction (in conversation exports, only with the metadata header on).

### Exporting tagged rows

**Export…** in the Tagged Rows hub is the guided export for sharing work product. It runs in three steps, or four when withholding:

1. **What**: *Only the tagged rows* (share what you tagged) or *Everything except the tagged rows* (withhold privileged rows from a reviewer).

> **Withholding covers every tag.** Sharing uses only the tags ticked in the Tagged Rows filter. Withholding ignores the ticks: every tagged row in the case is kept out unless you set its tags to Ignore or Redact in the Tags step, and LAVA checks the tags file itself and refuses to write if any tagged row would reach the reviewer.

2. **Tags** (withholding only): set each tag's action. *Withhold* leaves the row out. *Redact* keeps the row and blanks the columns you pick: text cells read `[REDACTED]`, other cells and media are left empty (a column that cannot be empty also reads `[REDACTED]`), and the original values are never written. *Ignore* means the tag has no effect. A row with any Withhold tag is withheld.
3. **Options**: the format (only when sharing tagged rows; withholding always makes a LAVA project) and a case note shown to whoever opens the export. A LAVA project adds a production label such as *Release 1*, **Replaces**, the run log and processed-files list, and the source folder name and paths. An HTML report adds media, dark mode, and the source folder name and path. The run log and paths start off when withholding and on when sharing tagged rows, because file paths and folder names can name a client, an attorney or a privileged file. Check them every time. From 2026.1.2, a LAVA project also has **Media**: untick it to leave the media files out. Media cells are left empty, the export record says media was left out, and the shared-media check is skipped because no file goes out.
4. **Review**: the rows exported (when sharing) or the rows withheld and redacted (when withholding), with a checklist before you send it when withholding.

The two formats:

| Format | What you get |
|---|---|
| LAVA project (subset) | A complete project that reopens in LAVA with its media, and with its tags when you shared tagged rows (a withhold export carries no tags). It opens with a **SUBSET** banner, and its provenance panel records the SHA-256 of the source `.lava` file and database, the LAVA version and time it was made, the tags used (or, when withholding, how many rows were withheld), rows redacted, the integrity result, which export it replaces, and the source project name and path when you chose to include them. Recommended for anything media-heavy. |
| HTML report | One file for quick review or case notes, with images inside it and video and audio linked from a media folder beside it. Dark mode starts on when LAVA uses the dark theme. With **Source folder name and paths** unticked, it leaves out the case folder name and the source path. |

**Conversation PDFs** in the hub writes one file per conversation (PDF or HTML) holding only the tagged messages, with the module's suggested bubble columns. Untagged messages show as filtered gaps, and the metadata header (on by default) records the filter.

### Leak checks in withhold exports

Withholding is where mistakes are expensive, so LAVA checks before it writes:

- **Needs review**: any row still tagged Needs review stops the export. This cannot be skipped.
- **Integrity**: tagged rows that no longer match their content, or are missing, are listed. When sharing tagged rows, missing rows are left out and you choose whether to include changed ones. When withholding, any such row, a row with no stored hash, or a database that changed since tagging stops the export with no override.
- **Shared media**: a media file stays in the export when any kept row points to it, even if a withheld row points to it too. LAVA lists those files and lets you tag the kept rows before continuing.
- **Copies**: the same content can sit in another artifact, such as a second message table, a recovered-records artifact or a timeline. LAVA lists kept rows whose text exactly matches a cell in a withheld or redacted row so you can tag them too. Only text of 8 or more characters (trimmed) in text columns is compared, and for redacted rows only the cells being redacted, and a value found in more than 5 kept rows is listed as common and not offered for tagging, so check those by hand. Text inside a longer cell is not found by this check.

Shared media and copies can be passed with **Export without tagging**. The export record in `_lava_filter_records` then lists each kept file and copy, and the common values that were not offered. Needs review and withhold integrity cannot be passed. A clean copies check means no exact match, not that nothing privileged is left.

### Replacing an earlier production

If this export corrects an earlier one, use **Replaces** (LAVA project only) to choose the earlier subset. It must come from the same database. When the export finishes, LAVA reports the rows removed and changed (claw these back) and the rows added, and lists them in your filter records.

## Things to keep in mind

- LAVA shows what the extractor wrote. An empty artifact does not prove an event never happened.
- Record your display time zone. HTML files and conversation exports with the metadata header name it; CSV, TSV, JSON, XML and the clipboard formats do not.
- Use the time window to focus, but remember untimed artifacts and rows with missing times behave differently. Tagging from Find and Select all matching covers the whole case whatever the window shows.
- Tags and notes are work product in `_lava_work.db`, and the records of searches, samples and exports are in `_lava_filter_records`. Keep both with the case and back them up.
- Reprocessing an extraction gives you a new case: every LEAPP run writes its own new folder, so the new case starts with no tags. Tag it from scratch.
- The artifact database of a tagged case should never change. If someone replaces `_lava_artifacts.db` or saves an edit to it, the tags fail the integrity check and a withhold export from that case stays blocked. Each blocked attempt is recorded in `_lava_filter_records` as a `withhold_blocked_` file with the database's size and change counter at tagging and now. To get past it, keep a copy of `_lava_work.db` as your record, remove every tag, reopen the case, and tag again.
- Check the provenance panel when you receive a subset. It gives the SHA-256 of the source it was cut from, and its name and path when the sender included them.

## Research and tools

- [LAVA releases](https://github.com/leapps-org/LAVA-releases): packaged builds for Windows, macOS and Linux.
- [iLEAPP](https://github.com/abrignoni/iLEAPP), [ALEAPP](https://github.com/abrignoni/ALEAPP) and the rest of the LEAPPs: the extractors that produce LAVA cases.
- [leapps.org](https://leapps.org): LEAPPs news, field guides and the artifact browser.
- [DB Browser for SQLite](https://sqlitebrowser.org): for running SQL against the case database (usually `_lava_artifacts.db`). Open it read-only; any saved change sets off tag integrity warnings.

## Before you call it done

- Open the project page and record the tool, version, input and modules run.
- Check the Processed Files Log for modules that found nothing.
- Set and record the display time zone.
- Validate important values in the detail panels instead of trusting a rendered format.
- Review every Needs review tag before a withhold export, and check each tag's action in the Tags step.
- Run a QC sample and record its seed.
- Resolve integrity, shared-media and copy warnings; do not click past them.
- Keep run logs and source paths out of reviewer exports unless they are needed. Media of kept rows goes with a reviewer export unless you untick Media (2026.1.2 and later), so use the shared-media check.
- Keep the source case, `_lava_work.db`, the `_lava_filter_records` folder and every export you produced.

Parse it. Open it. Work it in LAVA. And when something in the viewer slows you down or a view is missing, open an issue. That is how the tool grows.
