import io
import unittest
from contextlib import redirect_stdout
from datetime import datetime

from loadscript import load

fetch_postings  = load("fetch-postings.py")
first_link      = fetch_postings.first_link
apply_url       = fetch_postings.apply_url
pick_link       = fetch_postings.pick_link
deadline_fields = fetch_postings.deadline_fields
build_item      = fetch_postings.build_item
build_items     = fetch_postings.build_items
WANT            = fetch_postings.WANT

GUILD   = "555000111222333444"
CHANNEL = "666000111222333444"

REF = datetime.fromisoformat("2026-08-01T15:04:23.512000+00:00")


def message(content, message_id="1111122222333334444", timestamp="2026-08-01T15:04:23.512000+00:00", msg_type=0):
    """A message payload shaped like Discord's actual GET messages response."""
    return {
        "id": message_id,
        "type": msg_type,
        "content": content,
        "channel_id": CHANNEL,
        "author": {
            "id": "999000111222333444",
            "username": "recruiter_bot",
            "global_name": "Recruiter",
            "discriminator": "0",
            "avatar": None,
            "bot": True,
        },
        "timestamp": timestamp,
        "edited_timestamp": None,
        "tts": False,
        "mention_everyone": False,
        "mentions": [],
        "mention_roles": [],
        "attachments": [],
        "embeds": [],
        "pinned": False,
        "flags": 0,
        "components": [],
    }


class TestFirstLink(unittest.TestCase):
    def test_finds_first_http_or_https_link_in_raw_content(self):
        raw = "Apply here: https://example.com/careers/42 or http://example.org/backup"
        self.assertEqual(first_link(raw), "https://example.com/careers/42")

    def test_no_link_returns_none(self):
        self.assertIsNone(first_link("No link in this one, just apply in Discord."))


class TestApplyUrl(unittest.TestCase):
    def test_apply_line_url_is_used(self):
        raw = "Great internship.\napply: https://example.com/careers/42\nDM with questions."
        self.assertEqual(apply_url(raw), "https://example.com/careers/42")

    def test_case_insensitive_keyword(self):
        raw = "APPLY: https://example.com/careers/42"
        self.assertEqual(apply_url(raw), "https://example.com/careers/42")

    def test_bold_markdown_keyword_still_matches(self):
        raw = "**apply:** https://example.com/careers/42"
        self.assertEqual(apply_url(raw), "https://example.com/careers/42")

    def test_trailing_punctuation_stripped(self):
        raw = "apply: https://example.com/careers/42."
        self.assertEqual(apply_url(raw), "https://example.com/careers/42")

    def test_non_url_value_does_not_match(self):
        self.assertIsNone(apply_url("apply: in person at the career fair"))

    def test_no_apply_line_returns_none(self):
        self.assertIsNone(apply_url("Apply here: https://example.com/careers/42"))

    def test_apply_line_wins_even_when_it_is_not_the_first_link(self):
        raw = (
            "Connect with the recruiter: https://www.linkedin.com/in/example/\n"
            "apply: https://example.com/careers/42"
        )
        self.assertEqual(apply_url(raw), "https://example.com/careers/42")


class TestPickLink(unittest.TestCase):
    def test_single_link_is_used(self):
        self.assertEqual(pick_link("Apply at https://example.com/careers/42 today."), "https://example.com/careers/42")

    def test_no_links_returns_none(self):
        self.assertIsNone(pick_link("DM me for details, no link posted."))

    def test_profile_link_skipped_in_favor_of_a_later_job_link(self):
        raw = (
            "Connect with them directly:\n"
            "https://www.linkedin.com/in/wadethomas/\n"
            "https://www.linkedin.com/in/averyjonathan/\n\n"
            "https://www.linkedin.com/jobs/view/4461193427/"
        )
        self.assertEqual(pick_link(raw), "https://www.linkedin.com/jobs/view/4461193427/")

    def test_only_profile_links_falls_back_to_the_first_one(self):
        raw = (
            "https://www.linkedin.com/in/wadethomas/\n"
            "https://www.linkedin.com/in/averyjonathan/"
        )
        self.assertEqual(pick_link(raw), "https://www.linkedin.com/in/wadethomas/")

    def test_trailing_punctuation_stripped(self):
        raw = "See https://www.linkedin.com/in/wadethomas/, then https://example.com/job."
        self.assertEqual(pick_link(raw), "https://example.com/job")


