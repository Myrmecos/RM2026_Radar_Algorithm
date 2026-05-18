"""Receive-path tests: frame sync, CRC rejection, callback dispatch."""

import struct

import pytest

from driver.referee.serial_comm import PackageStatus, RefereeSerialManager
from driver.referee.serial_protocol import MsgID, Radar2ClientMessage
from test_comm.helpers import inject_frame


@pytest.fixture
def rx_manager():
    mgr = RefereeSerialManager(port="/dev/null", baudrate=115200, auto_scan=False)
    mgr.state = mgr.state.__class__.OPENNED
    return mgr


def test_rx_complete_frame(rx_manager):
    frame = Radar2ClientMessage(opponent_hero_x=42, opponent_hero_y=84).pack()
    received = []

    def _cb(cmd_id, data):
        received.append((cmd_id, data))

    rx_manager.bind(MsgID.CLIENT_RADAR_DATA.value, _cb)
    cmd_id = inject_frame(rx_manager, frame)
    assert cmd_id == MsgID.CLIENT_RADAR_DATA.value
    assert len(received) == 1
    assert received[0][0] == MsgID.CLIENT_RADAR_DATA.value
    assert len(received[0][1]) == 48


def test_rx_rejects_bad_crc16(rx_manager):
    frame = bytearray(Radar2ClientMessage().pack())
    frame[-1] ^= 0xFF
    rx_manager.rx_buffer.enqueue_rear(bytes(frame))
    status = rx_manager.update_and_get_next_frame()
    assert status == PackageStatus.CRC_ERROR


def test_rx_rejects_bad_header_crc8(rx_manager):
    frame = bytearray(Radar2ClientMessage().pack())
    frame[4] ^= 0xFF
    rx_manager.rx_buffer.enqueue_rear(bytes(frame))
    status = rx_manager.update_and_get_next_frame()
    assert status == PackageStatus.HEADER_CRC_ERROR


def test_rx_strips_leading_garbage(rx_manager):
    frame = Radar2ClientMessage(opponent_hero_x=7).pack()
    rx_manager.rx_buffer.enqueue_rear(b"\x00\x00\xff" + frame)
    status = rx_manager.update_and_get_next_frame()
    assert status == PackageStatus.PACKAGE_COMPLETE
    data_length = struct.unpack("<H", rx_manager.rx_frame_buffer[1:3])[0]
    cmd_id, data = rx_manager._get_cmd_id_and_data_from_buffer(data_length)
    assert cmd_id == MsgID.CLIENT_RADAR_DATA.value
    assert struct.unpack("<H", data[0:2])[0] == 7
