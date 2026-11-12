# FAU Cyber Security Club Wiki

The official wiki for the FAU Cyber Security Club at [csc.fau.edu](https://csc.fau.edu). 

This platform uses a **database-less (DB-less)** static architecture coupled with an **event-streaming agentic CI/CD pipeline** and an **interactive Web UI chat harness (Agora/Melete)** for real-time maintenance and direct site updates.

---

## 🏛️ Architecture Overview

```
                          ┌──────────────────────────┐
                          │    External Streams      │
                          │  (Discord, RSS Feeds)    │
                          └────────────┬─────────────┘
                                       │ (Scheduled sync)
                                       ▼
┌──────────────────┐      ┌──────────────────────────┐      ┌─────────────────────┐
│  Web UI (Agora)  │─────▶│  Melete Agent Pipeline   │─────▶│  GitHub Repository  │
│  Chat Interface  │◀─────│  (Autonomous Code/Sync)  │◀─────│  (Git as SSOT)       │
└──────────────────┘      └────────────┬─────────────┘      └──────────┬──────────┘
                                       │                               │
                                       ▼ (Deploy & Sync)               ▼ (CI Gate)
                          ┌──────────────────────────┐      ┌─────────────────────┐
                          │ Live Webroot / Apache    │      │ GitHub Actions      │
                          │ (/srv/www/csc-wiki)      │      │ (hugo --quiet gate) │
                          └──────────────────────────┘      └─────────────────────┘
```

### 1. Database-less (DB-less) Core with Hugo & Relearn
* **Static Site Generator:** Powered by [Hugo Extended](https://gohugo.io/) for high-speed, zero-runtime-dependency static site generation.
* **Documentation Theme:** Built upon the [Hugo Relearn Theme](https://themes.gohugo.io/themes/hugo-theme-relearn/), tailored for structured documentation, technical knowledge bases, and multi-tier club guides.
* **Git as the Single Source of Truth:** No SQL/NoSQL database or CMS backend. Every page is pure Markdown with TOML front matter under `content/`.
* **Zero Runtime Overhead:** Apache serves pre-rendered HTML, CSS, JS, and media directly from `/srv/www/csc-wiki`.
* **Client-side Search:** Lunr-powered instant client-side search generated at build time.

### 2. How Hugo is Used in This Wiki
* **Custom Theme Variants:** Customized Relearn variants (`hacker`, `hacker-light`, `cyber`) configured in `hugo.toml` (`params.themeVariant`), allowing users to toggle visual styles with persistent `localStorage` states.
* **Design Tokens:** The palette is defined once, in `tokens/tokens.json` (W3C Design Tokens format). `python3 scripts/gen-tokens.py` generates the three `assets/css/theme-*.css` files and `tokens/dist/tokens.css` (for other projects) from it, and CI runs `--check` so a hand-edited or stale theme sheet fails the build. See `tokens/README.md`.
* **Chroma Syntax Highlighting:** Configured with `markup.highlight.noClasses = false` to emit semantic CSS classes mapped to custom theme stylesheets (`chroma-hacker.css`, `chroma-cyber.css`).
* **Layout & Partial Overrides:** Tailored templates under `layouts/` to build custom homepage components (interactive owl wireframe canvas, terminal hero, live announcements, meeting schedules, and section grids).
* **Modular Shortcodes:** Reusable shortcodes (`{{< section-grid >}}`, `{{< topic-cards >}}`, `{{< board-feed >}}`, `{{< mark-preview >}}`) for dynamic content presentation without inline HTML.
* **Build Validation & Diagnostics:** Configured with `params.link.errorlevel = 'warning'` and `params.image.errorlevel = 'warning'` to pinpoint dead links and missing assets during compilation.

### 3. Event-Streaming Agentic CI/CD Pipeline
* **Continuous Ingestion:** Scheduled agent runs and streaming scripts poll external feeds (Discord announcements channel, Cyber News RSS) and commit formatted Markdown updates directly into the repository.
* **Autonomous Agents (Melete/Pi):** AI agents perform autonomous code tasks, schema checks, styling updates, and content generation.
* **Strict Build Gate (GitHub Actions):** Enforces a "silence is the pass condition" policy (`hugo --quiet`). Any broken links, missing shortcodes, or bad image paths immediately fail the gate before code reaches production.

### 4. Custom Web UI Chat Box (Agora Interface)
* **Direct Natural-Language Updates:** Club operators can update pages, add events, tweak stylesheets, or trigger builds simply by chatting with the assistant in the Agora control panel.
* **Safe Sandbox Testing:** Edits are tested and validated in isolated agent sessions with instant Hugo validation before syncing to live paths.
* **Private Preview App:** Changes can be previewed at `https://apps.necoconeco.net/csc-wiki/` before going live to the public site.

---

## 🚀 How to Operate the Site

You can manage and deploy the wiki using either the **Web UI Chat Interface** or **Manual CLI Deployment**.

---

### Method A: Via Web UI (Agora Chat)

The fastest way to manage content, news, or site logic:

1. **Open the Agora Web UI** chat session.
2. **Issue instructions in natural language**, such as:
   * *"Add a new workshop page under Learn for Wireshark basics."*
   * *"Pull latest Discord announcements and rebuild the site."*
   * *"Update the executive board listing with the new officers."*
   * *"Deploy the latest main branch to live."*
3. The agent validates syntax, verifies the build with `hugo --quiet`, commits/deploys, and confirms status back to you in chat.

---

### Method B: Manual CLI Deployment (No `sudo` Required)

The webroot `/srv/www/csc-wiki` is preconfigured with `administrator:www-data` ownership and sticky permissions. You can pull, build, and deploy without root privileges.

#### 1. Standard Deploy Cycle
```bash
# Navigate to the wiki directory
cd ~/FAU-CSC-WIKI

# 1. Pull latest commits from GitHub
git pull

# 2. Build static assets with Hugo
hugo

# 3. Rsync directly to the Apache webroot
rsync -rtv --delete public/ /srv/www/csc-wiki/
```

#### 2. Local Development & Preview
To write content locally with live browser reloading:
```bash
# Start local Hugo development server
hugo server

# Browse to http://localhost:1313
```

---

## 📝 Content Conventions

Pages are organized under section folders inside `content/`:
* `start/` — Getting started guides
* `learn/` — Educational resources & tutorials
* `compete/` — CTF & competition writeups
* `lab/` — Club lab infrastructure & guides
* `toolbox/` — Recommended security tools
* `projects/` — Club projects & repos
* `board/` — Officer & advisor roster
* `meta/` — Site policies & operations

### Example Markdown Page
```toml
+++
title = "Network Forensics with Zeek"
weight = 4
description = "Introduction to analyzing network traffic with Zeek."
icon = "fa-solid fa-network-wired"
+++

## Overview
Write your Markdown content here...
```

* `weight` controls page ordering in sidebar menus.
* `icon` accepts any valid [Font Awesome](https://fontawesome.com/) icon class.

---

## 🔄 Discord Sync

Four stdlib-only Python scripts under `scripts/` keep the board, home page,
and schedule current. Each is meant to run on a timer from a dedicated
checkout on the deploy box: it pulls from its source (Discord, an RSS feed,
or — for `fetch-schedule-queue.py` — a local queue file, no network at all),
writes its output file under `data/`, commits as a bot account, and pushes
to `main` only when the result changed. None of them touch git or the
network from CI — `.github/workflows/scripts.yml` only byte-compiles the
scripts and runs `tests/` (stdlib `unittest`) against their pure
text-handling helpers, with no Discord token and no live feed.

| Script | Writes | Env vars |
| --- | --- | --- |
| `fetch-announcements.py` | `data/announcements.json` | `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID` |
| `fetch-postings.py` | `data/discord-postings.json` | `DISCORD_BOT_TOKEN`, `DISCORD_JOBS_CHANNEL_ID` |
| `fetch-cyber-news.py` | `data/cyber-news.json` | none — reads public RSS feeds |
| `fetch-schedule-queue.py` | `data/discord-schedule.json` | `SCHEDULE_QUEUE_PATH` |

`fetch-postings.py` publishes every message in `#jobs` (newest 50, no
reaction needed; deleting the Discord message unpublishes it), skipping only
Discord system messages and messages with no text. It sets `expires` from a
`deadline:` line in the raw message body — several date formats and a
`start - end` range are accepted, see the module docstring — with no
`deadline:` line leaving the posting with no expiry at all. A `deadline:`
line present but unparseable also leaves it with no expiry, but prints a
warning to stdout, since that's a poster's typo worth surfacing. Output
entries carry no `kind`: the board shows one Jobs & Internships list.

The card's `url` (what "Open →" points at) is picked in order: an `apply:`
line's link, same convention as `deadline:`; else the first link in the
message that isn't a known personal-profile URL (`linkedin.com/in/` today —
see `PROFILE_LINK_RES` in the module); else the first link outright; else
the Discord permalink. `layouts/partials/board-feed.html` also linkifies
every http(s) URL inside a posting's own body text, so a reader isn't
limited to the one link the card's button uses.

`data/postings.toml` is a separate, hand-edited file neither script writes
to; `layouts/partials/board-feed.html` merges it with
`discord-postings.json` at render time, so both feed the same board
sections. See [`content/meta/discord-sync.md`](content/meta/discord-sync.md)
for the officer-facing version of this workflow.

`data/discord-schedule.json` is bot-owned like the files above, but with a
different lifecycle: it never rebuilds from scratch. `fetch-postings.py`
re-derives its whole output from the live `#jobs` channel on every run,
but a schedule entry has no equivalent live state to re-scan — there is only
a one-shot queue drain — so `discord-schedule.json` only ever grows on its
own; an `op: "update"` or `op: "delete"` line can still change or remove an
entry by id (see below), and hand-editing the file directly always works
too. Every session on the site now lives in this one file, each with an
id — the hand-written `content/_index.md` `[[params.sessions]]` blocks that
used to hold the schedule were migrated in. That front-matter mechanism
remains only as an escape hatch for a one-off hand entry, which gets no id
and so can't be reached by update or delete.
`layouts/partials/home/schedule.html` merges both sources before sorting,
and shows the id (see below) as a quiet inline note for any row that has
one — a hand-written front-matter session never has one and shows nothing.

`fetch-schedule-queue.py` does not talk to Discord's API and needs no bot
token. It reads `SCHEDULE_QUEUE_PATH`, a local file that something outside
this repo appends one JSON object to per line, one of three shapes:

* An add (`op` absent, or `op: "add"`) — validates the line and appends it
  to `discord-schedule.json` with a freshly assigned `id` (highest `id`
  already in the list, plus one; an entry with no `id` counts as zero).
* An update (`op: "update"`) — looks an entry up by that `id` in
  `discord-schedule.json` and merges validated fields into it in place.
  Zero or more-than-one match drops the line with a warning instead of
  guessing; an update can never touch `id` itself.
* A delete (`op: "delete"`) — looks an entry up by that `id`, same lookup
  as an update, and removes it. Zero or more-than-one match drops the line
  with a warning instead of guessing, same as update.

Either way the queue is validated the same way regardless of who sent it,
and a bad line is dropped with a warning rather than aborting the rest of
the queue. Because `id` is assigned only here and only for bot-owned
entries, an update or delete can never reach `content/_index.md`'s
hand-written `[[params.sessions]]` — that file has no `id` field and this
script does not read it. Once a full write succeeds, the queue file is
truncated.
