+++
title = "Authoring"
weight = 1
description = "How to write and submit wiki pages, the shortcode reference, and Hugo config for deeper edits."
+++

---

# So You Want to Help Write the Wiki?

This wiki is a community effort. Every page someone writes makes it more useful
for the next person who joins. You do not need to be a developer to contribute —
if you can write Markdown and use GitHub, you can add pages.

This guide covers two paths:

- **Just writing content** — the fast path. No local setup needed.
- **Full local setup** — for previewing changes before submitting, or making
  deeper edits to the site config and theme.

---

## Path 1 — Just Writing a Page

If you only want to add or edit content, you do not need Hugo installed. The
wiki is just Markdown files. You can write one, open a pull request, and someone
will review and merge it.

### 1. Fork and clone the repo

```bash
git clone https://github.com/dxcently/FAU-CSC-WIKI.git
cd FAU-CSC-WIKI
```

### 2. Create your file

All content lives under `content/`. The structure looks like this:

```
content/
├── _index.md                     # Home page
├── start/
│   └── _index.md                 # Section landing page
├── toolbox/
│   └── _index.md
└── your-section/
    └── your-page.md              ← your file goes here
```

Create a `.md` file in the right section. Every page needs a front matter block
at the top:

```toml
+++
title = "Your Page Title"
weight = 2
+++
```

- `title` — shows up in the sidebar and as the page heading
- `weight` — controls order in the sidebar (lower number = higher up)
- Add `type = "chapter"` for section landing pages to get the big header style

Write your content in plain Markdown below the front matter. That is it.

### 3. Submit a pull request

```bash
git checkout -b my-new-page
git add content/
git commit -m "add page: your topic here"
git push origin my-new-page
```

Open a pull request on GitHub. Someone will review it and merge it in.

---

## Path 2 — Full Local Setup

Do this if you want to preview the site before submitting, or if you are making
changes beyond content — config, menus, theme, etc.

### Install Hugo

{{< tabs >}} {{% tab title="Linux" %}}

```bash
sudo snap install hugo
```

{{% /tab %}} {{% tab title="macOS" %}}

```bash
brew install hugo
```

{{% /tab %}} {{% tab title="Windows" %}}

```bash
winget install Hugo.Hugo.Extended
```

{{% /tab %}} {{< /tabs >}}

Verify:

```bash
hugo version
```

### Run the dev server

```bash
hugo server
```

