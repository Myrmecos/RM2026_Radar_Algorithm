"""RefereeCommManager decode and TX scheduling logic (no real serial)."""

import struct
import threading
import time

import pytest

from driver.referee.referee_comm import FACTION, RadarTriggerState, RefereeCommManager
from driver.referee.serial_protocol import (
    MsgID,
    OBJECT_ID,
    Radar2ClientMessage,
    RadarInfoMessage,
    RadarMarkMessage,
    RobotStatusMessage,
    SubCmdID,
)
from test_comm.helpers import build_interactive_payload


@pytest.fixture
def comm():
    RefereeCommManager._instance = None
    mgr = RefereeCommManager(port="/dev/null", baudrate=115200)
    mgr.state = mgr.state.__class__.OPENNED
    return mgr


def test_faction_from_robot_status(comm):
    red = RobotStatusMessage(robot_id=OBJECT_ID.R_RADAR.value).pack()
    _, payload = _payload_from_frame(red)
    comm.status_message_decode_func(MsgID.ROBOT_DATA.value, payload)
    assert comm.faction == FACTION.RED

    blue = RobotStatusMessage(robot_id=OBJECT_ID.B_RADAR.value).pack()
    _, payload = _payload_from_frame(blue)
    comm.status_message_decode_func(MsgID.ROBOT_DATA.value, payload)
    assert comm.faction == FACTION.BLUE


def test_sentry2radar_updates_link(comm):
    from driver.referee.serial_protocol import Sentry2RadarData

    body = bytes(
        Sentry2RadarData(
            hero_x=1.0,
            hero_y=2.0,
            engineer_x=0,
            engineer_y=0,
            standard_3_x=0,
            standard_3_y=0,
            standard_4_x=0,
            standard_4_y=0,
            sentry_x=0,
            sentry_y=0,
            flag=1,
        )
    )
    wire = build_interactive_payload(
        SubCmdID.SENTRY_2_RADAR.value,
        OBJECT_ID.B_SENTRY.value,
        OBJECT_ID.B_RADAR.value,
        body,
    )
    comm.interactive_message_decode_func(MsgID.INTERACTIVE_DATA.value, wire)
    assert comm.is_sentry_connected is True
    assert comm.sentry_received_flag is True
    assert comm.sentry2radar_msg.hero_x == pytest.approx(1.0)


def test_radar_info_decode(comm):
    frame = RadarInfoMessage(
        double_vulnerability_count=2,
        is_double_vulnerability=1,
    ).pack()
    _, payload = _payload_from_frame(frame)
    comm.radar_info_message_decode_func(MsgID.RADAR_DECISION_SYNC.value, payload)
    assert comm.double_vulnerability_count == 2
    assert comm.is_double_vulnerability == 1


def test_mark_progress_decode(comm):
    frame = RadarMarkMessage(enemy_hero=1, ally_sentry=1).pack()
    _, payload = _payload_from_frame(frame)
    comm.radar_mark_progress_message_decode_func(MsgID.RADAR_MARK_PROGRESS.value, payload)
    assert comm.radar_mark_progress_msg.enemy_hero == 1
    assert comm.radar_mark_progress_msg.ally_sentry == 1


def test_message_daemon_sends_client_pack(comm):
    sent = []

    def _tx(data: bytes):
        sent.append(data)
        return True

    comm.tx = _tx
    comm.message_daemon_stop_event = threading.Event()
    comm.radar2client_msg = Radar2ClientMessage(opponent_hero_x=123)
    thread = threading.Thread(target=comm.message_daemon, daemon=True)
    thread.start()
    time.sleep(0.45)
    comm.message_daemon_stop_event.set()
    thread.join(timeout=2.0)

    assert len(sent) >= 2
    from test_comm.helpers import parse_frame

    cmd_ids = [parse_frame(f)[0] for f in sent]
    assert MsgID.CLIENT_RADAR_DATA.value in cmd_ids


def _payload_from_frame(frame: bytes):
    from test_comm.helpers import parse_frame

    return parse_frame(frame)
