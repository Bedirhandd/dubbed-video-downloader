from __future__ import annotations

import socket
import unittest

from tests.support import network_guard


class NetworkGuardTests(unittest.TestCase):
    def test_tcp_connect_is_blocked(self) -> None:
        with (
            self.assertRaises(RuntimeError) as context,
            socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock,
        ):
            sock.connect(("127.0.0.1", 9))

        self.assertIn("Network access is blocked during tests", str(context.exception))

    def test_install_network_guard_is_idempotent(self) -> None:
        network_guard.install_network_guard()
        network_guard.install_network_guard()


if __name__ == "__main__":
    unittest.main()
