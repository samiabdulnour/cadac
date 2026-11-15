"""Does the template hold what the standards list?

A comparison of two plain things: the standards (``standards.load``) and a
snapshot of a project (``snapshot.read``, or the JSON it was saved as). No
Archicad here, so every rule below is covered by a test.

What it reports:

* **missing** -- the standards name it and the template does not have it. A
  spec that names it would fail in the build, so the audit fails.
* **different** -- it is there, and not as the standards say: a building
  material at another intersection priority. The audit fails.
* **unchecked** -- the standards list something for a section and the
  snapshot could not read that section. Not proof of a fault, and not a pass
  either: an audit that did not look has not found anything.
* **extra** -- the template has it and the standards do not mention it. Only
  told, never failed: a template carries far more than a spec may use.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from cadac.standards import SECTIONS, Standards

__all__ = ["Finding", "Report", "compare"]

#: Each section of plain names, as one of its entries is called in a report.
_KINDS = {
    "layers": "layer",
    "layer_combinations": "layer combination",
    "composites": "composite",
    "profiles": "profile",
    "surfaces": "surface",
    "pen_sets": "pen set",
    "zone_categories": "zone category",
    "graphic_overrides": "graphic override",
    "publisher_sets": "publisher set",
}


@dataclass(frozen=True)
class Finding:
    """One thing the template does not hold as the standards say."""

    kind: str
    name: str
    detail: str = ""

    def describe(self) -> str:
        return f"{self.kind}: {self.name}" + (f" -- {self.detail}" if self.detail else "")


@dataclass
class Report:
    missing: list[Finding] = field(default_factory=list)
    different: list[Finding] = field(default_factory=list)
    #: ``(section, why it could not be read)``
    unchecked: list[tuple[str, str]] = field(default_factory=list)
    #: Kind -> the template's names the standards do not mention.
    extra: dict[str, list[str]] = field(default_factory=dict)
    #: How many names were looked for and found as the standards say.
    confirmed: int = 0

    @property
    def passed(self) -> bool:
        return not (self.missing or self.different or self.unchecked)


def _tidy(name: str) -> str:
    """What two names share when they differ only in case or spacing."""
    return " ".join(name.split()).casefold()


def _near(name: str, present: Iterable[str]) -> str:
    """Why a name that looks present is still missing. Archicad matches names
    exactly, so a favourite spelled with a second space is another favourite;
    saying which one it nearly was saves a search through the dialog."""
    for other in present:
        if other != name and _tidy(other) == _tidy(name):
            return f"the template has {other!r}, which differs only in case or spacing"
    return ""


def _check(report: Report, kind: str, wanted: Iterable[str], present: Iterable[str]) -> None:
    have = list(present)
    exact = set(have)
    wanted = list(wanted)
    for name in wanted:
        if name in exact:
            report.confirmed += 1
        else:
            report.missing.append(Finding(kind, name, _near(name, have)))
    listed = set(wanted)
    extra = sorted(name for name in exact if name not in listed)
    if extra:
        report.extra[kind] = extra


def compare(standards: Standards, snapshot: Mapping[str, Any]) -> Report:
    """Hold a snapshot of the template against the standards."""
    sections: Mapping[str, Any] = snapshot.get("sections") or {}
    unread: Mapping[str, Any] = snapshot.get("unread") or {}
    report = Report()

    def read(section: str, wanted: Any) -> Any | None:
        """The snapshot's answer for a section, or ``None`` when there is
        nothing to hold against it -- noted as unchecked if the standards list
        anything there."""
        if section in sections:
            return sections[section]
        if wanted:
            report.unchecked.append(
                (section, str(unread.get(section) or "the snapshot does not have this section"))
            )
        return None

    for section in SECTIONS:
        wanted = standards.names.get(section, ())
        present = read(section, wanted)
        if present is not None:
            _check(report, _KINDS[section], wanted, present)

    materials = read("building_materials", standards.building_materials)
    if materials is not None:
        priorities = {str(row.get("name")): row.get("priority") for row in materials}
        _check(report, "building material", standards.building_materials, priorities)
        for name, priority in standards.building_materials.items():
            if priority is None or name not in priorities:
                continue
            found = priorities[name]
            if found is None:
                report.unchecked.append(
                    (f"priority of {name}", "the snapshot does not carry its priority")
                )
            elif found != priority:
                # It was counted as confirmed for being there; it is not.
                report.confirmed -= 1
                report.different.append(
                    Finding(
                        "building material",
                        name,
                        f"priority {found} in the template, {priority} in the standards",
                    )
                )

    favourites = read("favourites", standards.favourites)
    if favourites is not None:
        for element, wanted in standards.favourites.items():
            if element not in favourites:
                report.unchecked.append(
                    (
                        f"favourites ({element})",
                        str(
                            unread.get(f"favourites ({element})")
                            or "the snapshot did not read this element type"
                        ),
                    )
                )
                continue
            _check(report, f"favourite ({element})", wanted, favourites[element])

    properties = read("properties", standards.properties)
    if properties is not None:
        present = [f"{row.get('group')} / {row.get('name')}" for row in properties]
        wanted = [f"{group} / {name}" for group, name in standards.properties]
        _check(report, "property", wanted, present)
        # Archicad's own properties are in every project and are nobody's
        # standard; listing hundreds of them as extra would bury the rest.
        report.extra.pop("property", None)

    return report
