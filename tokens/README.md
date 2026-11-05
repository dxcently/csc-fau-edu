# tokens/

`tokens.json` is the master for the site's palette. `assets/css/theme-*.css`
and `dist/tokens.css` are generated from it. Edit the JSON, then:

```bash
python3 scripts/gen-tokens.py           # rewrite the generated files
python3 scripts/gen-tokens.py --check   # exit 1 if they are out of date (CI runs this)
```

Never edit `theme-*.css` or `dist/tokens.css` by hand: the next run, or CI,
undoes it.

## Format

[W3C Design Tokens](https://www.w3.org/community/design-tokens/) (DTCG): groups
nest, a token is an object with `$value`, and `$type` / `$description` are
used where they apply. Colors and dimensions are CSS strings (`#00FF41`,
`rgba( 30, 144, 255, .30 )`, `2px`); font stacks are arrays of family names.
Tokens with no `$type` are raw CSS keywords (`normal`, `dark`, a chroma theme
name).

```json
"chrome": {
  "$type": "color",
  "$value": "#1E90FF",
  "$description": "structure blue",
  "$extensions": {"csc": {"variants": {
    "hacker-light": {"$value": "#0B5FC4", "$description": "structure blue 5.7:1"},
    "cyber":        {"$value": "#00C853", "$description": "structure green, MID value 8.1:1"}
  }}}
}
```

- **Variants.** `$extensions.csc.variants` on the root lists the variants. The
  first (`hacker`) is the base: a token's own `$value` and `$description` are
  the base's. A token's `variants` block overrides them per variant; a field
  it leaves out is the base's. Root, group and token descriptions all work
  this way, so each variant keeps its own header and comments.
- **The colour rule.** For a token whose base `$value` is a literal colour
  (`#hex`, `rgb()`, `rgba()`, `hsl()`), every other variant it applies to must
  either have its own `variants.<id>.$value` or be listed in
  `$extensions.csc.inherit` (`"inherit": ["cyber"]`), which says "this variant
  deliberately uses hacker's colour". Neither is an error naming the token and
  variant, so a forgotten colour cannot silently keep hacker's. It is also an
  error to override with the base's own value (use `inherit`), to list a variant
  in `inherit` that also overrides, or to use `inherit` on anything but a
  literal colour. Aliases (`{...}`) and non-colour tokens (fonts, sizes,
  keywords) are not subject to the rule: with no override they take the base's
  value.
- **`only`.** `$extensions.csc.only` limits a token to listed variants (today
  just `--wf-fill-solid`, cyber-only); the colour rule then applies to those
  variants only. Any other token exists in every variant.
- **Aliases.** `"{wf.palette.chrome}"` becomes `var( --wf-chrome )`.
- **Names.** Two top-level groups. `wf` (cssPrefix `wf-`) is the palette;
  `relearn` (no prefix) maps Relearn's own `--*-color` variables onto it. The
  CSS name is `--` + prefix + the token's key; the groups between are only for
  organising and their names never reach the CSS. Keys are unique per top group.
- **Comments.** `$description` is the short note that trails the value (a long
  one moves above it). `$extensions.csc.comment` is the block comment above
  the token (a list is several blocks); it overrides per variant too. In a
  comment, `\n` starts a new line, an empty line is a blank line and a line
  starting `* ` is a bullet. A group's `$description` is its banner comment.

## Output

- `assets/css/theme-<variant>.css`: one file per variant, all groups. The
  header comment is the variant's root description.
- `dist/tokens.css`: every variant's `wf` group in one file, as
  `:root[data-r-theme-variant='<id>']` blocks, the same attribute the site's
  switcher sets on `<html>`, so any page sharing that switcher matches. The
  `hacker` block also answers a bare `:root`, so an unattributed page gets the
  default. The Relearn map is left
  out. This is the file other repos import; it is committed so they can take it
  from a raw URL or a submodule.

The generator normalises layout (column alignment, comment wrapping, the
spacing inside `rgba( ... )`). Values are unchanged.
