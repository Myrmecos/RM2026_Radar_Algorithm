#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serial recorder with PTY-bridge mode.

This script can create a virtual PTY (slave) and bridge it to a real
serial device (default `/dev/ttyACM0`). Point your radar software at
the printed PTY path — the script will forward bytes both ways and
log every write to/reads from the real device into `test_comm/logs`.

Modes:
    - `pty` (default): create PTY and bridge to real device (transparent)
    - `tcp`: legacy TCP -> serial proxy (keeps previous behavior)

Usage example (PTY bridge, default):
    python test_comm/record.py --device /dev/ttyACM0 --baud 115200

Then point your radar to the printed virtual device, e.g.:
    /dev/pts/3

Requires: pyserial

python test_comm/record.py --device /dev/ttyACM0 --baud 115200
python test_comm/record.py --mode tcp --device /dev/ttyACM0 --port 4000
"""

from __future__ import annotations

import argparse
import os
import socket
import threading
import time
from datetime import datetime

import serial


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


class SerialRecorderTCP:
    """Legacy TCP -> serial recorder used when mode == 'tcp'."""
    def __init__(self, device: str, baud: int, listen_port: int, log_dir: str):
        self.device = device
        self.baud = baud
        self.listen_port = listen_port
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

        self.rx_path = os.path.join(self.log_dir, "rx.log")
        self.tx_path = os.path.join(self.log_dir, "tx.log")
        self.combined_path = os.path.join(self.log_dir, "combined.log")

        self._stop = threading.Event()
        self._client_connected = threading.Event()
        self._client_sock = None

        self.ser = None

    def open_serial(self) -> bool:
        try:
            self.ser = serial.Serial(self.device, self.baud, timeout=0.1)
            return True
        except Exception as e:
            print(f"Failed to open serial {self.device}: {e}")
            return False

    def start(self) -> None:
        if not self.open_serial():
            return

        self._server_thread = threading.Thread(target=self._serve_tcp, daemon=True)
        self._rx_thread = threading.Thread(target=self._serial_rx_loop, daemon=True)
        self._server_thread.start()
        self._rx_thread.start()
        print(f"Listening for TCP clients on 127.0.0.1:{self.listen_port} - serial {self.device} @ {self.baud}")

    def stop(self) -> None:
        self._stop.set()
        try:
            if self._client_sock:
                self._client_sock.close()
        except Exception:
            pass
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass

    def _serve_tcp(self) -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", self.listen_port))
        srv.listen(1)
        while not self._stop.is_set():
            try:
                srv.settimeout(1.0)
                client, addr = srv.accept()
            except Exception:
                continue
            print(f"Client connected from {addr}")
            self._client_sock = client
            self._client_connected.set()
            t = threading.Thread(target=self._client_to_serial_loop, args=(client,), daemon=True)
            t.start()
            # Wait until client disconnects
            while not self._stop.is_set() and self._client_connected.is_set():
                time.sleep(0.1)
            try:
                client.close()
            except Exception:
                pass
            self._client_sock = None
            print("Client disconnected")

    def _client_to_serial_loop(self, client_sock: socket.socket) -> None:
        try:
            while not self._stop.is_set():
                data = client_sock.recv(4096)
                if not data:
                    break
                # Write to serial
                try:
                    self.ser.write(data)
                except Exception as e:
                    print(f"Serial write error: {e}")
                    break
                self._log_tx(data)
        finally:
            self._client_connected.clear()

    def _serial_rx_loop(self) -> None:
        while not self._stop.is_set():
            try:
                data = self.ser.read(4096)
            except Exception as e:
                print(f"Serial read error: {e}")
                break
            if data:
                self._log_rx(data)
                # forward to client if connected
                if self._client_connected.is_set() and self._client_sock:
                    try:
                        self._client_sock.sendall(data)
                    except Exception:
                        # client likely disconnected
                        self._client_connected.clear()
            else:
                time.sleep(0.01)

    def _log_line(self, path: str, prefix: str, data: bytes) -> None:
        line = f"{now_ts()} {prefix} {len(data)}B {data.hex()}\n"
        try:
            with open(path, "a") as f:
                f.write(line)
            with open(self.combined_path, "a") as f:
                f.write(line)
        except Exception as e:
            print(f"Failed to write log {path}: {e}")

    def _log_rx(self, data: bytes) -> None:
        self._log_line(self.rx_path, "RX", data)

    def _log_tx(self, data: bytes) -> None:
        self._log_line(self.tx_path, "TX", data)


class PTYBridgeRecorder:
    """Create a PTY slave and bridge it to a real serial device while logging."""
    def __init__(self, device: str, baud: int, log_dir: str):
        self.device = device
        self.baud = baud
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

        self.rx_path = os.path.join(self.log_dir, "rx.log")
        self.tx_path = os.path.join(self.log_dir, "tx.log")
        self.combined_path = os.path.join(self.log_dir, "combined.log")

        self._stop = threading.Event()
        self.master_fd = None
        self.slave_name = None
        self.ser = None

    def start(self) -> bool:
        # create PTY
        try:
            import pty
            master_fd, slave_fd = pty.openpty()
            self.master_fd = master_fd
            self.slave_name = os.ttyname(slave_fd)
        except Exception as e:
            print(f"Failed to create PTY: {e}")
            return False

        # open real serial device
        try:
            self.ser = serial.Serial(self.device, self.baud, timeout=0)
        except Exception as e:
            print(f"Failed to open serial {self.device}: {e}")
            os.close(self.master_fd)
            return False

        print(f"PTY bridge created. Point your radar at: {self.slave_name}")
        print(f"Bridging {self.slave_name} <-> {self.device} @ {self.baud}")

        self._bridge_thread = threading.Thread(target=self._bridge_loop, daemon=True)
        self._bridge_thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass
        try:
            if self.master_fd:
                os.close(self.master_fd)
        except Exception:
            pass

    def _bridge_loop(self) -> None:
        import select
        ser_fd = None
        try:
            ser_fd = self.ser.fileno()
        except Exception:
            ser_fd = None

        while not self._stop.is_set():
            rlist = []
            if self.master_fd is not None:
                rlist.append(self.master_fd)
            if ser_fd is not None:
                rlist.append(ser_fd)
            if not rlist:
                time.sleep(0.1)
                continue
            try:
                ready_r, _, _ = select.select(rlist, [], [], 1.0)
            except Exception:
                time.sleep(0.1)
                continue

            for fd in ready_r:
                if fd == self.master_fd:
                    try:
                        data = os.read(self.master_fd, 4096)
                    except OSError:
                        data = b""
                    if data:
                        # data written by radar -> forward to real device
                        try:
                            self.ser.write(data)
                        except Exception as e:
                            print(f"Serial write error: {e}")
                        self._log_tx(data)
                elif fd == ser_fd:
                    try:
                        # read what's available
                        avail = 4096
                        data = self.ser.read(avail)
                    except Exception as e:
                        print(f"Serial read error: {e}")
                        data = b""
                    if data:
                        try:
                            os.write(self.master_fd, data)
                        except Exception:
                            pass
                        self._log_rx(data)

        # loop exit

    def _log_line(self, path: str, prefix: str, data: bytes) -> None:
        line = f"{now_ts()} {prefix} {len(data)}B {data.hex()}\n"
        try:
            with open(path, "a") as f:
                f.write(line)
            with open(self.combined_path, "a") as f:
                f.write(line)
        except Exception as e:
            print(f"Failed to write log {path}: {e}")

    def _log_rx(self, data: bytes) -> None:
        self._log_line(self.rx_path, "RX", data)

    def _log_tx(self, data: bytes) -> None:
        self._log_line(self.tx_path, "TX", data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serial recorder/proxy for /dev/ttyACM0")
    parser.add_argument("--device", default="/dev/ttyACM0", help="Serial device to open (default: /dev/ttyACM0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate (default: 115200)")
    parser.add_argument("--port", type=int, default=4000, help="TCP listen port for client connections (default: 4000)")
    parser.add_argument("--log-dir", default="test_comm/logs", help="Directory to write logs (default: test_comm/logs)")
    args = parser.parse_args()

    recorder = SerialRecorderTCP(args.device, args.baud, args.port, args.log_dir)
    recorder.start()
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        recorder.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
