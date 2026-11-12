#!/usr/bin/env python3
"""Publish the latest posts from the Discord #jobs channel to the Jobs & Internships board.

Reads DISCORD_BOT_TOKEN and DISCORD_JOBS_CHANNEL_ID from the environment —
never from the repo. Pulls the #jobs channel's recent messages and publishes
all of them, newest first, capped at WANT. No reaction or keyword is needed:
anything posted in #jobs shows up, and deleting the Discord message removes
it on the next run. Two kinds of message are skipped because they are not
postings: Discord system messages (joins, pins, thread notices — anything
whose type is not a plain or reply message) and messages whose text is empty
once cleaned (an image or embed with no words). Bot and webhook posts are
kept. Reuses clean() from fetch-announcements.py instead of reimplementing
its regexes.

Writes data/discord-postings.json, rebuilt in full from the channel on
every run: this is deliberate, since deleting or editing a message in
Discord must change the board on the next run. The hand-edited
data/postings.toml is a separate file this script never writes to; the two
are merged only at render time by the board-feed partial. There is a single
list: the output carries no job/internship split.

A posting has no expiry unless its author sets one: a `deadline:` line
anywhere in the message, followed by a date (or a date range) in one of a
handful of formats — see DATE_FORMATS_WITH_YEAR and DATE_FORMATS_NO_YEAR
below. No `deadline:` line means no `expires` key at all, and the item
rides the board until it ages out of the channel or the 50-item cap. A
`deadline:` line that is present but unparseable also omits `expires`,
but — unlike a missing line — it prints a warning to stdout, since that is
a poster's typo the sync should surface rather than silently swallow.

The card's "Open ->" link is picked in order: an `apply:` line's URL, if
the author set one; else the first link in the message that isn't a known
personal-profile URL (see PROFILE_LINK_RES); else the first link outright;
else the Discord permalink. See apply_url() and pick_link().

Meant to run from the same dedicated checkout as fetch-announcements.py: it
commits and pushes, and rebases onto main first so a concurrent push does
not wedge it.
"""
import importlib.util
import json, os, re, subprocess, sys, urllib.request
from datetime import datetime

API  = "https://discord.com/api/v10"
WANT = 50    # postings to publish
SCAN = 100   # Discord's per-request max; the whole channel fits one page
OUT  = "data/discord-postings.json"

LINK_RE = re.compile(r"https?://\S+")

# Author opt-in: an `apply:` line, anywhere in the raw message, whose value
# is itself an http(s) URL — same markdown tolerance as DEADLINE_LINE_RE
# below (`**apply:**`), matched before clean() strips it. If the text after
# the colon isn't a URL, this simply doesn't match and url selection falls
# through to the link-scanning rules in apply_url()'s caller.
APPLY_LINE_RE = re.compile(r"(?i)[*_]{0,2}apply[*_]{0,2}:[*_]{0,2}\s*(https?://\S+)")

# Trailing punctuation a URL picked out of prose shouldn't keep — the closing
# `.`/`,`/`)` of the sentence around it, not part of the link itself. Same
# set the board-feed.html linkify regex excludes from its final character;
# keep the two in sync. Balanced parentheses inside a URL (Wikipedia-style)
# are the same accepted edge case: a trailing `)` is always stripped.
TRAILING_URL_PUNCT = ".,;:!?)]\"'’”"

# Links that point at a person, not a job: not what "Open ->" should send a
# reader to. Small and explicit on purpose — grow this list as new patterns
# turn up instead of writing a general classifier.
PROFILE_LINK_RES = [
    re.compile(r"(?i)linkedin\.com/in/"),
]

# Author opt-in: a `deadline:` line, anywhere in the raw message, followed by
# a date or a date range. Tolerant of markdown emphasis around the keyword
# (`**deadline:**`) since this matches before clean() strips it. Captures the
# rest of the line — `.` does not span newlines without re.DOTALL, so this
# never reaches into the message body that follows.
DEADLINE_LINE_RE = re.compile(r"(?i)[*_]{0,2}deadline[*_]{0,2}:[*_]{0,2}\s*(.+)")

# A bare hyphen also separates the month/day/year of a numeric date
# (10-5-2026), so only a hyphen with space on both sides is treated as a
# range separator. En and em dashes never appear inside a single date, so
# they split a range even without surrounding space.
RANGE_SPLIT_RE = re.compile(r"(?i)\s+-\s+|–|—|\s+to\s+")

ORDINAL_RE = re.compile(r"(?i)\b(\d{1,2})(?:st|nd|rd|th)\b")

