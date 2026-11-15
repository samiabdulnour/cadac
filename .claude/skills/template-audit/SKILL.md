---
name: template-audit
description: Check that the Archicad template holds everything the standards list -- layers, layer combinations, building materials and their priorities, composites, profiles, surfaces, pen sets, zone categories, favourites, properties, graphic overrides, publisher sets. Use after the template or anything in standards/ changes, before building a project from the template, or when asked whether the template is up to date.
---

# Auditing the template

The standards say what the office builds with; the template is the file that
has to hold it. The audit asks the template, through Archicad, and compares.
It only reads.

## Before you start

- Archicad must be open **on this machine** with the template open in it. In a
  cloud session it is not: say so, and offer to compare the last committed
  snapshot instead (`uv run cadac audit --snapshot template/snapshot.json`),
  making clear that this checks the template as it was when the snapshot was
  taken.
- Run `uv run cadac validate` first. The audit refuses to compare against
  standards that have a problem.

## Steps

1. `uv run cadac audit`. A second Archicad open on the machine is on
   `--port 19724`; ask which project is the template if unsure, and check the
   project name the audit prints.
2. Read the result:
   - **missing** -- the standards name it and the template lacks it. Where
     the line says the template has a name that differs only in case or
     spacing, that is almost always the same thing misspelled on one side.
   - **different** -- there, and not as the standards say (a building
     material's priority).
   - **unchecked** -- a part could not be read. This is not a pass. Give the
     reason as printed.
   - **in the template and not in the standards** -- told, not failed.
     `--extra` lists them. Worth a look when the person expects the standards
     to cover something.
3. For each missing or different item, **ask which side is wrong** unless it
   is plainly a typing slip in `standards/`. The template is fixed by a person
   in Archicad; the standards are fixed here. Do not create or change anything
   in the template through the API.
4. After fixes, run the audit again until it prints `PASSED`.
5. `uv run cadac snapshot`, and commit `template/snapshot.json` together with
   the template and any change to `standards/`, in one commit, so the three
   always describe the same template.

## Reporting

Give the person the counts and every missing, different and unchecked line as
printed. Do not shorten "FAILED" to "mostly fine".

The first run against a live Archicad may find that a command answers in
another shape than `docs/archicad.md` records -- the reader was written from
the add-on's source and has not been run. If a section comes back unchecked
with a message about a missing list, copy the message into your report and
note it in `docs/archicad.md`; that is a finding about the tool, not about the
template.
