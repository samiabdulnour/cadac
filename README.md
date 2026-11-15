# cadac

The office's Archicad standards, kept as data, with the template they describe
and the checks that hold the two together. It exists so that an AI agent --
Claude Code, working in this repository -- can make an Archicad project from a
brief and get the layers, the materials, the properties and the sheets right,
because it reads the same standards every time it starts.

## The idea

**The agent never invents a style.** Everything that makes a model look and
schedule correctly lives in the template, as a named favourite, a named layer,
a named property. The standards here are the list of those names. An agent
building a model writes a spec that only uses names from the list, and a
builder places each element from its favourite. What is not on the list is a
question for a person.

That gives three things, each checked against the next:

| | What it is | Where |
|---|---|---|
| **Standards** | The names the office builds with, and the rules about them | `standards/*.yaml` |
| **Template** | The Archicad file that actually holds them | `template/` (Git LFS) |
| **Project** | A brief, then a spec, then a model, then its reports | `projects/<name>/` |

## The workflow, and how much of it exists

| # | Stage | What happens | Built |
|---|---|---|---|
| 0 | **Template audit** | The template is opened in Archicad and asked what it holds; that is compared with the standards | yes -- not yet run against a live Archicad |
| 1 | **Brief** | What was asked for becomes `brief.yaml`; a person answers the open questions and approves it | yes |
| 2 | **Spec** | Every storey, wall, slab, opening and zone, each naming a favourite; checked before Archicad is opened | no -- the format is not designed |
| 3 | **Build** | A copy of the template is filled stage by stage, read back and saved after each | no |
| 4 | **Model check** | Every element on an allowed layer, classified, named and with its properties; areas and mix against the brief | no |
| 5 | **Sheets** | Views, layouts and the publisher set, from the template's masters | no |
| 6 | **Report** | What was built, what failed, what is left for a person | no |

Stages 2 to 6 are the plan, not the product. They are built one at a time, each
against a real template, and `docs/decisions.md` records why each is the way it
is.

## Layout

```
CLAUDE.md            the rules an agent follows in every session
.claude/skills/      one procedure per stage, loaded when the stage is worked on
standards/           the names and rules, one YAML file per kind
template/            the .tpl (Git LFS), and snapshot.json: what it holds, in text
projects/<name>/     brief.yaml, later spec and reports; the model itself is not kept
src/cadac/           the checks, and the reader that asks Archicad
tests/               the checks' own tests; no Archicad needed
docs/decisions.md    what was decided and why
docs/archicad.md     every Archicad command used, and where its shape was read from
```

## Setting up

Needs [uv](https://docs.astral.sh/uv/) and [Git LFS](https://git-lfs.com).

```bash
git lfs install
```

```bash
uv sync
```

```bash
uv run pytest
```

## The commands

```bash
uv run cadac validate
```

Reads the standards and every brief, and lists everything wrong with them. Files
only; runs anywhere.

```bash
uv run cadac snapshot
```

Asks the Archicad running on this machine what the open project holds, and
writes it to `template/snapshot.json`. Open the template first. Commit the file
with the template: it is the diff the `.tpl` cannot give.

```bash
uv run cadac audit
```

Asks the same and compares it with the standards. `--snapshot <file>` compares
a snapshot already taken, without Archicad; `--extra` also lists what the
template has that the standards do not mention; `--port 19724` is the second
Archicad open on the machine.

`snapshot` and `audit` need Archicad 26 or newer with the
[Loriini](https://github.com/samiabdulnour/loriini) add-on, which carries
Tapir's commands, or with Tapir itself. With Tapir alone the graphic override
combinations cannot be read and are reported as unchecked.

## Starting from an existing template

The standards ship as examples: the right shape, somebody else's names. To
make them this office's:

1. Open the template in Archicad and run `uv run cadac snapshot`.
2. Put the template in `template/` and commit it with the snapshot.
3. Replace the names in `standards/*.yaml` with the ones the office builds
   with -- chosen from the snapshot, not all of it: a template holds far more
   than a spec should be allowed to use. Set each file's `status` to `draft`.
4. Run `uv run cadac audit` until it passes, fixing the template or the
   standards, whichever is wrong.
5. When the office agrees a file, set its `status` to `agreed`. Nothing is
   built against a file that is not.