# Tried in order; the first one that matches the whole (trimmed) string wins.
# Numeric formats are US ordering (month first) — this is a Florida club.
DATE_FORMATS_WITH_YEAR = [
    "%Y-%m-%d",       # 2026-10-05
    "%m/%d/%Y",       # 10/05/2026
    "%m/%d/%y",       # 10/5/26
    "%m-%d-%Y",       # 10-5-2026
    "%B %d, %Y",      # October 5, 2026
    "%B %d %Y",       # October 5 2026
    "%b %d, %Y",      # Oct 5, 2026
    "%b %d %Y",       # Oct 5 2026
    "%d %B %Y",       # 5 October 2026
    "%d %b %Y",       # 5 Oct 2026
]

# Month-and-day with no year: resolves to the next occurrence on or after
# the message's own timestamp, never a past date.
DATE_FORMATS_NO_YEAR = [
    "%B %d",          # October 5
    "%b %d",          # Oct 5
]

def _load_sibling(name):
    """Import a hyphenated sibling script under scripts/ without copying it.

    Hyphens rule out a normal `import`, and fetch-announcements.py's
    network/git side effects sit behind `if __name__ == "__main__":`, so
    this only defines its functions.
    """
    path = os.path.join(os.path.dirname(__file__), name)
    spec = importlib.util.spec_from_file_location(name.replace("-", "_").removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

clean = _load_sibling("fetch-announcements.py").clean

def first_link(raw):
    """First http(s) link in the raw (uncleaned) message content, if any."""
    m = LINK_RE.search(raw)
    return m.group(0) if m else None

def _strip_trailing_url_punct(url):
    """Trim trailing sentence punctuation a regex match swept up with a URL."""
    return url.rstrip(TRAILING_URL_PUNCT)

def _is_profile_link(url):
    """True for a link that points at a person rather than a job posting."""
    return any(p.search(url) for p in PROFILE_LINK_RES)

def apply_url(raw):
    """The `apply:` line's URL, if the raw message has one — or None.

    The officer-facing opt-in: whoever posts can pin exactly which link the
    board's "Open ->" button should use, the same way `deadline:` pins the
    closing date.
    """
    m = APPLY_LINE_RE.search(raw)
    return _strip_trailing_url_punct(m.group(1)) if m else None

def pick_link(raw):
    """Best-guess http(s) link from the raw message body, or None.

    The first link whose host+path doesn't match a known personal-profile
    pattern (see PROFILE_LINK_RES) — falling back to the first link outright
    if every link found is a profile link. A message with no links at all
    returns None.
    """
    links = [_strip_trailing_url_punct(m.group(0)) for m in LINK_RE.finditer(raw)]
    for link in links:
        if not _is_profile_link(link):
            return link
    return links[0] if links else None

def _normalize_date_text(text):
    """Strip an ordinal suffix (`5th` -> `5`) and collapse whitespace."""
    return re.sub(r"\s+", " ", ORDINAL_RE.sub(r"\1", text.strip()))

def _try_formats(text, formats):
    """First successful `strptime` result among `formats`, or None."""
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None

def _resolve_year(dt, ref):
    """Attach the next occurrence of a year-less `dt` on or after `ref` — or None."""
    try:
        candidate = dt.replace(year=ref.year)
    except ValueError:
        return None   # e.g. Feb 29 outside a leap year
    if candidate.date() < ref.date():
        try:
            candidate = candidate.replace(year=ref.year + 1)
        except ValueError:
            return None
    return candidate.date()

def _parse_single_date(text, ref):
    """One date, in any accepted format, resolved against `ref` — or None.

    `ref` anchors a year-less month/day to its next occurrence: never a date
    before `ref` itself.
    """
    text = _normalize_date_text(text)
    dt = _try_formats(text, DATE_FORMATS_WITH_YEAR)
    if dt:
        return dt.date()
    dt = _try_formats(text, DATE_FORMATS_NO_YEAR)
    return _resolve_year(dt, ref) if dt else None

def _parse_range(start_text, end_text, ref):
    """A (start, end) date pair from the two sides of a range — or None.

    A year-less side borrows the other side's year rather than resolving
    independently: "March 30 to April 5, 2026" is one year, not two. Only
    when both sides omit the year do they fall back to `ref`, with the end
    resolved forward from the (now dated) start so the range can't invert.
    """
    start_text, end_text = _normalize_date_text(start_text), _normalize_date_text(end_text)
    start_dt = _try_formats(start_text, DATE_FORMATS_WITH_YEAR)
    end_dt = _try_formats(end_text, DATE_FORMATS_WITH_YEAR)
    if start_dt and end_dt:
        return start_dt.date(), end_dt.date()
    if start_dt and not end_dt:
        end_nd = _try_formats(end_text, DATE_FORMATS_NO_YEAR)
        end = _resolve_year(end_nd, start_dt) if end_nd else None
        return (start_dt.date(), end) if end else None
    if end_dt and not start_dt:
        start_nd = _try_formats(start_text, DATE_FORMATS_NO_YEAR)
        if not start_nd:
            return None
        try:
            start = start_nd.replace(year=end_dt.year).date()
        except ValueError:
            return None
        return start, end_dt.date()
    start_nd = _try_formats(start_text, DATE_FORMATS_NO_YEAR)
    start = _resolve_year(start_nd, ref) if start_nd else None
    if not start:
        return None
    end_nd = _try_formats(end_text, DATE_FORMATS_NO_YEAR)
    end = _resolve_year(end_nd, datetime.combine(start, datetime.min.time())) if end_nd else None
    return (start, end) if end else None

def deadline_fields(raw, ref):
    """Fields from a message's `deadline:` line, and the bad text if it failed to parse.

    Returns (fields, bad_text):
      - no `deadline:` line at all:            ({}, None) — nothing to warn about
      - line present, one date parses:         ({"expires": "YYYY-MM-DD"}, None)
      - line present, a range parses:          ({"starts": ..., "expires": ...}, None)
      - line present, nothing usable parses:   ({}, "<the text after the keyword>")

    `ref` is the message's own timestamp (a datetime), used to resolve a
    year-less date. Never raises: a human typed this in a chat client.
    """
    m = DEADLINE_LINE_RE.search(raw)
    if not m:
        return {}, None
    text = m.group(1).strip().rstrip("*_.,; \t")
    parts = RANGE_SPLIT_RE.split(text, maxsplit=1)
    if len(parts) == 2:
        result = _parse_range(parts[0], parts[1], ref)
        if result:
            starts, expires = result
            return {"starts": starts.isoformat(), "expires": expires.isoformat()}, None
    else:
        expires = _parse_single_date(text, ref)
        if expires:
            return {"expires": expires.isoformat()}, None
    return {}, text

def build_item(message, guild, channel):
    """Build one data/discord-postings.json entry from a fetched message, or None to skip it.

    Skips Discord system messages and messages with no text once cleaned.
    An unparseable `deadline:` line prints a warning to stdout; the item is
    still built, just without `expires`.
    """
    if message.get("type") not in (0, 19):          # skip system messages
        return None
    raw = message.get("content", "")
    text = clean(raw)
    if not text:
        return None
    url = (apply_url(raw) or pick_link(raw)
           or f"https://discord.com/channels/{guild}/{channel}/{message['id']}")
    fields, bad = deadline_fields(raw, datetime.fromisoformat(message["timestamp"]))
    if bad is not None:
        print(f"deadline unparseable in message {message.get('id')}: {bad!r}")
    return {
        "date": message["timestamp"],
        "text": text,
        "url":  url,
        **fields,
    }

def build_items(jobs_channel, api):
    """Fetch #jobs and build the postings list: newest first, at most WANT.

    `api` is injected so tests can stub Discord out entirely.
    """
    guild = api(f"/channels/{jobs_channel}")["guild_id"]
    messages = api(f"/channels/{jobs_channel}/messages?limit={SCAN}")
    items = [i for i in (build_item(m, guild, jobs_channel) for m in messages) if i]
    items.sort(key=lambda i: i["date"], reverse=True)
    del items[WANT:]
    return items

def main():
    token   = os.environ.get("DISCORD_BOT_TOKEN")
    channel = os.environ.get("DISCORD_JOBS_CHANNEL_ID")
    if not (token and channel):
        sys.exit("DISCORD_BOT_TOKEN and DISCORD_JOBS_CHANNEL_ID must be set")

    def api(path):
        req = urllib.request.Request(API + path, headers={
            "Authorization": f"Bot {token}",
            # Discord's edge 403s the default Python-urllib UA; their API wants a
            # descriptive one.
            "User-Agent": "fau-csc-postings (+https://fau-cyber-wiki-test.necoconeco.net, 1.0)",
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)

    items = build_items(channel, api)

    new = json.dumps(items, indent=2, ensure_ascii=False) + "\n"
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if new == old:
        print("unchanged")
        sys.exit(0)

    if "--dry-run" in sys.argv:            # preview the JSON, touch nothing
        print(new)
        sys.exit(0)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(new)

    ident = ["-c", "user.name=csc-announcements-bot",
             "-c", "user.email=csc-announcements-bot@users.noreply.github.com"]
    push  = ["-c", "credential.helper=!gh auth git-credential"]
    subprocess.run(["git", "add", OUT], check=True)
    subprocess.run(["git", *ident, "commit", "-q", "-m", "postings: sync from Discord"], check=True)
    subprocess.run(["git", "pull", "--rebase", "--quiet", "origin", "main"], check=True)
    subprocess.run(["git", *push, "push", "-q", "origin", "HEAD:main"], check=True)
    print(f"published {len(items)} posting(s)")

if __name__ == "__main__":
    main()
