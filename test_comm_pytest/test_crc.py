"""CRC8/CRC16 tests (appendix-style verification)."""

from driver.referee.crc import Crc


def test_crc8_known_vector():
    header = bytes([0xA5, 0x0A, 0x00, 0x01])
    crc = Crc.get_crc8_check_sum(header)
    assert isinstance(crc, int)
    assert 0 <= crc <= 0xFF
    buf = bytearray(header) + bytearray([0])
    buf[4] = Crc.get_crc8_check_sum(buf[:4])
    assert Crc.verify_crc8_check_sum(buf)


def test_crc16_roundtrip():
    header = bytearray([0xA5, 0x04, 0x00, 0x01, 0x00])
    header[4] = Crc.get_crc8_check_sum(header[:4])
    frame = header + bytearray([0x01, 0x02, 0x03, 0x04, 0x00, 0x00])
    Crc.append_crc16_check_sum(frame)
    assert Crc.verify_crc16_check_sum(frame)
