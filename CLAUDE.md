# cadac — rules for every session

This repository holds an office's Archicad standards as data, the template
they describe, and the checks between them. Your job here is to make Archicad
projects that follow those standards, and to keep the standards and the
template true to each other. `README.md` has the workflow and what of it
exists.

## The rules

1. **Never invent a style.** A layer, favourite, building material, composite,
   property, pen set or layout master is used only if `standards/` lists it.
   If the work needs one that is not listed, stop and ask the person. Do not
   create an attribute or a favourite in a project to get past this.
2. **Do not build against standards that are not agreed.** Each file in
   `standards/` carries a `status`. `example` is the scaffold's placeholder
   names; `draft` is not agreed. `uv run cadac validate` says which are which.
3. **A brief is a person's.** Do not guess a number the brief does not give:
   write it under `open_questions`. Do not fill `approved`; a person does.
   Nothing is specified or built from a brief with an open question or no
   approval.
4. **Never work in somebody's live project.** A model is built in a copy of
   the template under `projects/<name>/model/`. The Archicad API cannot undo,
   so the copy saved after each stage is the only way back.
5. **Do not send Archicad commands of your own.** Use `uv run cadac ...`. If
   a command you need does not exist, say so; building it is a change to this
   repository, reviewed like any other, not something to improvise in a
   session.
6. **Do not change the template through the API.** The audit only reads. A
   template that fails it is fixed by a person in Archicad, or the standards
   are corrected -- ask which is wrong.
7. **Report what happened.** A failed check is listed with its output, never
   summarised away. *Unchecked* is not *passed*.

## Where Archicad is

Archicad runs on the person's workstation, not in a cloud session.
`cadac validate`, `cadac audit --snapshot <file>` and the tests run anywhere.
`cadac snapshot` and `cadac audit` need Archicad open on the same machine. If
you cannot reach it, say so and do the file work; do not treat it as a fault to
work around.

## Commands

```bash
uv run cadac validate
```

```bash
uv run cadac audit
```

```bash
uv run pytest
```

Run `validate` at the start of any work on a project or the standards, and the
tests before committing a change to `src/`.

## Working in this repository

- **Names are exact.** Archicad matches a layer or a favourite by its spelling,
  spaces included. Copy names from `standards/` or `template/snapshot.json`;
  never retype them from memory.
- **Lengths are metres, areas square metres**, in briefs and in everything
  sent to Archicad. Millimetres only where a key says `_mm`.
- **Facts about Archicad's API go in `docs/archicad.md`** with where each came
  from: read in the add-on's source, read in Graphisoft's reference, or run
  against a live Archicad. Do not write one from memory.
- **Decisions go in `docs/decisions.md`**, numbered, with the reason. Read it
  before changing how something works.
- **The template and other Archicad files are in Git LFS.** A machine needs
  `git lfs install` once. A project's working model and its printed outputs
  are not committed (`.gitignore`).
- The procedures for each stage are skills in `.claude/skills/`. Stages
  without a skill are not built yet: do not improvise them.