class TestDeadlineFieldsNoLine(unittest.TestCase):
    def test_no_deadline_line_yields_no_fields(self):
        fields, bad = deadline_fields("Apply whenever, no rush.", REF)
        self.assertEqual(fields, {})
        self.assertIsNone(bad)

    def test_synonym_keyword_not_accepted(self):
        fields, bad = deadline_fields("closes: 2026-09-05", REF)
        self.assertEqual(fields, {})
        self.assertIsNone(bad)


class TestDeadlineFieldsSingleDate(unittest.TestCase):
    def test_iso_date(self):
        fields, bad = deadline_fields("deadline: 2026-10-05", REF)
        self.assertEqual(fields, {"expires": "2026-10-05"})
        self.assertIsNone(bad)

    def test_us_slash_date_with_four_digit_year(self):
        fields, _ = deadline_fields("deadline: 10/05/2026", REF)
        self.assertEqual(fields, {"expires": "2026-10-05"})

    def test_us_slash_date_with_two_digit_year(self):
        fields, _ = deadline_fields("deadline: 10/5/26", REF)
        self.assertEqual(fields, {"expires": "2026-10-05"})

    def test_us_dash_date(self):
        fields, _ = deadline_fields("deadline: 10-5-2026", REF)
        self.assertEqual(fields, {"expires": "2026-10-05"})

    def test_written_out_date_with_comma(self):
        fields, _ = deadline_fields("deadline: October 5, 2026", REF)
        self.assertEqual(fields, {"expires": "2026-10-05"})

    def test_abbreviated_month_no_comma(self):
        fields, _ = deadline_fields("deadline: Oct 5 2026", REF)
        self.assertEqual(fields, {"expires": "2026-10-05"})

    def test_ordinal_suffix(self):
        fields, bad = deadline_fields("deadline: Oct 5th", REF)
        self.assertEqual(fields, {"expires": "2026-10-05"})
        self.assertIsNone(bad)

    def test_day_first_written_date(self):
        fields, _ = deadline_fields("deadline: 5 October 2026", REF)
        self.assertEqual(fields, {"expires": "2026-10-05"})

    def test_bold_markdown_keyword_still_matches(self):
        fields, _ = deadline_fields("**deadline:** 2026-10-05", REF)
        self.assertEqual(fields, {"expires": "2026-10-05"})

    def test_case_insensitive_keyword(self):
        fields, _ = deadline_fields("DEADLINE: 2026-09-05", REF)
        self.assertEqual(fields, {"expires": "2026-09-05"})

    def test_deadline_line_anywhere_in_body(self):
        raw = "Hey everyone, cool internship!\n\ndeadline: 2026-09-05\n\nApply on our site."
        fields, _ = deadline_fields(raw, REF)
        self.assertEqual(fields, {"expires": "2026-09-05"})

    def test_no_starts_key_for_a_single_date(self):
        fields, _ = deadline_fields("deadline: 2026-10-05", REF)
        self.assertNotIn("starts", fields)


class TestDeadlineFieldsYearlessDate(unittest.TestCase):
    def test_month_day_after_ref_resolves_to_current_year(self):
        # REF is 2026-08-01; Nov 1 hasn't happened yet this year.
        fields, _ = deadline_fields("deadline: Nov 1", REF)
        self.assertEqual(fields, {"expires": "2026-11-01"})

    def test_month_day_before_ref_resolves_to_next_year(self):
        # REF is 2026-08-01; Jan 1 already passed this year.
        fields, _ = deadline_fields("deadline: Jan 1", REF)
        self.assertEqual(fields, {"expires": "2027-01-01"})


