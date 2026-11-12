+++
title = "Discord Sync"
weight = 2
description = "How posts move from Discord onto the board, for officers — no code, just the rules."
icon = "fa-solid fa-robot"
+++

The board on this wiki is not edited by hand. A bot reads the club Discord
and writes the pages for you. Know the rules below and you can run the whole
thing from Discord — you never need to touch the wiki itself.

## Announcements

Everything posted in **#announcements** is picked up automatically. No
reaction, no keyword, nothing to do. The newest ten posts that have text show
up on the home page.

## Jobs & internships

Post in **#jobs** however you like. Everything posted there shows up on the
Jobs & Internships board, newest first. No reaction, no keyword, nothing to
do.

Delete the Discord message and the post drops off the board on the next
sync. Discord system messages (pins, joins) and posts with no text are
ignored.

## Setting a deadline

A closing date is optional. If you want one, add one line anywhere in the
message, starting with the word `deadline` and a colon. The bot accepts a
plain date, a written-out date, or a range:

```
deadline: 2026-10-15
deadline: October 15, 2026
deadline: 03/30/2026 - 04/05/2026
```

The word must be `deadline` — not "closes," not "due." Numeric dates like
`10/15/2026` are read month first, American style. A range shows on the
board as a window ("Mar 30 – Apr 5") instead of a posted date.

Leave the line out entirely and the posting has no closing date. It stays
on the board until newer postings push it off, not for a fixed number of
days. Type a `deadline:` line the bot can't read and the posting behaves
the same way — no closing date — so get the date right if you want one.

The bot does not warn anyone about a deadline it can't read, so check the
post on the board after you send it.

## Pointing "Open ->" at the right link

Every link in your post is clickable on the board — you don't need to do
anything for that. But the card also has its own "Open ->" button, and the
bot has to guess which link that button should use. If your message has
more than one link — your LinkedIn, a company page, the actual job posting
— the guess can pick the wrong one.

Pin it yourself with an `apply:` line, anywhere in the message:

```
apply: https://example.com/careers/42
```

The word must be `apply`, and the value must be a link. Add this line and
the bot always uses it for "Open ->," no matter how many other links are in
the post.

## Fixing a mistake

Edit the Discord message, not the wiki. Every sync rebuilds the board from
the channel, so a wiki edit gets overwritten on the next run anyway. Fix the
typo or fix the date — in Discord.

## Limits and timing

- The board shows the newest 50 posts from #jobs. Older ones still exist in Discord,
  they just do not get a page.
- A sync runs every few minutes, so a post, a deletion, or an edit shows up
  on the wiki within about five minutes.

## The hand-edited list

Jobs and internships that never came through Discord — a flyer someone
emailed, a posting from before the bot existed — live in a hand-edited list
alongside the Discord ones. The Jobs & Internships page shows both lists
together, sorted newest first. If you need to add one of these by hand, ask
whoever maintains the wiki.
