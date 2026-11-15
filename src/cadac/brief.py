"""A project's brief, read from ``projects/<name>/brief.yaml``.

The brief is what a person asked for, written down so that it can be checked
and so that the same brief gives the same building twice. It is the first gate
of the workflow: nothing is specified or built from a brief that has a problem,
an open question or no approval.

Only what every project has is required. Anything else a project needs --
planning controls, a parking rate, a setback -- goes under ``controls`` as it is
worded in the brief, and is checked by a person, not here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = ["Brief", "load"]


@dataclass(frozen=True)
class Brief:
    name: str = ""
    #: The whole file, for whoever writes the spec from it.
    data: dict[str, Any] = field(default_factory=dict)
    #: What is still to be answered by a person. Empty before a build.
    open_questions: tuple[str, ...] = ()
    #: Who approved it and when, as written; empty until somebody has.
    approved_by: str = ""

    @property
    def ready(self) -> bool:
        """May a spec be written from it? Only once nothing is open and a
        person has put their name to it."""
        return bool(self.approved_by) and not self.open_questions


def _number(value: Any) -> float | None:
    # `bool` is an `int` to Python; `storeys: yes` is not one storey.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _positive(data: Any, key: str, where: str, problems: list[str], *, whole: bool = False) -> None:
    value = _number(data.get(key)) if isinstance(data, dict) else None
    if value is None or value <= 0 or (whole and value != int(value)):
        kind = "a whole number above zero" if whole else "a number above zero"
        found = data.get(key) if isinstance(data, dict) else None
        problems.append(f"{where}: {key} is {found!r}; it must be {kind}.")


def load(path: Path) -> tuple[Brief, list[str]]:
    """Read a brief and every problem with it."""
    where = str(path)
    problems: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Brief(), [f"{where}: the file is missing."]
    except yaml.YAMLError as exc:
        return Brief(), [f"{where}: not valid YAML ({' '.join(str(exc).split())})."]
    if not isinstance(data, dict):
        return Brief(), [f"{where}: expected project, site, building and programme."]

    project = data.get("project")
    name = str(project.get("name") or "").strip() if isinstance(project, dict) else ""
    if not name:
        problems.append(f"{where}: project has no name.")

    site = data.get("site")
    if not isinstance(site, dict):
        problems.append(f"{where}: there is no site.")
    else:
        if not str(site.get("address") or "").strip():
            problems.append(f"{where}: site has no address.")
        _positive(site, "area_m2", f"{where}: site", problems)

    building = data.get("building")
    if not isinstance(building, dict):
        problems.append(f"{where}: there is no building.")
    else:
        if not str(building.get("use") or "").strip():
            problems.append(f"{where}: building has no use.")
        _positive(building, "storeys_above_ground", f"{where}: building", problems, whole=True)
        basements = _number(building.get("basements", 0))
        if basements is None or basements < 0 or basements != int(basements):
            problems.append(
                f"{where}: building: basements is {building.get('basements')!r}; "
                "it must be a whole number, zero or more."
            )
        heights = building.get("floor_to_floor_m")
        if not isinstance(heights, dict) or not heights:
            problems.append(f"{where}: building has no floor_to_floor_m.")
        else:
            for level in heights:
                _positive(heights, level, f"{where}: building: floor_to_floor_m", problems)

    programme = data.get("programme")
    if not isinstance(programme, list) or not programme:
        problems.append(f"{where}: the programme lists nothing.")
    else:
        seen: set[str] = set()
        for position, row in enumerate(programme, start=1):
            at = f"{where}: programme row {position}"
            kind = str(row.get("type") or "").strip() if isinstance(row, dict) else ""
            if not kind:
                problems.append(f"{at} has no type.")
                continue
            if kind in seen:
                problems.append(f"{at}: {kind!r} is listed twice.")
            seen.add(kind)
            _positive(row, "count", at, problems, whole=True)
            _positive(row, "area_m2", at, problems)

    questions = data.get("open_questions") or []
    if not isinstance(questions, list):
        problems.append(f"{where}: open_questions must be a list.")
        questions = []

    approved = data.get("approved")
    approved_by = ""
    if isinstance(approved, dict) and approved.get("by") and approved.get("date"):
        approved_by = f"{approved['by']}, {approved['date']}"
    elif approved:
        problems.append(f"{where}: approved needs both by and date.")

    return (
        Brief(
            name=name,
            data=data,
            open_questions=tuple(str(question) for question in questions),
            approved_by=approved_by,
        ),
        problems,
    )
