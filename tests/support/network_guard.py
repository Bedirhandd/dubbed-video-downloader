"""Block network access during the unittest suite unless explicitly opted out."""

from __future__ import annotations

import os
import socket
from collections.abc import Callable
from typing import Any

_GUARD_INSTALLED = False
_ORIGINAL_CONNECT: Callable[..., object] | None = None
_ORIGINAL_CONNECT_EX: Callable[..., object] | None = None
_ORIGINAL_CREATE_CONNECTION: Callable[..., object] | None = None

_NETWORK_BLOCKED_MESSAGE = (
    "Network access is blocked during tests. "
    "Set DBDVDL_TESTS_ALLOW_NETWORK=1 to opt out for local debugging."
)


def _network_allowed() -> bool:
    return os.environ.get("DBDVDL_TESTS_ALLOW_NETWORK", "").strip() in {
        "1",
        "true",
        "True",
        "yes",
        "YES",
    }


def _is_unix_socket_address(address: object) -> bool:
    if not isinstance(address, tuple) or not address:
        return False
    family = address[0]
    return family == socket.AF_UNIX


def _blocked_connect(
    self: socket.socket, address: object, *args: Any, **kwargs: Any
) -> object:
    if _network_allowed() or _is_unix_socket_address(address):
        assert _ORIGINAL_CONNECT is not None
        return _ORIGINAL_CONNECT(self, address, *args, **kwargs)
    raise RuntimeError(_NETWORK_BLOCKED_MESSAGE)


def _blocked_connect_ex(
    self: socket.socket, address: object, *args: Any, **kwargs: Any
) -> object:
    if _network_allowed() or _is_unix_socket_address(address):
        assert _ORIGINAL_CONNECT_EX is not None
        return _ORIGINAL_CONNECT_EX(self, address, *args, **kwargs)
    raise RuntimeError(_NETWORK_BLOCKED_MESSAGE)


def _blocked_create_connection(address: object, *args: Any, **kwargs: Any) -> object:
    if _network_allowed() or _is_unix_socket_address(address):
        assert _ORIGINAL_CREATE_CONNECTION is not None
        return _ORIGINAL_CREATE_CONNECTION(address, *args, **kwargs)
    raise RuntimeError(_NETWORK_BLOCKED_MESSAGE)


def install_network_guard() -> None:
    global \
        _GUARD_INSTALLED, \
        _ORIGINAL_CONNECT, \
        _ORIGINAL_CONNECT_EX, \
        _ORIGINAL_CREATE_CONNECTION

    if _GUARD_INSTALLED:
        return

    _ORIGINAL_CONNECT = socket.socket.connect
    _ORIGINAL_CONNECT_EX = socket.socket.connect_ex
    _ORIGINAL_CREATE_CONNECTION = socket.create_connection

    socket.socket.connect = _blocked_connect  # type: ignore[method-assign]
    socket.socket.connect_ex = _blocked_connect_ex  # type: ignore[method-assign]
    socket.create_connection = _blocked_create_connection  # type: ignore[assignment]

    _GUARD_INSTALLED = True
