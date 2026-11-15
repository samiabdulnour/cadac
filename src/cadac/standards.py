"""The office standards, read from ``standards/*.yaml``.

One list, used twice. It tells whoever writes a spec which names exist -- no
other layer, favourite or property may be used -- and it tells the audit what
the template must contain. There is no second manifest to drift from it.

Reading never raises on what a person wrote. Every problem is collected and
returned, so one run of ``cadac validate`` lists them all.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "ELEMENT_TYPES",
    "FILES",
    "SECTIONS",
    "STATUSES",
    "Standards",
    "load",
]

#: How far a file has got. ``example`` is what the scaffold ships: the right
#: shape, somebody else's names. ``draft`` is the office's own names, not yet
#: agreed. Nothing is built against a file that is not ``agreed``.
STATUSES = ("example", "draft", "agreed")

#: The element types a favourite can belong to, spelled as the add-on spells
#: them (``GetElementTypeFromNonLocalizedName`` in Tapir's ``CommandBase.cpp``).
#: ``Hatch`` is the Fill tool and ``PolyLine`` the Polyline tool.
ELEMENT_TYPES = (
    "Wall",
    "Column",
    "Beam",
    "Window",
    "Door",
    "Object",
    "Lamp",
    "Slab",
    "Roof",
    "Mesh",
    "Zone",
    "Hatch",
    "Line",
    "PolyLine",
    "Text",
    "Label",
    "Dimension",
    "Stair",
    "Railing",
    "Morph",
    "Shell",
    "Skylight",
    "Opening",
    "CurtainWall",
)

#: Each file and the lists of plain names it may hold. ``attributes.yaml`` also
#: holds ``building_materials``, ``favourites.yaml`` holds ``favourites``,
#: ``properties.yaml`` holds ``property_groups`` and ``naming.yaml`` holds
#: ``patterns``; those four have their own shape and their own reader below.
FILES: Mapping[str, tuple[str, ...]] = {
    "layers": ("layers", "layer_combinations"),
    "attributes": ("composites", "profiles", "surfaces", "pen_sets", "zone_categories"),
    "favourites": (),
    "properties": (),
    "documentation": ("graphic_overrides", "publisher_sets"),
    "naming": (),
}

_OTHER_KEYS: Mapping[str, tuple[str, ...]] = {
    "attributes": ("building_materials",),
    "favourites": ("favourites",),
    "properties": ("property_groups",),
    "naming": ("patterns",),
}

#: Every list of plain names, in the order a report prints them.
SECTIONS = tuple(section for sections in FILES.values() for section in sections)


@dataclass(frozen=True)
class Standards:
    """What the office's template must contain, and so what a spec may name."""

    #: File name without its extension -> ``example``, ``draft`` or ``agreed``.
    status: Mapping[str, str] = field(default_factory=dict)
    #: Section -> its names, for every section in ``SECTIONS``.
    names: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    #: Building material -> its intersection priority as Archicad's dialog
    #: shows it, or ``None`` where the standards do not fix one.
    building_materials: Mapping[str, int | None] = field(default_factory=dict)
    #: Element type -> the favourites a spec may place of that type.
    favourites: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    #: ``(group, property)`` for every property the template must define.
    properties: tuple[tuple[str, str], ...] = ()
    #: What is named -> the pattern its name must match in full.
    patterns: Mapping[str, str] = field(default_factory=dict)

    def not_agreed(self) -> tuple[str, ...]:
        """The files a build may not rely on yet, as ``layers (example)``."""
        return tuple(
            f"{name} ({state})" for name, state in self.status.items() if state != "agreed"
        )


def load(directory: Path) -> tuple[Standards, list[str]]:
    """Read every standards file in ``directory``.

    Returns what could be read and every problem found, each one naming its
    file. A file with a problem still contributes whatever of it was sound.
    """
    problems: list[str] = []
    status: dict[str, str] = {}
    names: dict[str, tuple[str, ...]] = {section: () for section in SECTIONS}
    building_materials: dict[str, int | None] = {}
    favourites: dict[str, tuple[str, ...]] = {}
    properties: tuple[tuple[str, str], ...] = ()
    patterns: dict[str, str] = {}

    for name, sections in FILES.items():
        where = f"{name}.yaml"
        data = _read(directory / where, where, problems)
        if data is None:
            continue
        state = data.get("status")
        if state in STATUSES:
            status[name] = str(state)
        else:
            problems.append(f"{where}: status is {state!r}; it must be one of {list(STATUSES)}.")
        allowed = ("status", *sections, *_OTHER_KEYS.get(name, ()))
        for key in data:
            if key not in allowed:
                problems.append(f"{where}: {key!r} is not a section of this file.")
        for section in sections:
            names[section] = _names(data.get(section), f"{where}: {section}", problems)
        if name == "attributes":
            building_materials = _building_materials(data.get("building_materials"), problems)
        elif name == "favourites":
            favourites = _favourites(data.get("favourites"), problems)
        elif name == "properties":
            properties = _properties(data.get("property_groups"), problems)
        elif name == "naming":
            patterns = _patterns(data.get("patterns"), problems)

    return (
        Standards(
            status=status,
            names=names,
            building_materials=building_materials,
            favourites=favourites,
            properties=properties,
            patterns=patterns,
        ),
        problems,
    )


