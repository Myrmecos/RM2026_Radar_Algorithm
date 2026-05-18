# -*- coding: utf-8 -*-
"""Build referee-side frames for integration simulation (no pytest)."""

import ctypes

import numpy as np

from driver.referee.serial_protocol import (
    DartStatusMessage,
    InteractiveMessage,
    MsgID,
    OBJECT_ID,
    RadarInfoMessage,
    RadarMarkMessage,
    RobotStatusMessage,
    Sentry2RadarData,
    SubCmdID,
)


def pack_sentry2radar(
    is_blue: bool = False,
    flag: int = 1,
    hero_x: float = 12.0,
    hero_y: float = 34.0,
    **kwargs,
) -> bytes:
    """Pack 0x0301 interactive with sub_cmd 0x0222 (matches radar RX handler)."""
    body = Sentry2RadarData(
        hero_x=hero_x,
        hero_y=hero_y,
        engineer_x=kwargs.get("engineer_x", 0.0),
        engineer_y=kwargs.get("engineer_y", 0.0),
        standard_3_x=kwargs.get("standard_3_x", 0.0),
        standard_3_y=kwargs.get("standard_3_y", 0.0),
        standard_4_x=kwargs.get("standard_4_x", 0.0),
        standard_4_y=kwargs.get("standard_4_y", 0.0),
        sentry_x=kwargs.get("sentry_x", 0.0),
        sentry_y=kwargs.get("sentry_y", 0.0),
        flag=flag,
    )
    sender = OBJECT_ID.B_SENTRY.value if is_blue else OBJECT_ID.R_SENTRY.value
    receiver = OBJECT_ID.B_RADAR.value if is_blue else OBJECT_ID.R_RADAR.value
    msg = InteractiveMessage(
        np.uint16(SubCmdID.SENTRY_2_RADAR.value),
        np.uint16(sender),
        np.uint16(receiver),
        bytes(body),
    )
    return msg.pack()


def pack_robot_status_red_radar() -> bytes:
    return RobotStatusMessage(
        robot_id=OBJECT_ID.R_RADAR.value,
        robot_level=1,
        current_hp=200,
        max_hp=200,
        shooter_barrel_cooling_value=0,
        shooter_barrel_heat_limit=0,
        chassis_power_limit=0,
        power_management_gimbal_output=0,
        power_management_chassis_output=0,
        power_management_shooter_output=0,
        reserve=0,
    ).pack()


def pack_dart_status(selected_target: int = 0, remaining_time: int = 60) -> bytes:
    return DartStatusMessage(
        dart_remaining_time=remaining_time,
        recent_hit_target=0,
        accumulated_hit_count=0,
        selected_target=selected_target,
        reserve=0,
    ).pack()


def pack_radar_mark_progress(enemy_hero: int = 1) -> bytes:
    return RadarMarkMessage(
        enemy_hero=enemy_hero,
        enemy_engineer=0,
        enemy_standard_3=0,
        enemy_standard_4=0,
        enemy_aerial=0,
        enemy_sentry=0,
        ally_hero=0,
        ally_engineer=0,
        ally_standard_3=0,
        ally_standard_4=0,
        ally_aerial=0,
        ally_sentry=0,
        reserve=0,
    ).pack()


def pack_radar_info(
    double_vulnerability_count: int = 2,
    is_double_vulnerability: int = 0,
) -> bytes:
    return RadarInfoMessage(
        double_vulnerability_count=double_vulnerability_count,
        is_double_vulnerability=is_double_vulnerability,
        encrypted_level=1,
        can_modify_passwd=0,
        reserve=0,
    ).pack()