Open [http://localhost:1313](http://localhost:1313). The page live-reloads on
every save. Use this to check that your page looks right before submitting.

### Build the site

```bash
hugo
```

Outputs the static site to `public/`. You normally do not need this unless you
are deploying.

---

## Editing the Meeting Schedule

The schedule on the home page is the thing you will edit most. It lives in the
front matter of `content/_index.md` — not in a database, not in the theme. You
edit Markdown, the site rebuilds, the page updates.

### Add a meeting

Open `content/_index.md` and add one block per meeting:

```toml
[[params.sessions]]
  date  = "2026-10-02"
  title = "Active Directory workshop"
  track = "learn"
  lead  = "Officers"
  link  = "/learn/windows/active-directory/"
```

| Field | Required | What it does |
| ----- | -------- | ------------ |
| `date` | yes | `"YYYY-MM-DD"`, in quotes. Drives everything below. |
| `title` | yes | What the meeting is about. Keep it one line. |
| `room` | no | Where it is. Leave it out and the row inherits the weekly room from `[params.meeting]`. Set it only when a session moves — another room, another building, or `"Online"`. An overridden room is highlighted so nobody skims past it. |
| `track` | no | Free text label shown on the right (`general`, `learn`, `compete`). |
| `lead` | no | Who is running it. |
| `link` | no | Where to send people who want to prepare. Internal paths start with `/`. |
| `status` | no | Manual override. See below. |

### The site works out the rest

You do not mark meetings as finished. The page compares each date to today:

- date in the past → dimmed and struck through
- date is today → **TODAY**, red bar
- first date still ahead → **NEXT**, red bar
- anything after that → plain upcoming row

Only one row ever gets a red bar. If a meeting is today, nothing is marked
NEXT.

### Overriding a row

Set `status` by hand only when reality disagrees with the calendar:

```toml
  status = "cancelled"   # meeting called off — row is struck through
  status = "moved"       # date changed; say what happened in the title
  status = "done"        # force a row to read as finished
```

### Order does not matter

Rows are sorted by date when the site builds. Add new meetings anywhere in the
list.

### Changing the recurring details

Day, time, and room live in one place near the top of the same file:

```toml
[params.meeting]
  day   = "Thursday"
  time  = "5:00 – 7:00 PM"
  room  = "CM 22"
```

Change the semester label and the note under the table in `[params.schedule]`.

---

## Adding a Page

Where a file lives decides where it appears. There is no separate menu to
update.

### Add a page to an existing section

Create `content/<section>/<name>.md`. Example — a new page under Linux:

```
content/learn/linux/systemd.md
```

```toml
+++
title = "systemd"
weight = 4
description = "What systemd does, and how to read a unit file."
+++
```

`weight` orders it against its siblings — lower numbers come first.
`description` is the sentence shown on the section's card grid, so do not skip
it.

### Add a whole new section

Create a directory with an `_index.md` in it:

```
content/learn/cloud/_index.md
```

```toml
+++
title = "Cloud Security"
weight = 10
description = "One sentence about what this section covers."
icon = "fa-solid fa-pen-ruler"
+++
```

Then add `{{</* section-grid */>}}` at the bottom of that `_index.md` and the
section lists its own child pages automatically.

### Editing a page that already exists

Find the file, change the words, save. Two things to keep in mind:

- **The URL comes from the file path.** Renaming a file breaks every link to
  it. If you must rename, either add `slug = "old-name"` to keep the old URL,
  or grep the repo for the old path and fix every link:
  ```bash
  grep -rn "old-page-name" content/
  ```
- **`description` is what other pages show.** If you change what a page is
  about, change its description too — it appears on the parent section's card
  grid, not just in the file.

### Moving or deleting a page

```bash
git mv content/learn/linux/old.md content/learn/linux/new.md
grep -rn "linux/old" content/          # then fix what turns up
```

Deleting is the same minus the move. Always grep first — a dead internal link
is invisible until someone clicks it.

### Reordering pages

`weight` sorts siblings, lowest first. Leave gaps (10, 20, 30) so you can slot
something in later without renumbering everything.

### Checking your work before you push

```bash
hugo server        # http://localhost:1313, reloads as you save
hugo --quiet       # must print nothing at all
```

`hugo --quiet` printing *nothing* is the pass condition. Any output is a
problem, including warnings.

Then look at the page in the browser. A page that builds is not a page that
reads well:

- Does it appear in the sidebar where you expected?
- Does its card show a sensible description on the parent section?
- Do your links go where you meant?
- Does it look right narrow? Drag the window thin, or open it on your phone.

### Common mistakes

| Symptom | Cause |
| ------- | ----- |
| Page does not appear at all | Missing front matter, or the `+++` delimiters are `---` |
| Page appears but the section does not | The directory has no `_index.md` |
| Blank card on the section grid | No `description` in front matter |
| Wrong order in the sidebar | `weight` missing or duplicated between siblings |
| Link 404s | Missing leading `/`, or missing trailing `/` |
| Build warning about `relref` | Use a plain `/path/` link instead of the `relref` shortcode |
| Your CSS change did nothing | You edited `themes/` — that is a submodule; use `assets/css/custom.css` |

### Writing style

Read `AGENTS.md` in the repo root — it carries the voice, the policy rules,
and the plain-English guidelines every page follows. The short
version: short sentences, active voice, define jargon the first time you use
it, no filler, and never publish anything that points a reader at a system
they are not allowed to touch.

### Rules that keep the site consistent

- Every page needs `title`, `weight`, and `description`.
- Section landing pages are `_index.md`. Everything else is `<name>.md`.
- Internal links start with `/` and end with `/` — `/learn/linux/permissions/`.
- Do not edit anything in `themes/` — it is a submodule and your changes will
  be lost. Site-wide styling goes in `assets/css/custom.css`.
- Do not hand-edit `public/` — it is generated output.

---

## Shortcodes (Fancy Formatting)

Shortcodes are Hugo's way of doing things plain Markdown cannot. Use them
sparingly — plain text is usually enough and easier to maintain.

| Shortcode   | What It Does                                     |
| ----------- | ------------------------------------------------ |
| **Notice**  | Callout boxes (tip, warning, info, caution, etc) |
| **Tabs**    | Tabbed content for OS or environment differences |
| **Expand**  | Collapsible sections for optional content        |
| **Mermaid** | Diagrams and flowcharts rendered from text       |

---

### Notice (Callout Boxes)

Use when something needs to stand out — a warning, a tip, a gotcha. Two syntax
options; both work the same way.

Short form (simpler to write):

```
> [!tip] Pro Tip
> Your tip text goes here.
```

Shortcode form (more control over the title text):

```
{{%/* notice style="warning" title="Heads Up" */%}}
Something the reader should not skip.
{{%/* /notice */%}}
```

Swap `style=` for: `tip`, `warning`, `info`, `note`, `caution`, `important`

---

### Tabs

Use tabs when the same instructions differ by OS or environment and stacking
them vertically would be cluttered.

Wrap everything in `tabs`, then put each option in its own `tab` block. The
`title=` value is what appears on the clickable tab.

```
{{</* tabs */>}}
{{%/* tab title="Linux" */%}}
Your Linux instructions here.
{{%/* /tab */%}}
{{%/* tab title="Windows" */%}}
Your Windows instructions here.
{{%/* /tab */%}}
{{</* /tabs */>}}
```

Any normal Markdown works inside a tab block — code, lists, paragraphs.

---

### Expand (Collapsible Sections)

Use for content that is optional or would interrupt the flow — full command
output, a deeper explanation, a reference table. The section is collapsed by
default; the reader opens it if they want it.

The `title=` is the label shown while collapsed.

```
{{%/* expand title="Show the full output..." */%}}
Your hidden content here. Works with any Markdown inside.
{{%/* /expand */%}}
```

---

### Mermaid (Diagrams)

Renders diagrams from text. No image files, no external tools. Write the diagram
definition between the tags.

```
{{</* mermaid */>}}
flowchart TD
    A[Start] --> B[Do a thing]
    B --> C[Done]
{{</* /mermaid */>}}
```

Mermaid supports flowcharts, sequence diagrams, state machines, Gantt charts,
and more. The syntax differs per diagram type — check the
[Mermaid docs](https://mermaid.js.org/intro/) for what you need.

---

## The Club Mark — Files You Can Drop In

If you are making a slide, a flyer, a Discord banner, or a page that needs the
owl, take it from here rather than screenshotting it off the site. All six are
SVG, so they scale to any size cleanly.

Every form comes in two grounds. Pick the one that matches what you are
putting it on — the dark files wash out on paper, the light files disappear on
black.

### Shield

The full lockup. The only form that brings its own base, so it survives
anywhere. Use it when the mark stands alone: an avatar, a sticker, a slide
corner.

{{< mark-preview dark="/images/logo.svg" light="/images/shield-light.svg" width="170" alt="Club owl mark inside a shield" >}}

[dark ground](/images/logo.svg) · [light ground](/images/shield-light.svg)

### Owl head

No frame. Use it when it sits on a panel or beside text, where a second
border is just clutter.

{{< mark-preview dark="/images/owl-mark.svg" light="/images/owl-mark-light.svg" width="220" alt="Club owl head without the shield" >}}

[dark ground](/images/owl-mark.svg) · [light ground](/images/owl-mark-light.svg)

### Full owl

Head, folded wings, breast and talons — the one on the home page. Use it
where there is vertical room and the mark is the subject.

{{< mark-preview dark="/images/owl-full.svg" light="/images/owl-full-light.svg" width="180" alt="The full club owl with wings and talons" >}}

[dark ground](/images/owl-full.svg) · [light ground](/images/owl-full-light.svg)

The previews above swap with the theme — flip it in the topbar and watch.

**Before you use it anywhere official**, read the rules on
[Logo & Brand](/meta/brand/): the palette, the clear space, the minimum
sizes, and the FAU trademark warning. This owl is the *club's* mark, not the
university's.

---

## Front Matter Reference

| Parameter           | Type    | Default | What It Does                                |
| ------------------- | ------- | ------- | ------------------------------------------- |
| **title**           | string  | —       | Page title                                  |
| **weight**          | int     | —       | Sidebar order (lower = higher up)           |
| **type**            | string  | —       | `"home"` or `"chapter"` for special layouts |
| **hidden**          | boolean | false   | Hides the page from the sidebar             |
| **disableToc**      | boolean | false   | Hides the table of contents                 |
| **disableNextPrev** | boolean | false   | Hides the Next / Previous nav buttons       |

---

## Deeper Edits — Hugo Config and Theme

This section is for changes beyond content: menus, sidebar links, colors,
config.

### Key files

| File                          | What it controls                                    |
| ----------------------------- | --------------------------------------------------- |
| `hugo.toml`                   | Site title, theme variant, sidebar menus, nav links |
| `i18n/en.toml`                | UI string overrides (e.g. sidebar section title)    |
| `tokens/tokens.json`          | Color scheme — the palette's source (`scripts/gen-tokens.py` writes `assets/css/theme-*.css` from it) |

### Adding sidebar shortcut links

Shortcut links (Discord, GitHub, etc.) live in `hugo.toml` under
`[[menus.shortcuts]]`. Add a new entry:

```toml
[[menus.shortcuts]]
  name = "<i class='fab fa-github'></i> GitHub"
  url = "https://github.com/your-repo"
  weight = 10
```

The sidebar section title ("Quick Links") is set in `i18n/en.toml`.

### Color scheme

The wiki uses a custom **Hacker Terminal** palette — green on black. All colors
are defined as design tokens in `tokens/tokens.json`, which
`scripts/gen-tokens.py` turns into the CSS variables in `assets/css/theme-*.css`.

**Base palette**

| Hex       | Role                               |
| --------- | ---------------------------------- |
| `#001100` | Background (main + sidebar)        |
| `#002200` | Slightly lighter bg (code, boxes)  |
| `#005500` | Dark accent, borders, separators   |
| `#007700` | Muted text, visited links          |
| `#009900` | Secondary elements, H5/H6 headings |
| `#00BB00` | Main text, H3/H4 headings          |
| `#00FF00` | H1/H2 titles, highlights, hover    |
| `#00FF88` | Hyperlinks (cyan-green)            |
| `#00FFC8` | Hyperlink hover state              |

**Key CSS variables**

| Variable                    | Value     | What it controls      |
| --------------------------- | --------- | --------------------- |
| `--PRIMARY-color`           | `#00BB00` | Primary brand color   |
| `--PRIMARY-HOVER-color`     | `#00FF00` | Hover state           |
| `--MAIN-BG-color`           | `#001100` | Page background       |
| `--MAIN-TEXT-color`         | `#00BB00` | Body text             |
| `--MAIN-TITLES-TEXT-color`  | `#00FF00` | H1 / H2 headings      |
| `--MAIN-LINK-color`         | `#00FF88` | Hyperlinks            |
| `--CODE-BLOCK-BG-color`     | `#002200` | Code block background |
| `--CODE-BLOCK-BORDER-color` | `#005500` | Code block border     |
| `--CODE-INLINE-color`       | `#00FF00` | Inline code text      |
| `--MENU-SECTIONS-BG-color`  | `#001100` | Sidebar background    |
| `--MENU-VISITED-color`      | `#007700` | Visited sidebar links |

Edit `tokens/tokens.json` and run `python3 scripts/gen-tokens.py` to change any of
these; never edit the generated `assets/css/theme-*.css`. The theme variant is
wired up in `hugo.toml` via `themeVariant = 'hacker'`.

---

## Using AI to Write Pages

You do not have to write everything from scratch. An AI assistant can draft a
Markdown page well, as long as you give it enough context and review what comes
out.

### What to tell it

- The front matter format (TOML with `+++` delimiters)
- Which section the page belongs to
- What it should cover
- The tone: direct, practical, no filler

Example prompt:

```
Write a wiki page for a cybersecurity club. Front matter uses TOML with +++ delimiters.

+++
title = "Your Title"
weight = 2
+++

The page is about [topic]. Keep it direct and practical.
Cover: [list what you want].
```

### If your tool reads the repo

Coding agents that run in a terminal read the repo before they write. Point one
at the repo root and it picks up the rules on its own:

- `AGENTS.md` — one file, everything: build commands, site structure, the
  writing voice, FAU policy rules, and the Simplified Technical English
  rules. `CLAUDE.md` is a symlink to it, so either name loads the same thing.

Read both yourself before you write a page by hand. They apply to people too.

### What to watch for

AI will confidently write things that are wrong. Read it before committing. If
the page covers a specific tool or command, test that it actually works.

Cut any paragraph that says nothing. Phrases like "it's important to note" or
"feel free to explore" are filler — delete them.

---

## Questions?

Reach out on the [Discord](http://discord.gg/2Yun8WAUuy). No judgment — we were
all new to this once.