def _read(path: Path, where: str, problems: list[str]) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        problems.append(f"{where}: the file is missing.")
        return None
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        problems.append(f"{where}: not valid YAML ({' '.join(str(exc).split())}).")
        return None
    if not isinstance(data, dict):
        problems.append(f"{where}: expected sections with names under them.")
        return None
    return data


def _name_of(entry: Any) -> str | None:
    """An entry's name. An entry is either the name alone or a mapping that
    carries ``name`` beside whatever else the file keeps about it."""
    if isinstance(entry, str):
        return entry.strip() or None
    if isinstance(entry, dict) and isinstance(entry.get("name"), str):
        return entry["name"].strip() or None
    return None


def _entries(value: Any, where: str, problems: list[str]) -> list[tuple[str, Any]]:
    """The named entries of a list, with the blank and the repeated reported."""
    if value is None:
        return []
    if not isinstance(value, list):
        problems.append(f"{where}: expected a list.")
        return []
    found: list[tuple[str, Any]] = []
    seen: set[str] = set()
    for position, entry in enumerate(value, start=1):
        name = _name_of(entry)
        if name is None:
            problems.append(f"{where}: entry {position} has no name.")
        elif name in seen:
            problems.append(f"{where}: {name!r} is listed twice.")
        else:
            seen.add(name)
            found.append((name, entry))
    return found


def _names(value: Any, where: str, problems: list[str]) -> tuple[str, ...]:
    return tuple(name for name, _ in _entries(value, where, problems))


def _building_materials(value: Any, problems: list[str]) -> dict[str, int | None]:
    where = "attributes.yaml: building_materials"
    found: dict[str, int | None] = {}
    for name, entry in _entries(value, where, problems):
        priority = entry.get("priority") if isinstance(entry, dict) else None
        # `bool` is an `int` to Python, and `priority: yes` is a slip, not a 1.
        if priority is not None and (
            isinstance(priority, bool) or not isinstance(priority, int) or not 0 <= priority <= 999
        ):
            problems.append(
                f"{where}: {name!r} has priority {priority!r}; "
                "it must be a whole number from 0 to 999."
            )
            priority = None
        found[name] = priority
    return found


def _favourites(value: Any, problems: list[str]) -> dict[str, tuple[str, ...]]:
    where = "favourites.yaml: favourites"
    by_type: dict[str, list[str]] = {}
    for name, entry in _entries(value, where, problems):
        element = entry.get("element") if isinstance(entry, dict) else None
        if element not in ELEMENT_TYPES:
            problems.append(
                f"{where}: {name!r} has element {element!r}; "
                f"it must be one of {', '.join(ELEMENT_TYPES)}."
            )
            continue
        by_type.setdefault(str(element), []).append(name)
    return {element: tuple(names) for element, names in by_type.items()}


def _properties(value: Any, problems: list[str]) -> tuple[tuple[str, str], ...]:
    where = "properties.yaml: property_groups"
    found: list[tuple[str, str]] = []
    for group, entry in _entries(value, where, problems):
        listed = entry.get("properties") if isinstance(entry, dict) else None
        for name, _ in _entries(listed, f"{where}: {group}", problems):
            found.append((group, name))
    return tuple(found)


def _patterns(value: Any, problems: list[str]) -> dict[str, str]:
    where = "naming.yaml: patterns"
    if value is None:
        return {}
    if not isinstance(value, dict):
        problems.append(f"{where}: expected what is named, each with its pattern.")
        return {}
    found: dict[str, str] = {}
    for what, entry in value.items():
        pattern = entry.get("pattern") if isinstance(entry, dict) else entry
        if not isinstance(pattern, str) or not pattern:
            problems.append(f"{where}: {what!r} has no pattern.")
            continue
        try:
            re.compile(pattern)
        except re.error as exc:
            problems.append(f"{where}: {what!r} is not a valid pattern ({exc}).")
            continue
        found[str(what)] = pattern
    return found
