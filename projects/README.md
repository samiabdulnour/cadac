# Projects

One folder per project.

| File | What | Kept in git |
|---|---|---|
| `brief.yaml` | what was asked for, checked and approved | yes |
| `spec.json` | every element to build, each naming a favourite | yes -- format not designed yet |
| `reports/` | the model check and the hand-over report | yes -- not built yet |
| `model/` | the Archicad file: a copy of the template, filled and saved at each stage | no |
| `out/` | what the model publishes: PDFs, pictures, IFC | no |

`_example/` is the starting point for a new brief; copy the folder. It is
checked by `uv run cadac validate` and by the tests like any other, so it
always shows a brief the tool accepts.

The model and its outputs are not committed because they are made from what
is: the same template, standards, brief and spec give the same model again.
