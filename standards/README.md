# Standards

What the office builds with, as data. One list, used twice: it tells an agent
which names exist, and it tells the audit what the template must contain.

| File | Holds |
|---|---|
| `layers.yaml` | layers, layer combinations |
| `attributes.yaml` | building materials and their intersection priorities, composites, profiles, surfaces, pen sets, zone categories |
| `favourites.yaml` | the favourites a spec may place, each with the tool it belongs to and when to use it |
| `properties.yaml` | property groups and their properties |
| `documentation.yaml` | graphic override combinations, publisher sets |
| `naming.yaml` | the patterns IDs, zone numbers and layout numbers must match |

## How an entry is written

A name, or a name with more beside it:

```yaml
layers:
  - "Wall - External"
  - name: "Zone - Room"
    note: one zone for every room
```

Names are matched exactly as Archicad spells them. `note` and `use` are for
the reader -- a person or an agent choosing between two favourites -- and are
not checked.

## Status

Every file starts with `status`:

- `example` -- what this repository shipped with: the right shape, not this
  office's names.
- `draft` -- the office's names, not agreed yet.
- `agreed` -- what a model may be built against.

`uv run cadac validate` lists the files that are not agreed.

## Changing the standards

A change here is a change to what the template must hold. Change the template
to match, run the audit, and commit the standards, the template and its
snapshot together. `uv run cadac validate` catches a misspelled section, a
name listed twice, a favourite on a tool the add-on does not know, a priority
outside 0 to 999 and a pattern that is not one.
