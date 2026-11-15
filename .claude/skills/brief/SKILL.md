---
name: brief
description: Turn what a person asked for -- an email, a meeting note, a client's document, a sentence -- into projects/<name>/brief.yaml, the checked brief every later stage is built from. Use when starting a new project, when the person gives or changes requirements for one, or when asked whether a brief is ready to build from.
---

# Writing a brief

The brief is the first gate. A spec is written from it and a model is built
from the spec, so a number that is wrong or guessed here is wrong in every
drawing later. Your job is to write down what the person asked for, exactly,
and to make what they did not say visible.

## Steps

1. **Start from the example.** Copy `projects/_example/` to
   `projects/<name>/`, the name short and in lower case with hyphens. Keep the
   file's comments; they explain each part to the next reader.
2. **Fill in only what you were given.** Every value in the brief traces to
   something the person said or a document they gave. Where they gave a
   document, read all of it before writing.
3. **Put everything else under `open_questions`.** A missing storey height, an
   ambiguous use, two figures that disagree, an area that does not fit the
   site: each is one question, worded so it can be answered in a line. Do not
   pick a "sensible default" and do not leave the example's value in place --
   remove a key you have no value for and ask.
4. **Check the arithmetic the brief implies** and add a question where it does
   not hold: the programme's total area against the site area times the floor
   space ratio, the storeys times their heights against the height limit.
   Say the numbers in the question.
5. **Run `uv run cadac validate`** and fix every problem it lists for the
   brief.
6. **Give the person the open questions**, all at once, and write their
   answers into the brief. Repeat until the list is empty.
7. **Ask for approval.** The person fills `approved` with their name and the
   date, or tells you to with both. Never fill it on your own.

## Rules

- Planning controls and anything else particular to the site go under
  `controls`, each named as the source names it. The tool carries them and
  does not check them; say so if the person assumes otherwise.
- Lengths are metres and areas square metres. Convert, and note the original
  figure in a comment when you do.
- A brief that changes after approval is a new approval: clear `approved`,
  say what changed, and ask again.
- `validate` reporting "not ready to build from" is the normal state of a
  brief in progress, not an error.

## Done when

`uv run cadac validate` lists no problem for the brief and reports it
approved. Tell the person the next stage -- the spec -- is not built yet.
