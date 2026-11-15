"""The command line: ``cadac validate``, ``cadac snapshot``, ``cadac audit``.

``validate`` reads only files and runs anywhere. ``snapshot`` and ``audit``
ask a running Archicad, so they run on the machine Archicad is open on --
``audit --snapshot <file>`` aside, which compares a snapshot already taken.

Every command ends 0 when there is nothing to fix and 1 when there is, so a
script, a hook or an agent can tell without reading the words.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from cadac import audit, brief, snapshot, standards
from cadac.archicad import DEFAULT_PORT, Archicad, ArchicadError

#: Where a snapshot of the template is kept: beside the template, committed,
#: so two versions of a binary file can be compared in text.
TEMPLATE_SNAPSHOT = Path("template") / "snapshot.json"


def _say(text: str = "") -> None:
    print(text)


def _problems(title: str, problems: Sequence[str]) -> None:
    _say(f"{title}: {len(problems)} to fix")
    for problem in problems:
        _say(f"  - {problem}")


def validate(root: Path) -> int:
    """Check the standards and every brief. Files only."""
    found, problems = standards.load(root / "standards")
    failed = bool(problems)
    if problems:
        _problems("standards", problems)
    else:
        _say("standards: read without a problem")
    waiting = found.not_agreed()
    if waiting:
        _say(f"  not agreed yet, so nothing may be built against them: {', '.join(waiting)}")

    briefs = sorted((root / "projects").glob("*/brief.yaml"))
    for path in briefs:
        read, problems = brief.load(path)
        shown = path.relative_to(root)
        if problems:
            failed = True
            _problems(str(shown), problems)
        elif read.ready:
            _say(f"{shown}: read without a problem; approved by {read.approved_by}")
        else:
            why = (
                f"{len(read.open_questions)} open question(s)"
                if read.open_questions
                else "not approved"
            )
            _say(f"{shown}: read without a problem; not ready to build from ({why})")
    if not briefs:
        _say("projects: no brief yet")
    return 1 if failed else 0


def _take(port: int) -> dict[str, Any]:
    return snapshot.read(Archicad(port))


def take_snapshot(root: Path, port: int, out: Path | None) -> int:
    """Write down what the open project holds."""
    taken = _take(port)
    target = out if out is not None else root / TEMPLATE_SNAPSHOT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(taken, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    _say(f"Read {taken.get('project') or 'the open project'} on port {port} into {target}")
    for section, reason in sorted((taken.get("unread") or {}).items()):
        _say(f"  could not read {section}: {reason}")
    return 0


def run_audit(root: Path, port: int, saved: Path | None, show_extra: bool) -> int:
    """Hold the template against the standards."""
    found, problems = standards.load(root / "standards")
    if problems:
        _problems("standards", problems)
        _say("The audit compares against the standards, so they are fixed first.")
        return 1
    if saved is not None:
        taken = json.loads(saved.read_text(encoding="utf-8"))
        source = str(saved)
    else:
        taken = _take(port)
        source = f"{taken.get('project') or 'the open project'} on port {port}"
    report = audit.compare(found, taken)

    _say(f"Template audit of {source}")
    _say(f"  as the standards say: {report.confirmed}")
    for title, findings in (("missing", report.missing), ("different", report.different)):
        _say(f"  {title}: {len(findings)}")
        for finding in findings:
            _say(f"    - {finding.describe()}")
    _say(f"  unchecked: {len(report.unchecked)}")
    for section, reason in report.unchecked:
        _say(f"    - {section}: {reason}")
    extra = sum(len(names) for names in report.extra.values())
    _say(f"  in the template and not in the standards: {extra}")
    if show_extra:
        for kind, names in report.extra.items():
            for name in names:
                _say(f"    - {kind}: {name}")
    waiting = found.not_agreed()
    if waiting:
        _say(f"  standards not agreed yet: {', '.join(waiting)}")
    _say("PASSED" if report.passed else "FAILED")
    return 0 if report.passed else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cadac", description="Office standards for Archicad, and the checks that hold to them."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="the repository: the folder holding standards/, template/ and projects/",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("validate", help="check the standards and every brief; files only")

    port_help = "Archicad's JSON port; 19723 for the first one running, 19724 for the second"
    taking = commands.add_parser("snapshot", help="write down what the open project holds")
    taking.add_argument("--port", type=int, default=DEFAULT_PORT, help=port_help)
    taking.add_argument(
        "--out", type=Path, help=f"where to write it; {TEMPLATE_SNAPSHOT} if not given"
    )

    auditing = commands.add_parser("audit", help="hold the template against the standards")
    auditing.add_argument("--port", type=int, default=DEFAULT_PORT, help=port_help)
    auditing.add_argument(
        "--snapshot", type=Path, help="compare a snapshot already taken, without asking Archicad"
    )
    auditing.add_argument(
        "--extra", action="store_true", help="also list what the template has beyond the standards"
    )

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return validate(args.root)
        if args.command == "snapshot":
            return take_snapshot(args.root, args.port, args.out)
        return run_audit(args.root, args.port, args.snapshot, args.extra)
    except ArchicadError as exc:
        print(f"cadac: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
