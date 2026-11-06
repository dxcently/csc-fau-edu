import copy
import json
import tempfile
import unittest
from pathlib import Path

from loadscript import load

gen = load("gen-tokens.py")


def fixture(**token):
    """A two-variant token file: `base` (default) and `dark`, one colour token
    `ink`, one alias `link` -> ink. `token` is merged into the ink token."""
    ink = {"$type": "color", "$value": "#111111", "$description": "text"}
    ink.update(token)
    return {
        "$description": "fixture header",
        "$extensions": {"csc": {"variants": {"base": {}, "dark": {"$description": "dark header"}}}},
        "wf": {
            "$extensions": {"csc": {"cssPrefix": "wf-"}},
            "palette": {"$description": "palette", "ink": ink, "link": {"$value": "{wf.palette.ink}"}},
        },
    }


def build(data):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "tokens.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return gen.build(path)


def csc(**fields):
    return {"$extensions": {"csc": fields}}


class TestColourRule(unittest.TestCase):
    def test_colour_with_no_value_for_a_variant_fails_naming_both(self):
        with self.assertRaises(gen.TokenError) as cm:
            build(fixture())
        self.assertIn("wf.palette.ink", str(cm.exception))
        self.assertIn("'dark'", str(cm.exception))

    def test_own_value_passes(self):
        build(fixture(**csc(variants={"dark": {"$value": "#EEEEEE"}})))

    def test_inherit_marker_passes_and_emits_the_base_colour(self):
        files = build(fixture(**csc(inherit=["dark"])))
        dark = next(t for p, t in files.items() if p.name == "theme-dark.css")
        self.assertIn("--wf-ink:  #111111;", dark)

    def test_alias_needs_no_marker(self):
        # `link` is an alias of ink; only ink is decided per variant
        build(fixture(**csc(inherit=["dark"])))

    def test_override_equal_to_base_fails(self):
        with self.assertRaises(gen.TokenError) as cm:
            build(fixture(**csc(variants={"dark": {"$value": "#111111"}})))
        self.assertIn("inherit", str(cm.exception))

    def test_inherit_and_override_together_fail(self):
        with self.assertRaises(gen.TokenError) as cm:
            build(fixture(**csc(inherit=["dark"], variants={"dark": {"$value": "#EEEEEE"}})))
        self.assertIn("also overrides", str(cm.exception))

    def test_inherit_on_unknown_or_base_variant_fails(self):
        for bad in (["nope"], ["base"]):
            with self.assertRaises(gen.TokenError):
                build(fixture(**csc(inherit=bad)))

    def test_rgba_is_a_colour_too(self):
        with self.assertRaises(gen.TokenError):
            build(fixture(**{"$value": "rgba( 1, 2, 3, .5 )"}))

    def test_only_excludes_the_other_variant(self):
        # a base-only colour needs no decision for the variant it excludes
        data = fixture(**csc(only=["base"]))
        del data["wf"]["palette"]["link"]      # the alias would point at a missing token
        build(data)

    def test_non_colour_falls_back_without_marker(self):
        data = fixture(**csc(inherit=["dark"]))
        data["wf"]["palette"]["gap"] = {"$type": "dimension", "$value": "1rem"}
        build(data)


class TestRepoTokens(unittest.TestCase):
    def test_committed_tokens_build(self):
        build_files = gen.build()
        self.assertEqual(len(build_files), 5)


class TestAuthentikCss(unittest.TestCase):
    css = gen.build()[gen.AUTHENTIK]

    def dark(self):
        return self.css.split("\nhtml[data-theme='light'] {")[0]

    def test_dark_is_the_default_and_light_is_scoped(self):
        self.assertIn(":root,\nhtml[data-theme='dark'] {", self.css)
        self.assertIn("html[data-theme='light'] {", self.css)
        dark = self.dark()
        self.assertIn("--ak-color-surface-muted:  #030A08;", dark)

    def test_colours_come_from_the_tokens_not_literals(self):
        data, variants, _t, tokens, byalias = gen.load()
        for path, var in (("wf.palette.chrome", "--ak-color-primary"),
                          ("wf.palette.bg", "--ak-color-surface-muted")):
            want = gen.resolve(tokens, byalias, variants, "hacker", path)
            self.assertRegex(self.css, rf"{var}:\s+{want};")

    def test_red_is_only_the_danger_text_colour(self):
        data, variants, _t, tokens, byalias = gen.load()
        for variant in ("hacker", "hacker-light"):
            text = gen.resolve(tokens, byalias, variants, variant, "wf.palette.red-text")
            red = gen.resolve(tokens, byalias, variants, variant, "wf.palette.red")
            self.assertIn(f"--ak-color-danger:         {text};", self.css)
        # in the dark default the fill red must not appear at all
        self.assertNotIn(gen.resolve(tokens, byalias, variants, "hacker", "wf.palette.red"),
                         self.dark())

    def test_no_club_marks_or_fau_naming_beyond_the_banner(self):
        body = self.css.split("*/", 1)[1]
        self.assertNotIn("url(", body)
        self.assertNotRegex(body, r"(?i)\bfau\b")


if __name__ == "__main__":
    unittest.main()
