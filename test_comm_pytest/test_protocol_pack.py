"""Pack/unpack tests for radar-related protocol messages."""

import ctypes
import struct

import numpy as np
import pytest

from driver.referee.serial_protocol import (
    MsgID,
    OBJECT_ID,
    Radar2ClientMessage,
    Radar2SentryMessage,
    RadarDecisionMessage,
    RadarInfoMessage,
    RadarMarkMessage,
    RobotStatusMessage,
    Sentry2RadarMessage,
    SubCmdID,
)
from test_comm.helpers import FRAME_HEADER_SIZE, parse_frame


def test_radar2client_payload_size():
    assert ctypes.sizeof(Radar2ClientMessage.STRUCT_CLASS) == 48


def test_radar2sentry_payload_size():
    assert ctypes.sizeof(Radar2SentryMessage.STRUCT_CLASS) == 43


def test_radar2client_pack_frame():
    msg = Radar2ClientMessage(
        opponent_hero_x=100,
        opponent_hero_y=200,
        ally_sentry_x=300,
        ally_sentry_y=400,
    )
    frame = msg.pack()
    cmd_id, payload = parse_frame(frame)
    assert cmd_id == MsgID.CLIENT_RADAR_DATA.value
    assert len(payload) == 48
    assert struct.unpack("<H", payload[0:2])[0] == 100
    assert struct.unpack("<H", payload[2:4])[0] == 200


def test_radar2sentry_interactive_ids():
    msg = Radar2SentryMessage(
        is_blue=True,
        hero_x=1.5,
        hero_y=2.5,
        engineer_x=3.0,
        engineer_y=4.0,
        standard_3_x=5.0,
        standard_3_y=6.0,
        standard_4_x=7.0,
        standard_4_y=8.0,
        sentry_x=9.0,
        sentry_y=10.0,
        suggested_target=1,
        flags=2,
    )
    frame = msg.pack()
    cmd_id, payload = parse_frame(frame)
    assert cmd_id == MsgID.INTERACTIVE_DATA.value
    sub_cmd, sender, receiver = struct.unpack("<HHH", payload[:6])
    assert sub_cmd == SubCmdID.RADAR_2_SENTRY.value
    assert sender == OBJECT_ID.B_RADAR.value
    assert receiver == OBJECT_ID.B_SENTRY.value
    assert len(payload) == 6 + 43


def test_radar_decision_to_server():
    msg = RadarDecisionMessage(is_blue=False, radar_cmd=1)
    frame = msg.pack()
    cmd_id, payload = parse_frame(frame)
    assert cmd_id == MsgID.INTERACTIVE_DATA.value
    sub_cmd, sender, receiver = struct.unpack("<HHH", payload[:6])
    assert sub_cmd == SubCmdID.RADAR_DECISION.value
    assert sender == OBJECT_ID.R_RADAR.value
    assert receiver == OBJECT_ID.SERVER.value
    assert payload[6] == 1


def test_robot_status_roundtrip():
    original = RobotStatusMessage(
        robot_id=OBJECT_ID.R_RADAR.value,
        robot_level=1,
        current_hp=100,
        max_hp=200,
        shooter_barrel_cooling_value=10,
        shooter_barrel_heat_limit=20,
        chassis_power_limit=30,
        power_management_gimbal_output=1,
        power_management_chassis_output=1,
        power_management_shooter_output=0,
        reserve=0,
    )
    frame = original.pack()
    cmd_id, payload = parse_frame(frame)
    assert cmd_id == MsgID.ROBOT_DATA.value
    decoded = RobotStatusMessage.from_bytes(payload)
    assert decoded.robot_id == OBJECT_ID.R_RADAR.value


def test_sentry2radar_from_bytes_subcmd_0222():
    """RX path uses sub_cmd 0x0222; payload layout must match Sentry2RadarData."""
    body = Sentry2RadarMessage.STRUCT_CLASS(
        hero_x=1.0,
        hero_y=2.0,
        engineer_x=3.0,
        engineer_y=4.0,
        standard_3_x=5.0,
        standard_3_y=6.0,
        standard_4_x=7.0,
        standard_4_y=8.0,
        sentry_x=9.0,
        sentry_y=10.0,
        flag=1,
    )
    wire = struct.pack(
        "<HHH",
        SubCmdID.SENTRY_2_RADAR.value,
        OBJECT_ID.R_SENTRY.value,
        OBJECT_ID.R_RADAR.value,
    ) + bytes(body)
    msg = Sentry2RadarMessage.from_bytes(wire)
    assert msg.hero_x == pytest.approx(1.0)
    assert msg.flag == 1


def test_radar_mark_and_info_sizes():
    assert ctypes.sizeof(RadarMarkMessage.STRUCT_CLASS) == 2
    assert ctypes.sizeof(RadarInfoMessage.STRUCT_CLASS) == 1


def test_generic_message_sof():
    from driver.referee.serial_protocol import RefereeGenericMessage

    msg = RefereeGenericMessage(np.uint16(MsgID.GAME_STATUS.value), np.uint8(1))
    frame = msg.pack()
    assert frame[0] == RefereeGenericMessage.SOF
    assert len(frame) >= FRAME_HEADER_SIZE + 2 + 2