class TestDeadlineFieldsRange(unittest.TestCase):
    def test_hyphen_separator(self):
        fields, bad = deadline_fields("deadline: 03/30/2026 - 04/05/2026", REF)
        self.assertEqual(fields, {"starts": "2026-03-30", "expires": "2026-04-05"})
        self.assertIsNone(bad)

    def test_to_separator_with_written_dates(self):
        fields, bad = deadline_fields("deadline: March 30 to April 5, 2026", REF)
        self.assertEqual(fields, {"starts": "2026-03-30", "expires": "2026-04-05"})
        self.assertIsNone(bad)

    def test_en_dash_separator(self):
        fields, _ = deadline_fields("deadline: March 30 – April 5, 2026", REF)
        self.assertEqual(fields, {"starts": "2026-03-30", "expires": "2026-04-05"})

    def test_em_dash_separator(self):
        fields, _ = deadline_fields("deadline: March 30 — April 5, 2026", REF)
        self.assertEqual(fields, {"starts": "2026-03-30", "expires": "2026-04-05"})

    def test_year_on_end_only_applies_to_both_sides(self):
        # Without this, a naive year-less resolve would push "March 30" (a
        # date already past REF this year) into 2027 while "April 5, 2026"
        # stayed put, splitting the range across two different years.
        fields, _ = deadline_fields("deadline: March 30 to April 5, 2026", REF)
        self.assertEqual(fields["starts"][:4], fields["expires"][:4])

    def test_numeric_dash_dates_do_not_get_split_mid_date(self):
        fields, bad = deadline_fields("deadline: 10-5-2026", REF)
        self.assertNotIn("starts", fields)
        self.assertEqual(fields, {"expires": "2026-10-05"})
        self.assertIsNone(bad)


class TestDeadlineFieldsMalformed(unittest.TestCase):
    def test_unrecognized_text_yields_no_expires(self):
        fields, bad = deadline_fields("deadline: whenever works", REF)
        self.assertEqual(fields, {})
        self.assertIsNotNone(bad)

    def test_impossible_calendar_date_yields_no_expires(self):
        fields, bad = deadline_fields("deadline: 2026-13-45", REF)
        self.assertEqual(fields, {})
        self.assertIsNotNone(bad)

    def test_non_iso_numeric_with_wrong_field_count_is_malformed(self):
        fields, bad = deadline_fields("deadline: 2026/40/99", REF)
        self.assertEqual(fields, {})
        self.assertIsNotNone(bad)


class TestBuildItemDeadlineWarnings(unittest.TestCase):
    def _run(self, content, timestamp="2026-08-01T15:04:23.512000+00:00"):
        m = message(content, timestamp=timestamp)
        out = io.StringIO()
        with redirect_stdout(out):
            item = build_item(m, GUILD, CHANNEL)
        return item, out.getvalue()

    def test_no_deadline_line_does_not_warn(self):
        item, out = self._run("Hiring now, apply on our site.")
        self.assertNotIn("expires", item)
        self.assertEqual(out, "")

    def test_malformed_deadline_warns_and_omits_expires(self):
        item, out = self._run("Hiring now.\ndeadline: sometime soon")
        self.assertNotIn("expires", item)
        self.assertIn("1111122222333334444", out)
        self.assertIn("sometime soon", out)

    def test_valid_deadline_does_not_warn(self):
        item, out = self._run("Hiring now.\ndeadline: 2026-10-05")
        self.assertEqual(item["expires"], "2026-10-05")
        self.assertEqual(out, "")


