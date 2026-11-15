# Decisions

What was decided and why, newest last. Read before changing how something
works; add an entry when a decision is made or reversed.

## D1 — The standards are the manifest

There is one list of what the template must contain, and it is
`standards/*.yaml`. A separate manifest of the template was considered and
dropped: the same layers and favourites would be listed twice, and two lists
drift. The audit compares the template with the standards directly.

## D2 — The template is in this repository, through Git LFS

A `.tpl` is binary: git cannot diff it and keeps a whole copy for every
change. LFS keeps those copies out of the history. Keeping the template beside
the standards means one commit holds the template, its snapshot and the
standards that describe it, so they cannot describe three different templates.
The alternative, a shared folder outside git, was dropped for that reason.

## D3 — A snapshot of the template is committed with it

`template/snapshot.json` is what the template holds, by name, in sorted text.
It is the diff the binary cannot give, and it lets the audit run where there
is no Archicad (`cadac audit --snapshot`), against the template as it was when
the snapshot was taken.

## D4 — A command line, not an MCP server

Claude Code works in this repository and runs commands, so `uv run cadac ...`
is all it needs, and the standards, the rules and the skills load from the
repository itself. An MCP server would be needed only for a client that
cannot run commands, such as Claude Desktop; it can be added over the same
functions when somebody wants that, and is not built until then.

## D5 — The agent gets this repository's commands, not Archicad's

An agent sending Tapir commands of its own can create an attribute to get past
a missing one, and the API cannot undo. So what an agent may do in Archicad is
what `cadac` offers, each command written, reviewed and tested here. The same
rule Loriini's roadmap sets for its own agent, for the same reason.

## D6 — A model is built in a copy of the template, saved at every stage

Follows from D5's second half: with no undo, the way back is a file. The
builder, when it exists, works only in `projects/<name>/model/`, never in a
project somebody has open for their own work, and saves a copy after each
stage. The models are not committed (`.gitignore`): they are made from the
template, the standards, the brief and the spec, which are.

## D7 — Every standards file says how far it has got

`status: example | draft | agreed`. The scaffold has to ship with entries to
show the shape of each file, and an agent that reads a file of plausible names
will build with them. The status is what tells it not to: nothing is built
against a file that is not `agreed`, and `cadac validate` names the ones that
are not.

## D8 — Procedures are skills in `.claude/skills/`

Claude Code loads skills from there by itself, and only the one a task needs,
so a session is not carrying the build procedure while writing a brief. A
stage has a skill only once the commands behind it exist: a procedure with no
tool behind it would be improvised, which D5 rules out.

## D9 — Tapir's commands, from the Loriini add-on first

The reader asks Tapir's commands under `LoriiniTapir`, where the Loriini
add-on carries them, and falls back to a stand-alone Tapir under
`TapirCommand`. The office already installs the Loriini add-on, and its copy
of Tapir is the one whose source this was written against. One command,
`GetGraphicOverrideCombinations`, is Loriini's own; without that add-on the
section is reported unchecked.

## D10 — Unchecked is a failure of the audit, not of the template

A section the snapshot could not read is reported as unchecked, with the
reason, and the audit does not pass. The other two choices are both worse:
calling it missing blames the template for the tool's failure, and ignoring it
lets an audit pass that never looked.

## D11 — What the template has beyond the standards is told, not failed

A template carries hundreds of attributes and the standards list the ones a
spec may use. Failing on the rest would make the standards a copy of the
template. They are counted, and listed with `--extra`. Archicad's own
properties are left out even of that: they are in every project.
