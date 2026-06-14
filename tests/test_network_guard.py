from __future__ import annotations

import socket

import pytest

from tests.support import network_guard


def test_tcp_connect_is_blocked() -> None:
    with (
        pytest.raises(RuntimeError, match="Network access is blocked during tests"),
        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock,
    ):
        sock.connect(("127.0.0.1", 9))


def test_install_network_guard_is_idempotent() -> None:
    network_guard.install_network_guard()
    network_guard.install_network_guard()