class TestBuildItem(unittest.TestCase):
    def test_job_item_uses_raw_link_and_cleaned_text(self):
        m = message(
            "💼 **Hiring**: SOC analyst intern, apply at https://example.com/apply now @everyone",
                        timestamp="2026-08-01T15:04:23.512000+00:00",
        )
        item = build_item(m, GUILD, CHANNEL)
        self.assertNotIn("kind", item)
        self.assertEqual(item["url"], "https://example.com/apply")
        self.assertEqual(item["date"], "2026-08-01T15:04:23.512000+00:00")
        self.assertNotIn("expires", item)
        self.assertNotIn("**", item["text"])
        self.assertNotIn("@everyone", item["text"])
        self.assertIn("💼", item["text"])

    def test_no_link_falls_back_to_permalink(self):
        m = message("🎓 Internship posting, DM me for details",
                     message_id="777788889999000011")
        item = build_item(m, GUILD, CHANNEL)
        self.assertEqual(item["url"], f"https://discord.com/channels/{GUILD}/{CHANNEL}/777788889999000011")

    def test_message_without_any_reaction_is_published(self):
        m = message("Hiring a SOC analyst.")
        self.assertEqual(build_item(m, GUILD, CHANNEL)["text"], "Hiring a SOC analyst.")

    def test_system_message_is_not_built(self):
        m = message("Someone pinned a message", msg_type=6)
        self.assertIsNone(build_item(m, GUILD, CHANNEL))

    def test_reply_message_is_built(self):
        m = message("Reply with more details.", msg_type=19)
        self.assertIsNotNone(build_item(m, GUILD, CHANNEL))

    def test_empty_text_is_not_built(self):
        m = message("   ")
        self.assertIsNone(build_item(m, GUILD, CHANNEL))

    def test_unicode_emoji_in_body_survive_cleaning(self):
        m = message("🚨 Job posting 📢 apply now 🎓")
        item = build_item(m, GUILD, CHANNEL)
        self.assertIn("🚨", item["text"])
        self.assertIn("📢", item["text"])
        self.assertIn("🎓", item["text"])

    def test_range_deadline_sets_starts_and_expires(self):
        m = message(
            "Career fair booth sign-ups.\ndeadline: 03/30/2026 - 04/05/2026",
                    )
        item = build_item(m, GUILD, CHANNEL)
        self.assertEqual(item["starts"], "2026-03-30")
        self.assertEqual(item["expires"], "2026-04-05")

    def test_apply_line_wins_over_any_body_link(self):
        # Shaped like the channel's actual posts: a "connect with them" block
        # of profile links, then the real job link further down, plus an
        # explicit apply: line pinning a completely different URL.
        raw = (
            "Internship at NCCI — Boca Raton, FL\n\n"
            "Connect with them directly:\n"
            "https://www.linkedin.com/in/wadethomas/\n"
            "https://www.linkedin.com/in/averyjonathan/\n\n"
            "apply: https://example.com/careers/nnci-intern\n\n"
            "https://www.linkedin.com/jobs/view/4461193427/"
        )
        m = message(raw)
        item = build_item(m, GUILD, CHANNEL)
        self.assertEqual(item["url"], "https://example.com/careers/nnci-intern")

    def test_profile_link_skipped_in_favor_of_later_job_link(self):
        # The live posting this defect came from: five LinkedIn links, four
        # of them personal profiles, and the job link is the last one.
        raw = (
            "📢 NCCI IT Infrastructure Internship — Boca Raton, FL\n\n"
            "👤 Connect with them directly:\n"
            "- [Wade Thomas — IT Infosec & Infrastructure Manager]\n"
            "https://www.linkedin.com/in/wadethomas/\n\n"
            "https://www.linkedin.com/in/averyjonathan/\n"
            "https://www.linkedin.com/in/marcos-caceres-41ab49b2/\n"
            "https://www.linkedin.com/in/nicolasbrugger/\n\n"
            "Apply ASAP — DM me with questions.\n\n"
            "https://www.linkedin.com/jobs/view/4461193427/"
        )
        m = message(raw)
        item = build_item(m, GUILD, CHANNEL)
        self.assertEqual(item["url"], "https://www.linkedin.com/jobs/view/4461193427/")


class FakeApi:
    """Stands in for fetch-postings.py's `api()` closure, no network involved."""

    def __init__(self, jobs_messages=()):
        self.jobs_messages = list(jobs_messages)
        self.calls = []

    def __call__(self, path):
        self.calls.append(path)
        if path == f"/channels/{CHANNEL}":
            return {"guild_id": GUILD}
        if path.startswith(f"/channels/{CHANNEL}/messages?"):
            return self.jobs_messages
        raise AssertionError(f"unexpected path {path!r}")


class TestBuildItems(unittest.TestCase):
    def test_every_message_is_published_newest_first(self):
        old = message("Older.", message_id="1", timestamp="2026-07-01T00:00:00+00:00")
        new = message("Newer.", message_id="2", timestamp="2026-08-01T00:00:00+00:00")
        items = build_items(CHANNEL, FakeApi([old, new]))
        self.assertEqual([i["text"] for i in items], ["Newer.", "Older."])

    def test_only_channel_endpoints_are_called(self):
        api = FakeApi([message("Hiring.")])
        build_items(CHANNEL, api)
        self.assertEqual(len(api.calls), 2)

    def test_capped_at_want(self):
        msgs = [message(f"Post {n}", message_id=str(n),
                        timestamp=f"2026-01-01T00:{n // 60:02d}:{n % 60:02d}+00:00")
                for n in range(WANT + 10)]
        items = build_items(CHANNEL, FakeApi(msgs))
        self.assertEqual(len(items), WANT)
        self.assertEqual(items[0]["text"], f"Post {WANT + 9}")

    def test_system_and_empty_messages_are_dropped(self):
        msgs = [message("Real posting.", message_id="1"),
                message("joined", message_id="2", msg_type=7),
                message("", message_id="3")]
        self.assertEqual(len(build_items(CHANNEL, FakeApi(msgs))), 1)


if __name__ == "__main__":
    unittest.main()
