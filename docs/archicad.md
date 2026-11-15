# Archicad, as this repository talks to it

Every command `cadac` sends, the shape of its answer, and where that was read
from. Nothing here is from memory. Add to it when a command is added, and
correct it the first time a live Archicad disagrees.

**None of it has been run against a live Archicad from this repository yet.**
The tests send through a stand-in that answers in the shapes below. The
column *Seen live* says whether Loriini, which uses the same command, has run
it against Archicad 26.

## The protocol

Archicad listens for JSON over HTTP on `127.0.0.1`, port 19723 for the first
instance running and the next port up for each further one, and takes
`{"command": "API.<Name>", "parameters": {...}}`.

An add-on's command goes through `API.ExecuteAddOnCommand`, with
`addOnCommandId: {commandNamespace, commandName}` and
`addOnCommandParameters`. Tapir's commands answer under `LoriiniTapir` inside
the Loriini add-on and under `TapirCommand` in a stand-alone Tapir; Loriini's
own under `Loriini`. Archicad answers code `4010` for a namespace or command
no add-on registered.

An answer fails at two levels: the outer `succeeded: false` with `error`, and
an `error` inside `result.addOnCommandResponse` while the outer one says it
succeeded. `cadac.archicad` raises on both.

Source: Loriini's `src/sun_study/archicad/connection.py` and its
`docs/archicad.md`, both written against a live Archicad 26.

## Commands

All read-only.

| Command | Asked with | Answer used | Read from | Seen live |
|---|---|---|---|---|
| Tapir `GetAttributesByType` | `attributeType`: `Layer`, `LayerCombination`, `PenTable`, `Surface` | `attributes[]`: `attributeId.guid`, `index`, `name` | Loriini's code | yes, in Loriini |
| Tapir `GetAttributesByType` | `attributeType`: `BuildingMaterial`, `Composite`, `Profile`, `ZoneCategory` | the same | the type names in Tapir's `AttributeCommands.cpp` (`ConvertAttributeTypeStringToID`) | no |
| Tapir `GetBuildingMaterials` | `attributeIds[]`: `{attributeId: {guid}}`; `fields: ["connPriority"]` | `buildingMaterials[]`, parallel to the ids: `connPriority`, already the 0-999 of the dialog; or an error item | Tapir's `AttributeCommands.cpp` | no |
| Tapir `GetFavoritesByType` | `elementType` | `favorites[]`: names | Loriini's code | yes, for `Hatch` and `Wall` |
| Tapir `GetAllProperties` | nothing | `properties[]`: `propertyGroupName`, `propertyName` | Loriini's code; the group name in Tapir's `PropertyCommands.cpp` | yes, `propertyName` only |
| Tapir `GetProjectInfo` | nothing | `projectName`, `isUntitled` | Loriini's code | yes |
| Loriini `GetGraphicOverrideCombinations` | nothing | `combinations[]`: `guid`, `name` | Loriini's `ProjectCommands.cpp` | yes, in Loriini |
| `API.GetPublisherSetNames` | nothing | `publisherSetNames[]` | Graphisoft's JSON interface reference | no |

The element types `GetFavoritesByType` is asked for are `ELEMENT_TYPES` in
`cadac/standards.py`, each spelled as `GetElementTypeFromNonLocalizedName`
spells it in Tapir's `CommandBase.cpp`. A type Archicad keeps no favourites
for comes back as an error and is recorded as unread for that type alone.

Tapir's source here means the copy built into the Loriini add-on
(`archicad-addon/Tapir` in that repository).

## Not read yet

The audit does not check these, so `standards/` does not list them:

- **Master layouts** -- in the Layout Book's tree
  (`GetNavigatorItemTree`, `navigatorMapId: LayoutBook`), which Loriini reads.
- **Model view options** -- Tapir has `GetModelViewOptions`.
- **The view map's folders** -- `GetNavigatorItemTree`.
- **The classification system** -- Archicad has `API.GetAllClassificationSystems`.
- **Line types and fills** -- `GetAttributesByType` takes `Line` and `Fill`.
- **A favourite's own settings** -- which layer and building material it
  carries. Only its name is checked.

## What the add-on can create

Not used yet; recorded because the build stage depends on it. Read out of the
command names in Loriini's bundled Tapir, not run:

walls, doors, windows, slabs, columns, beams, roofs, stairs, zones, objects,
lamps, meshes, morphs, openings; sections, details, worksheets, interior
elevations; layouts, layout subsets, views, drawings; dimensions, labels,
texts, fills, lines; layers, layer combinations, building materials,
composites, profiles, surfaces, pen tables, zone categories; property groups
and definitions; classification systems and items; favourites from elements,
and favourites applied to elements.

Not there: curtain walls, railings, shells, skylights; starting a project from
a template; saving under another name; exporting a view as a picture.
