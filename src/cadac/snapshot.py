"""What the open project holds, by name, as plain data.

The template cannot be read from its file: only Archicad opens a ``.tpl``. So
the template is opened in Archicad and asked, and the answer is written down
as JSON. That file does two jobs. The audit compares it with the standards,
and, committed beside the template, it is the diff the binary cannot give:
what changed between two versions of the template, in text.

Reading only. Nothing here changes the project.

Each section is read by itself. One that cannot be read -- an add-on without
the command, an older Archicad -- is recorded under ``unread`` with the
reason, and the rest are still read. The audit then says *unchecked* for it
rather than *missing*.

Two failures are not a section's and stop the reading at once, with one
message instead of thirty: no Archicad to ask, and no add-on carrying Tapir's
commands, which nearly every section needs.

``docs/archicad.md`` lists every command used here and where its shape was
read from.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from cadac.archicad import Archicad, ArchicadError, Unreachable
from cadac.standards import ELEMENT_TYPES

__all__ = ["read"]

#: Section -> the attribute type as ``GetAttributesByType`` spells it.
_ATTRIBUTES = {
    "layers": "Layer",
    "layer_combinations": "LayerCombination",
    "composites": "Composite",
    "profiles": "Profile",
    "surfaces": "Surface",
    "pen_sets": "PenTable",
    "zone_categories": "ZoneCategory",
}


def _attributes(archicad: Archicad, kind: str) -> list[dict[str, Any]]:
    """Every attribute of one type: its id, index and name, and no more --
    ``GetAttributesByType`` enumerates and says nothing else about them."""
    answer = archicad.tapir("GetAttributesByType", {"attributeType": kind})
    rows = answer.get("attributes") if isinstance(answer, dict) else None
    if not isinstance(rows, list):
        raise ArchicadError(f"GetAttributesByType gave no list for {kind}: {answer!r}")
    return [row for row in rows if isinstance(row, dict)]


def _names(rows: Iterable[Any]) -> list[str]:
    return sorted({str(row.get("name", "")) for row in rows if isinstance(row, dict)} - {""})


def _building_materials(archicad: Archicad) -> list[dict[str, Any]]:
    """Each building material with its intersection priority.

    Two calls, as for layers: the first enumerates, the second takes the ids
    and answers with the priority, already converted to the 0-999 the
    Building Materials dialog shows.
    """
    listed = [
        (str((row.get("attributeId") or {}).get("guid", "")), str(row.get("name", "")))
        for row in _attributes(archicad, "BuildingMaterial")
    ]
    listed = [(guid, name) for guid, name in listed if guid and name]
    if not listed:
        return []
    answer = archicad.tapir(
        "GetBuildingMaterials",
        {
            "attributeIds": [{"attributeId": {"guid": guid}} for guid, _ in listed],
            "fields": ["connPriority"],
        },
    )
    rows = answer.get("buildingMaterials") if isinstance(answer, dict) else None
    if not isinstance(rows, list) or len(rows) != len(listed):
        raise ArchicadError(
            f"GetBuildingMaterials answered for {len(rows) if isinstance(rows, list) else 0} "
            f"of {len(listed)} building materials; the lists must be parallel."
        )
    found = []
    for (_, name), row in zip(listed, rows, strict=True):
        priority = row.get("connPriority") if isinstance(row, dict) else None
        found.append({"name": name, "priority": priority if isinstance(priority, int) else None})
    return sorted(found, key=lambda row: row["name"])


def _favourites(archicad: Archicad, unread: dict[str, str]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for element in ELEMENT_TYPES:
        try:
            answer = archicad.tapir("GetFavoritesByType", {"elementType": element})
        except Unreachable:
            raise
        except ArchicadError as exc:
            unread[f"favourites ({element})"] = str(exc)
            continue
        names = answer.get("favorites") if isinstance(answer, dict) else None
        if not isinstance(names, list):
            unread[f"favourites ({element})"] = f"GetFavoritesByType gave no list: {answer!r}"
            continue
        found[element] = sorted(str(name) for name in names)
    return found


def _properties(archicad: Archicad) -> list[dict[str, str]]:
    answer = archicad.tapir("GetAllProperties")
    rows = answer.get("properties") if isinstance(answer, dict) else None
    if not isinstance(rows, list):
        raise ArchicadError(f"GetAllProperties gave no list: {answer!r}")
    found = {
        (str(row.get("propertyGroupName", "")), str(row.get("propertyName", "")))
        for row in rows
        if isinstance(row, dict)
    }
    return [{"group": group, "name": name} for group, name in sorted(found) if name]


def _graphic_overrides(archicad: Archicad) -> list[str]:
    answer = archicad.loriini("GetGraphicOverrideCombinations")
    rows = answer.get("combinations") if isinstance(answer, dict) else None
    if not isinstance(rows, list):
        raise ArchicadError(f"GetGraphicOverrideCombinations gave no list: {answer!r}")
    return _names(rows)


def _publisher_sets(archicad: Archicad) -> list[str]:
    answer = archicad.official("API.GetPublisherSetNames")
    names = answer.get("publisherSetNames") if isinstance(answer, dict) else None
    if not isinstance(names, list):
        raise ArchicadError(f"API.GetPublisherSetNames gave no list: {answer!r}")
    return sorted(str(name) for name in names)


def read(archicad: Archicad) -> dict[str, Any]:
    """Everything the audit compares, read from the project Archicad has open."""
    sections: dict[str, Any] = {}
    unread: dict[str, str] = {}

    # First, and not as a section: it is the question that finds out whether
    # there is an Archicad and an add-on to ask at all.
    info = archicad.tapir("GetProjectInfo")
    project = ""
    if isinstance(info, dict):
        project = str(info.get("projectName") or ("Untitled" if info.get("isUntitled") else ""))

    def attempt(section: str, reader: Callable[[], Any]) -> None:
        try:
            sections[section] = reader()
        except Unreachable:
            raise
        except ArchicadError as exc:
            unread[section] = str(exc)

    for section, kind in _ATTRIBUTES.items():
        attempt(section, lambda kind=kind: _names(_attributes(archicad, kind)))
    attempt("building_materials", lambda: _building_materials(archicad))
    sections["favourites"] = _favourites(archicad, unread)
    attempt("properties", lambda: _properties(archicad))
    attempt("graphic_overrides", lambda: _graphic_overrides(archicad))
    attempt("publisher_sets", lambda: _publisher_sets(archicad))

    return {"project": project, "sections": sections, "unread": unread}
