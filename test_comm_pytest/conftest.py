"""Pytest fixtures: mock rclpy/serial so tests run without ROS or hardware."""

import logging
import sys
from unittest.mock import MagicMock

import pytest


class _FakeLogger:
    def info(self, msg, *args, **kwargs):
        logging.getLogger("test_comm").info(msg)

    def warning(self, msg, *args, **kwargs):
        logging.getLogger("test_comm").warning(msg)

    def error(self, msg, *args, **kwargs):
        logging.getLogger("test_comm").error(msg)


class _FakeNode:
    def __init__(self, name=None):
        self.name = name

    def get_logger(self):
        return _FakeLogger()


def _install_mocks():
    if "rclpy" not in sys.modules:
        import types

        rclpy_mod = types.ModuleType("rclpy")
        node_mod = types.ModuleType("rclpy.node")
        node_mod.Node = _FakeNode
        rclpy_mod.node = node_mod
        sys.modules["rclpy"] = rclpy_mod
        sys.modules["rclpy.node"] = node_mod

    if "serial" not in sys.modules:
        import types

        serial_mod = types.ModuleType("serial")
        serial_mod.SerialException = OSError
        serial_mod.Serial = MagicMock()

        tools_mod = types.ModuleType("serial.tools")
        list_ports_mod = types.ModuleType("serial.tools.list_ports")
        list_ports_mod.comports = lambda: []
        tools_mod.list_ports = list_ports_mod
        serial_mod.tools = tools_mod

        sys.modules["serial"] = serial_mod
        sys.modules["serial.tools"] = tools_mod
        sys.modules["serial.tools.list_ports"] = list_ports_mod


_install_mocks()


@pytest.fixture
def project_root():
    import os

    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
