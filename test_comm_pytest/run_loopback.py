#!/usr/bin/env python3
"""
Hardware loopback test for referee serial communication.

Setup (two virtual ports):
  sudo socat -d -d pty,raw,echo=0,mode=666 pty,raw,echo=0,mode=666

Usage:
  python test_comm/run_loopback.py --tx /dev/pts/3 --rx /dev/pts/4
"""

import argparse
import struct
import sys
import time

# Ensure repo root on path
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from driver.referee.serial_comm import RefereeSerialManager
from driver.referee.serial_protocol import (
    MsgID,
    Radar2ClientMessage,
    Radar2SentryMessage,
)
from test_comm.helpers import parse_frame


def main():
    parser = argparse.ArgumentParser(description="Referee serial loopback test")
    parser.add_argument("--tx", required=True, help="TX serial port (e.g. /dev/pts/3)")
    parser.add_argument("--rx", required=True, help="RX serial port (e.g. /dev/pts/4)")
    parser.add_argument("--baudrate", type=int, default=115200)
    args = parser.parse_args()

    received = []

    def on_rx(cmd_id, data):
        received.append((cmd_id, data))
        print(f"[RX] cmd_id=0x{cmd_id:04x} len={len(data)} hex={data[:16].hex()}...")

    rx_mgr = RefereeSerialManager(port=args.rx, baudrate=args.baudrate, auto_scan=False)
    tx_mgr = RefereeSerialManager(port=args.tx, baudrate=args.baudrate, auto_scan=False)
    rx_mgr.bind(MsgID.CLIENT_RADAR_DATA.value, on_rx)
    rx_mgr.bind(MsgID.INTERACTIVE_DATA.value, on_rx)

    if not rx_mgr.start():
        print("Failed to start RX manager", file=sys.stderr)
        return 1
    time.sleep(0.3)
    if not tx_mgr.start():
        print("Failed to start TX manager", file=sys.stderr)
        rx_mgr.close()
        return 1
    time.sleep(0.3)

    cases = [
        ("Radar2Client", Radar2ClientMessage(opponent_hero_x=111, opponent_hero_y=222).pack()),
        (
            "Radar2Sentry",
            Radar2SentryMessage(
                is_blue=False,
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
            ).pack(),
        ),
    ]

    ok = True
    for name, frame in cases:
        received.clear()
        print(f"\n[TX] {name} ({len(frame)} bytes)")
        if not tx_mgr.tx(frame):
            print(f"  TX failed for {name}")
            ok = False
            continue
        time.sleep(0.2)
        if not received:
            print(f"  No RX for {name}")
            ok = False
            continue
        rx_cmd, rx_data = received[-1]
        tx_cmd, _ = parse_frame(frame)
        if rx_cmd != tx_cmd:
            print(f"  cmd_id mismatch: tx=0x{tx_cmd:04x} rx=0x{rx_cmd:04x}")
            ok = False
        else:
            print(f"  OK cmd_id=0x{rx_cmd:04x}")

    tx_mgr.summarize()
    rx_mgr.summarize()
    tx_mgr.close()
    rx_mgr.close()
    print("\nLoopback:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
