#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-end serial simulation: radar station (RefereeCommManager) <-> mock referee.

Virtual ports (from repo ReadMe):
  sudo socat -d -d PTY,link=/dev/ttyV0,raw,echo=0 PTY,link=/dev/ttyV1,raw,echo=0

Run both ends in one terminal:
  python test_comm/sim_radar_referee.py

Or split across two terminals:
  python test_comm/sim_radar_referee.py --mode radar   --port /dev/ttyV0
  python test_comm/sim_radar_referee.py --mode referee --port /dev/ttyV1

Requires: rclpy, pyserial, numpy (same as main.py).
"""

from __future__ import annotations

import argparse
import math
import os
import struct
import sys
import threading
import time

# Repo root on path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import rclpy

from driver.referee.referee_comm import FACTION, RefereeCommManager
from driver.referee.serial_comm import RefereeSerialManager
from driver.referee.serial_protocol import (
    MsgID,
    Radar2ClientMessage,
    Radar2SentryMessage,
    SubCmdID,
)
from test_comm.helpers import parse_frame
from test_comm.mock_referee_frames import (
    pack_dart_status,
    pack_radar_info,
    pack_radar_mark_progress,
    pack_robot_status_red_radar,
    pack_sentry2radar,
)


def _cmd_name(cmd_id: int) -> str:
    try:
        return MsgID(cmd_id).name
    except ValueError:
        return f"UNKNOWN_0x{cmd_id:04x}"


def _describe_radar_tx(cmd_id: int, payload: bytes) -> str:
    if cmd_id == MsgID.CLIENT_RADAR_DATA.value and len(payload) >= 4:
        ox, oy = struct.unpack("<HH", payload[0:4])
        return f"opponent_hero=({ox}, {oy}) cm"
    if cmd_id == MsgID.INTERACTIVE_DATA.value and len(payload) >= 6:
        sub_cmd, sender, receiver = struct.unpack("<HHH", payload[:6])
        sub_name = f"0x{sub_cmd:04x}"
        try:
            sub_name = SubCmdID(sub_cmd).name
        except ValueError:
            pass
        extra = f"payload_len={len(payload) - 6}"
        if sub_cmd == SubCmdID.RADAR_2_SENTRY.value and len(payload) >= 14:
            hx, hy = struct.unpack("<ff", payload[6:14])
            extra = f"enemy_hero=({hx:.2f}, {hy:.2f}) m"
        elif sub_cmd == SubCmdID.RADAR_DECISION.value and len(payload) >= 7:
            extra = f"radar_cmd={payload[6]}"
        return f"sub={sub_name} sender=0x{sender:04x} receiver=0x{receiver:04x} {extra}"
    return f"len={len(payload)} hex={payload[:24].hex()}"


class MockRefereeSimulator:
    """Simulates referee system TX/RX on the far end of the serial link."""

    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self._stop = threading.Event()
        self._mgr = RefereeSerialManager(
            port=port, baudrate=baudrate, auto_scan=False
        )
        self._mgr.bind(MsgID.CLIENT_RADAR_DATA.value, self._on_radar_frame)
        self._mgr.bind(MsgID.INTERACTIVE_DATA.value, self._on_radar_frame)
        self._tick = 0

    def _on_radar_frame(self, cmd_id: int, data: bytes) -> None:
        # Reconstruct full frame hex from logged path is not available; print parsed summary
        print(
            f"[MockReferee RX] cmd={_cmd_name(cmd_id)} (0x{cmd_id:04x}) "
            f"{_describe_radar_tx(cmd_id, data)}"
        )

    def start(self) -> bool:
        if not self._mgr.start():
            print("[MockReferee] Failed to start serial manager")
            return False
        self._feed_thread = threading.Thread(target=self._feed_loop, daemon=True)
        self._feed_thread.start()
        print(f"[MockReferee] Listening on {self.port} @ {self.baudrate}")
        return True

    def _feed_loop(self) -> None:
        """Periodically inject messages a real referee would send to radar."""
        while not self._stop.is_set():
            self._tick += 1
            t = self._tick

            # ~1 Hz: robot status (faction), mark progress, radar info
            if t % 10 == 1:
                self._send("ROBOT_DATA", pack_robot_status_red_radar())
            if t % 10 == 3:
                self._send("RADAR_MARK_PROGRESS", pack_radar_mark_progress())
            if t % 10 == 5:
                self._send("RADAR_DECISION_SYNC", pack_radar_info())

            # ~1 Hz: dart status; cycle selected_target for double-vuln logic
            if t % 10 == 7:
                target = [0, 1, 2, 3][(t // 10) % 4]
                self._send("LAUNCHER_DATA", pack_dart_status(selected_target=target))

            # ~1 Hz: sentry -> radar link
            if t % 10 == 9:
                self._send(
                    "SENTRY_2_RADAR",
                    pack_sentry2radar(
                        is_blue=False,
                        flag=1,
                        hero_x=10.0 + 0.1 * t,
                        hero_y=20.0,
                    ),
                )

            time.sleep(0.1)

    def _send(self, label: str, frame: bytes) -> None:
        if self._mgr.tx(frame):
            cmd_id, _ = parse_frame(frame)
            print(f"[MockReferee TX] {label} cmd={_cmd_name(cmd_id)} ({len(frame)}B)")
        else:
            print(f"[MockReferee TX] {label} FAILED (port not open?)")

    def stop(self) -> None:
        self._stop.set()
        self._mgr.close()


class RadarStationSimulator:
    """
    Runs RefereeCommManager like main.py + simplified main_event_loop feed.
    """

    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self._stop = threading.Event()
        RefereeCommManager._instance = None
        self._referee = RefereeCommManager(port=port, baudrate=baudrate)
        # Disable USB auto-scan for fixed virtual port
        self._referee.auto_scan = False
        self._referee.initial_port = port

    def start(self) -> bool:
        if not self._referee.start():
            print("[Radar] Failed to start RefereeCommManager")
            return False
        self._feed_thread = threading.Thread(target=self._feed_loop, daemon=True)
        self._status_thread = threading.Thread(target=self._status_loop, daemon=True)
        self._feed_thread.start()
        self._status_thread.start()
        print(f"[Radar] RefereeCommManager on {self.port} (daemon TX active)")
        return True

    def _feed_loop(self) -> None:
        """Mimic main_event_loop: refresh outbound messages each tick."""
        phase = 0.0
        while not self._stop.is_set():
            phase += 0.15
            # Fake detected positions (cm), blue team as opponent indices 0-4
            base_x = int(800 + 50 * math.sin(phase))
            base_y = int(1200 + 50 * math.cos(phase))

            self._referee.radar2client_msg = Radar2ClientMessage(
                opponent_hero_x=base_x,
                opponent_hero_y=base_y,
                opponent_engineer_x=base_x + 100,
                opponent_engineer_y=base_y + 50,
                opponent_infantry_3_x=0,
                opponent_infantry_3_y=0,
                opponent_infantry_4_x=0,
                opponent_infantry_4_y=0,
                opponent_sentry_x=0,
                opponent_sentry_y=0,
                ally_hero_x=2000,
                ally_hero_y=1500,
            )

            self._referee.radar2sentry_msg = Radar2SentryMessage(
                is_blue=False,
                hero_x=base_x / 100.0,
                hero_y=base_y / 100.0,
                engineer_x=(base_x + 100) / 100.0,
                engineer_y=(base_y + 50) / 100.0,
                standard_3_x=-8888,
                standard_3_y=-8888,
                standard_4_x=-8888,
                standard_4_y=-8888,
                sentry_x=-8888,
                sentry_y=-8888,
                suggested_target=0,
                flags=0,
            )

            time.sleep(0.05)

    def _status_loop(self) -> None:
        while not self._stop.is_set():
            r = self._referee
            faction = r.get_faction().name
            print(
                f"[Radar状态] 阵营={faction} | 裁判串口={'已连接' if r.is_connected() else '未连接'} "
                f"| 哨兵={'在线' if r.is_sentry_connected else '离线'} "
                f"| sentry_flag={r.sentry_received_flag} "
                f"| 飞镖目标={r.target} | 双易伤次数={r.double_vulnerability_count} "
                f"| 双易伤生效={r.is_double_vulnerability} | 请求计数={r.request_count}"
            )
            if r.sentry2radar_msg.hero_x > -1000:
                print(
                    f"           哨兵回传 hero=({r.sentry2radar_msg.hero_x:.1f}, "
                    f"{r.sentry2radar_msg.hero_y:.1f}) m"
                )
            time.sleep(2.0)

    def stop(self) -> None:
        self._stop.set()
        self._referee.close()


def run_both(radar_port: str, referee_port: str, baudrate: int) -> int:
    rclpy.init()
    radar = RadarStationSimulator(radar_port, baudrate)
    referee = MockRefereeSimulator(referee_port, baudrate)

    if not referee.start():
        rclpy.shutdown()
        return 1
    time.sleep(0.5)
    if not radar.start():
        referee.stop()
        rclpy.shutdown()
        return 1

    print(
        "\n=== Simulation running (Ctrl+C to stop) ===\n"
        f"  Radar   -> {radar_port}\n"
        f"  Referee -> {referee_port}\n"
    )
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        radar.stop()
        referee.stop()
        rclpy.shutdown()
    return 0


def run_radar_only(port: str, baudrate: int) -> int:
    rclpy.init()
    radar = RadarStationSimulator(port, baudrate)
    if not radar.start():
        rclpy.shutdown()
        return 1
    print(f"[Radar] Only mode on {port}. Pair with: --mode referee on the other PTY.")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        radar.stop()
        rclpy.shutdown()
    return 0


def run_referee_only(port: str, baudrate: int) -> int:
    rclpy.init()
    referee = MockRefereeSimulator(port, baudrate)
    if not referee.start():
        rclpy.shutdown()
        return 1
    print(f"[MockReferee] Only mode on {port}. Pair with: --mode radar on the other PTY.")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        referee.stop()
        rclpy.shutdown()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Radar RefereeCommManager <-> mock referee serial simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create virtual ports first:
  sudo socat -d -d PTY,link=/dev/ttyV0,raw,echo=0 PTY,link=/dev/ttyV1,raw,echo=0

  python test_comm/sim_radar_referee.py
  python test_comm/sim_radar_referee.py --mode radar --port /dev/ttyV0
  python test_comm/sim_radar_referee.py --mode referee --port /dev/ttyV1
        """,
    )
    parser.add_argument(
        "--mode",
        choices=("both", "radar", "referee"),
        default="both",
        help="Run radar side, mock referee side, or both (default: both)",
    )
    parser.add_argument(
        "--radar-port",
        default="/dev/ttyV0",
        help="Serial port for RefereeCommManager (default: /dev/ttyV0)",
    )
    parser.add_argument(
        "--referee-port",
        default="/dev/ttyV1",
        help="Serial port for mock referee (default: /dev/ttyV1)",
    )
    parser.add_argument("--baudrate", type=int, default=115200)
    args = parser.parse_args()

    if args.mode == "both":
        return run_both(args.radar_port, args.referee_port, args.baudrate)
    if args.mode == "radar":
        return run_radar_only(args.radar_port, args.baudrate)
    return run_referee_only(args.referee_port, args.baudrate)


if __name__ == "__main__":
    sys.exit(main())
