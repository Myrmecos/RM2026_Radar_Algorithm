"""Shared helpers for parsing and building referee serial frames."""

import struct
from typing import Optional, Tuple

from driver.referee.crc import Crc
from driver.referee.serial_protocol import RefereeGenericMessage

FRAME_HEADER_SIZE = 5
START_BYTE = 0xA5


def parse_frame(frame: bytes) -> Tuple[int, bytes]:
    """Parse a complete frame; return (cmd_id, payload without cmd_id)."""
    if len(frame) < FRAME_HEADER_SIZE + 4:
        raise ValueError(f"frame too short: {len(frame)} bytes")
    if frame[0] != START_BYTE:
        raise ValueError(f"bad SOF: 0x{frame[0]:02x}")

    data_length = struct.unpack("<H", frame[1:3])[0]
    header_for_crc = frame[:4]
    if frame[4] != Crc.get_crc8_check_sum(header_for_crc):
        raise ValueError("header CRC8 mismatch")

    body_end = FRAME_HEADER_SIZE + data_length + 2
    if len(frame) < body_end + 2:
        raise ValueError("frame truncated")

    message_without_tail = frame[:body_end]
    crc16_received = struct.unpack("<H", frame[body_end : body_end + 2])[0]
    if crc16_received != Crc.get_crc16_check_sum(message_without_tail):
        raise ValueError("frame CRC16 mismatch")

    cmd_id = struct.unpack("<H", frame[FRAME_HEADER_SIZE : FRAME_HEADER_SIZE + 2])[0]
    payload = frame[FRAME_HEADER_SIZE + 2 : body_end]
    return cmd_id, payload


def inject_frame(manager, frame: bytes) -> Optional[int]:
    """
    Push raw bytes into RefereeSerialManager RX buffer and run one frame parse.
    Returns cmd_id if a complete frame was decoded and callbacks ran.
    """
    from driver.referee.serial_comm import PackageStatus

    manager.rx_buffer.enqueue_rear(frame)
    status = manager.update_and_get_next_frame()
    if status != PackageStatus.PACKAGE_COMPLETE:
        return None
    data_length = struct.unpack("<H", manager.rx_frame_buffer[1:3])[0]
    cmd_id, _ = manager._get_cmd_id_and_data_from_buffer(data_length)
    key_id = f"0x{cmd_id:04x}"
    if key_id in manager.cb_funcs:
        for cb in manager.cb_funcs[key_id]:
            cb(cmd_id, manager.rx_frame_buffer[
                FRAME_HEADER_SIZE + 2 : FRAME_HEADER_SIZE + data_length + 2
            ])
    return cmd_id


def build_interactive_payload(sub_cmd_id: int, sender_id: int, receiver_id: int, body: bytes) -> bytes:
    return struct.pack("<HHH", sub_cmd_id, sender_id, receiver_id) + body
