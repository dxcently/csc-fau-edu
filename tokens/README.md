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
- **`only`.** `$extensions.csc.only` limits a token to listed variants (today
  just `--wf-fill-solid`, cyber-only). Every other token must resolve in every
  variant; the generator refuses to run otherwise.
- **Aliases.** `"{wf.palette.chrome}"` becomes `var( --wf-chrome )`.
- **Names.** Two top-level groups. `wf` (cssPrefix `wf-`) is the palette;
  `relearn` (no prefix) maps Relearn's own `--*-color` variables onto it. The
  CSS name is `--` + prefix + the token's key; the groups between are only for
  organising and their names never reach the CSS. Keys are unique per top group.
- **Descriptions** become the CSS comments: a short one trails the value, a
  long one goes above it, a group's goes above the group.

## Output

- `assets/css/theme-<variant>.css`: one file per variant, all groups. The
  header comment is the variant's root description.
- `dist/tokens.css`: every variant's `wf` group in one file, as
  `:root[data-theme-variant='<id>']` blocks (`hacker` also matches a bare
  `:root`, so an unattributed page gets the default). The Relearn map is left
  out. This is the file other repos import; it is committed so they can take it
  from a raw URL or a submodule.

The generator normalises layout (column alignment, comment wrapping, the
spacing inside `rgba( ... )`). Values are unchanged.
