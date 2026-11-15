# Template

The office's Archicad template goes here, with a snapshot of what it holds.

| File | What |
|---|---|
| `<name>.tpl` | the template, stored through Git LFS |
| `snapshot.json` | what the template holds, by name, written by `uv run cadac snapshot` |

Neither is here yet.

## Why the snapshot is kept

Git cannot show what changed inside a `.tpl`. The snapshot is the same
information in text -- every layer, favourite, building material and property
by name -- so the difference between two versions of the template is an
ordinary diff of `snapshot.json`. Take a new one whenever the template changes
and commit the two together.

## Adding or changing the template

Once on each machine:

```bash
git lfs install
```

Then save the template into this folder, open it in Archicad, and:

```bash
uv run cadac audit
```

```bash
uv run cadac snapshot
```

Commit the template, the snapshot and any change to `standards/` in one
commit. `.gitattributes` already sends `.tpl`, `.pln`, `.pla`, `.mod`, `.lcf`,
`.gsm`, `.aat` and `.prf` files through LFS; check with `git lfs ls-files`
after staging that the template is listed.

## One template

Keep one template here, the one models are built from. A model is made by
copying it into `projects/<name>/model/`, never by working in this file.
