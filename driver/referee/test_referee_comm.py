from .serial_comm import RefereeSerialManager
from .serial_protocol import Sentry2RadarMessage, RobotStatusMessage
from .serial_protocol import Radar2SentryMessage
from .serial_protocol import MsgID, SubCmdID


def status_message_decode_func(cmd_id, data):

    if cmd_id == MsgID.ROBOT_DATA.value:
        message = RobotStatusMessage.from_bytes(data)
        print(f"[STATUS] Robot Status: {message}")


def sentry2radar_message_decode_func(cmd_id, data):
    if cmd_id == MsgID.INTERACTIVE_DATA.value:
        message = Sentry2RadarMessage.from_bytes(data)
        print(f"[SENTRY2RADAR] Sentry to Radar Message: {message}")


if __name__ == "__main__":
    import rclpy
    rclpy.init()
    serial_manager = RefereeSerialManager(port="/dev/ttyV0", baudrate=115200)
    serial_manager.bind(MsgID.ROBOT_DATA.value, status_message_decode_func)
    serial_manager.bind(MsgID.INTERACTIVE_DATA.value, sentry2radar_message_decode_func)
    serial_manager.start()
    import time

    while True:
        # serial_manager.summarize()
        sentry_msg = Radar2SentryMessage(
            is_blue=True,
            hero_x=1.0,
            hero_y=2.0,
            engineer_x=3.0,
            engineer_y=4.0,
            standard_3_x=5.0,
            standard_3_y=6.0,
            standard_4_x=7.0,
            standard_4_y=8.0,
            sentry_x=9.0,
            sentry_y=10.0,  # 40
            suggested_target=1,
            flags=2,
        )
        serial_manager.summarize()
        # # print len of the packed message
        # print(f"Sending Sentry2RadarMessage: {sentry_msg}")
        # print(f"Length of packed message: {len(sentry_msg.pack())}")
        # print(sentry_msg.pack().hex())
        data_to_send = sentry_msg.pack()
        print("Sending data: ", data_to_send.hex())
        print("len of data to send: ", len(data_to_send))
        serial_manager.tx(data_to_send)
        time.sleep(1)

        # # compose some data to send
        # all bytes should be 42
        data = bytearray(58)
        for i in range(58):
            data[i] = 0x42
        data[0] = 0xA5  # header
        data[5] = 0x00
        # pack the message "data" and send it
        print(f"Sending fake data: {data.hex()}")
        print("len of fake data: ", len(data))
        data = bytes(data)  # convert to bytes
        serial_manager.tx(data)
        time.sleep(1)