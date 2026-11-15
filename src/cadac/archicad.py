"""One request to a running Archicad, and its answer or its refusal.

Archicad listens for JSON on ``http://127.0.0.1:19723`` -- the next instance
on 19724, and so on -- and takes ``{"command": "API.<Name>", "parameters":
{...}}``. An add-on's commands are reached through one of Archicad's own::

    {"command": "API.ExecuteAddOnCommand",
     "parameters": {"addOnCommandId": {"commandNamespace": "<namespace>",
                                       "commandName": "<Name>"},
                    "addOnCommandParameters": {...}}}

The commands used here are Tapir's. The Loriini add-on carries them under the
namespace ``LoriiniTapir`` and its own under ``Loriini``; a stand-alone Tapir
answers under ``TapirCommand``. Whichever of the two Tapir namespaces answers
first is kept.

**An answer can fail at two levels.** The outer one carries ``succeeded`` and
maybe ``error``. The add-on's own answer, under
``result.addOnCommandResponse``, can carry an ``error`` while the outer one
says it succeeded. Both raise here, so an error is never read as data.

Nothing in this module is run by the tests against an Archicad, because there
is none to run against; they send through a stand-in. ``docs/archicad.md``
says where each fact came from.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

__all__ = [
    "DEFAULT_PORT",
    "Archicad",
    "ArchicadError",
    "CommandFailed",
    "NotRunning",
    "Unreachable",
]

DEFAULT_PORT = 19723

#: Tapir's commands inside the Loriini add-on, then a stand-alone Tapir.
TAPIR_NAMESPACES = ("LoriiniTapir", "TapirCommand")
LORIINI_NAMESPACE = "Loriini"

#: Archicad's code for a namespace or command that no add-on registered.
NOT_REGISTERED = 4010

Send = Callable[[dict[str, Any]], dict[str, Any]]


class ArchicadError(Exception):
    """Any failure talking to Archicad."""


class Unreachable(ArchicadError):
    """Archicad could not be asked at all, so asking again for something else
    will not go better. Apart from a refusal, which is about one command."""


class NotRunning(Unreachable):
    """Nothing is listening on the port."""


class CommandFailed(ArchicadError):
    """Archicad or the add-on refused a command."""

    def __init__(self, message: str, code: Any = None) -> None:
        super().__init__(message)
        self.code = code


def _http(port: int, timeout: float) -> Send:
    url = f"http://127.0.0.1:{port}"

    def send(payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
        except urllib.error.URLError as exc:
            raise NotRunning(
                f"Could not reach Archicad at {url} ({exc.reason}). It has to be running "
                "on this machine with a project open. A second Archicad is on the next "
                "port up: try --port 19724."
            ) from exc
        except TimeoutError as exc:
            raise Unreachable(
                f"Archicad did not answer within {timeout:g}s. A dialog waiting to be "
                "clicked stops it answering at all."
            ) from exc
        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as exc:
            raise Unreachable(
                f"Archicad answered with something that is not JSON: {body[:200]!r}"
            ) from exc
        if not isinstance(decoded, dict):
            raise Unreachable(f"Archicad answered with something unexpected: {decoded!r}")
        return decoded

    return send


class Archicad:
    """A running Archicad, asked one command at a time."""

    def __init__(
        self, port: int = DEFAULT_PORT, *, timeout: float = 60.0, send: Send | None = None
    ) -> None:
        self.port = port
        self._send = send if send is not None else _http(port, timeout)
        self._tapir_namespace: str | None = None

    def official(self, command: str, parameters: dict[str, Any] | None = None) -> Any:
        """Run one of Archicad's own ``API.*`` commands."""
        response = self._send({"command": command, "parameters": parameters or {}})
        if response.get("succeeded"):
            return response.get("result")
        error = response.get("error") or {}
        said = error.get("message") or repr(response)
        raise CommandFailed(f"{command} was refused: {said}", error.get("code"))

    def _addon(self, namespace: str, command: str, parameters: dict[str, Any] | None) -> Any:
        result = self.official(
            "API.ExecuteAddOnCommand",
            {
                "addOnCommandId": {"commandNamespace": namespace, "commandName": command},
                "addOnCommandParameters": parameters or {},
            },
        )
        inner = result.get("addOnCommandResponse") if isinstance(result, dict) else None
        if inner is None:
            raise CommandFailed(f"{namespace}.{command} gave no answer: {result!r}")
        error = inner.get("error") if isinstance(inner, dict) else None
        if isinstance(error, dict):
            said = error.get("message") or repr(error)
            raise CommandFailed(f"{namespace}.{command} failed: {said}", error.get("code"))
        return inner

    def tapir(self, command: str, parameters: dict[str, Any] | None = None) -> Any:
        """Run one of Tapir's commands, from whichever add-on carries them."""
        if self._tapir_namespace is not None:
            return self._addon(self._tapir_namespace, command, parameters)
        first: CommandFailed | None = None
        for namespace in TAPIR_NAMESPACES:
            try:
                answer = self._addon(namespace, command, parameters)
            except CommandFailed as exc:
                if exc.code != NOT_REGISTERED:
                    raise
                first = first or exc
                continue
            self._tapir_namespace = namespace
            return answer
        raise CommandFailed(
            f"No add-on answers Tapir's {command}. Install the Loriini add-on, which "
            "carries Tapir's commands, or Tapir itself.",
            NOT_REGISTERED,
        ) from first

    def loriini(self, command: str, parameters: dict[str, Any] | None = None) -> Any:
        """Run one of the Loriini add-on's own commands."""
        return self._addon(LORIINI_NAMESPACE, command, parameters)
