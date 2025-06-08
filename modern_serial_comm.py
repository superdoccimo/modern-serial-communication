#!/usr/bin/env python3
"""
Modern Serial Communication Library
Python replacement for Serial (Cross-platform)
"""

import asyncio
import serial_asyncio  # pyserial-asyncio が必要
import json
import configparser
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
import sys
import serial  # serial.SerialException をキャッチするためにインポート
import os

# Windows では grp/pwd が存在しないため、プラットフォーム判別してインポート
if sys.platform.startswith("linux"):
    import grp
    import pwd


class EventLogger:
    """イベントロギング用クラス"""
    def __init__(self, log_file_path: Optional[str] = "serial_events.log"):
        self.log_entries: List[Dict[str, Any]] = []
        self.log_file_path = Path(log_file_path) if log_file_path else None
        self.logger = logging.getLogger(__name__)
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_event(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "message": message,
            "details": details or {}
        }
        self.log_entries.append(log_entry)
        self.logger.info(f"[{event_type.upper()}] {message} {details if details else ''}")
        if self.log_file_path:
            try:
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception as e:
                self.logger.error(f"Failed to write to log file {self.log_file_path}: {e}")

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.log_entries

    def flush_logs_to_file(self):
        """メモリ上のログを指定されたファイルに書き出す（追記）"""
        if not self.log_file_path or not self.log_entries:
            return
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                for entry in self.log_entries:
                    f.write(json.dumps(entry) + "\n")
            self.logger.info(f"Flushed logs to {self.log_file_path}")
        except Exception as e:
            self.logger.error(f"Failed to flush logs to file {self.log_file_path}: {e}")


class SerialConfig:
    """シリアル通信設定管理"""
    def __init__(self, config_path: str = "serial_config.ini"):
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger(__name__ + ".SerialConfig")
        self.load_config()

    def load_config(self):
        """設定ファイル読み込み"""
        if self.config_path.exists():
            try:
                self.config.read(self.config_path, encoding='utf-8')
                self.logger.info(f"Configuration loaded from {self.config_path}")
            except Exception as e:
                self.logger.error(f"Error reading config file {self.config_path}: {e}. Using defaults.")
                self.create_default_config()
        else:
            self.logger.warning(f"Config file {self.config_path} not found. Creating default configuration.")
            self.create_default_config()
            self.save_config()

    def create_default_config(self):
        """デフォルト設定作成"""
        self.config['SERIAL'] = {
            'port': 'loop://',
            'baudrate': '9600',
            'bytesize': '8',
            'parity': 'N',
            'stopbits': '1',
            'timeout': '1.0',
            'rtscts': 'False',
            'dsrdtr': 'False',
            'xonxoff': 'False'
        }
        self.config['APP'] = {
            'log_level': 'INFO',
            'timestamp_format': '%Y-%m-%d %H:%M:%S.%f'
        }
        self.logger.info("Default configuration created.")

    def save_config(self):
        """設定ファイル保存"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            self.logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error saving config file {self.config_path}: {e}")

    def get_setting(self, section: str, key: str, fallback: Optional[Any] = None) -> Optional[Any]:
        """設定値取得"""
        return self.config.get(section, key, fallback=fallback)

    def set_setting(self, section: str, key: str, value: str):
        """設定値設定"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)


class ModernSerialComm:
    """非同期シリアル通信管理クラス"""
    def __init__(self, config_path: str = "serial_config.ini"):
        self.config_manager = SerialConfig(config_path)
        self.port: Optional[str] = None
        self.baudrate: int = 9600
        self.bytesize: int = serial.EIGHTBITS
        self.parity: str = serial.PARITY_NONE
        self.stopbits: float = serial.STOPBITS_ONE
        self.timeout: Optional[float] = 1.0
        self.rtscts: bool = False
        self.dsrdtr: bool = False
        self.xonxoff: bool = False

        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.is_connected: bool = False
        self.receive_task: Optional[asyncio.Task] = None
        self.receive_callback: Optional[Callable[[bytes, str], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None

        self.logger = EventLogger()
        self._load_settings_from_config()

    def _load_settings_from_config(self):
        """設定ファイルからシリアルパラメータをロード"""
        s = 'SERIAL'
        self.port = self.config_manager.get_setting(s, 'port', 'loop://')

        try:
            self.baudrate = int(self.config_manager.get_setting(s, 'baudrate', '9600') or 9600)
            bytesize_str = self.config_manager.get_setting(s, 'bytesize', '8')
            bytesize_map = {'5': serial.FIVEBITS, '6': serial.SIXBITS, '7': serial.SEVENBITS, '8': serial.EIGHTBITS}
            self.bytesize = bytesize_map.get(bytesize_str, serial.EIGHTBITS)

            parity_str = self.config_manager.get_setting(s, 'parity', 'N').upper()
            parity_map = {
                'N': serial.PARITY_NONE, 'E': serial.PARITY_EVEN,
                'O': serial.PARITY_ODD, 'M': serial.PARITY_MARK, 'S': serial.PARITY_SPACE
            }
            self.parity = parity_map.get(parity_str, serial.PARITY_NONE)

            stopbits_str = self.config_manager.get_setting(s, 'stopbits', '1')
            stopbits_map = {'1': serial.STOPBITS_ONE, '1.5': serial.STOPBITS_ONE_POINT_FIVE, '2': serial.STOPBITS_TWO}
            self.stopbits = stopbits_map.get(stopbits_str, serial.STOPBITS_ONE)

            timeout_str = self.config_manager.get_setting(s, 'timeout', '1.0')
            self.timeout = float(timeout_str) if timeout_str else None

            self.rtscts = self.config_manager.get_setting(s, 'rtscts', 'False').lower() == 'true'
            self.dsrdtr = self.config_manager.get_setting(s, 'dsrdtr', 'False').lower() == 'true'
            self.xonxoff = self.config_manager.get_setting(s, 'xonxoff', 'False').lower() == 'true'
            self.logger.log_event("config_loaded", f"Serial settings loaded: {self.get_config_summary()}")
        except Exception as e:
            self.logger.log_event("config_error", f"Error loading serial settings: {e}. Using defaults.")
            # 戻り値はデフォルトのまま
            self.baudrate = 9600
            self.bytesize = serial.EIGHTBITS
            self.parity = serial.PARITY_NONE
            self.stopbits = serial.STOPBITS_ONE
            self.timeout = 1.0
            self.rtscts = False
            self.dsrdtr = False
            self.xonxoff = False
            self.logger.log_event("config_default", f"Using default serial settings: {self.get_config_summary()}")

    def set_receive_callback(self, callback: Callable[[bytes, str], None]):
        self.receive_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]):
        self.error_callback = callback

    async def _read_loop(self):
        if not self.reader:
            self.logger.log_event("read_loop_error", "Reader not available for read loop.")
            if self.error_callback:
                self.error_callback("Reader not available for read loop.")
            return

        self.logger.log_event("read_loop_start", "Read loop started.")
        try:
            while self.is_connected:
                try:
                    read_timeout = self.timeout if self.timeout and self.timeout > 0 else 0.1
                    data = await asyncio.wait_for(self.reader.read(1024), timeout=read_timeout)
                    if data:
                        if self.receive_callback:
                            self.receive_callback(data, "RX")
                        self.logger.log_event("data_received", f"Received {len(data)} bytes", {
                            "length": len(data), "raw_hex": data.hex()
                        })
                    else:
                        if self.is_connected:
                            self.logger.log_event("read_loop_info", "Reader returned empty data, might indicate connection close.")
                        break
                except asyncio.TimeoutError:
                    continue
                except serial.SerialException as e:
                    self.logger.log_event("serial_exception_read", f"Serial read error: {e}", {"error": str(e)})
                    if self.error_callback:
                        self.error_callback(f"Serial read error: {e}")
                    self.is_connected = False
                    break
                except ConnectionResetError as e:
                    self.logger.log_event("connection_reset_error", f"Connection reset during read: {e}", {"error": str(e)})
                    if self.error_callback:
                        self.error_callback(f"Connection reset: {e}")
                    self.is_connected = False
                    break
                except Exception as e:
                    self.logger.log_event("read_loop_exception", f"Unexpected error in read loop: {e}", {"error": str(e)})
                    if self.error_callback:
                        self.error_callback(f"Unexpected read error: {e}")
                    self.is_connected = False
                    break
        except asyncio.CancelledError:
            self.logger.log_event("read_loop_cancelled", "Read loop was cancelled.")
        finally:
            self.logger.log_event("read_loop_exit", "Exiting read loop.")

    async def connect(self) -> bool:
        """シリアル接続開始（Linux 権限チェック対応）"""
        if self.is_connected:
            self.logger.log_event("connect_attempt_while_connected", "Already connected.")
            return True

        self._load_settings_from_config()
        if not self.port:
            self.logger.log_event("connect_error_no_port", "Port not specified.")
            if self.error_callback:
                self.error_callback("Port not specified.")
            return False

        # Linux 環境での権限チェック
        if sys.platform.startswith('linux') and self.port.startswith('/dev/'):
            if os.path.exists(self.port):
                if not os.access(self.port, os.R_OK | os.W_OK):
                    error_msg = f"Permission denied for {self.port}. "
                    try:
                        current_user = pwd.getpwuid(os.getuid()).pw_name
                        groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
                        if 'dialout' not in groups:
                            error_msg += "User not in dialout group. Run: sudo usermod -a -G dialout $USER"
                        else:
                            error_msg += "Try running with sudo or check device permissions."
                    except:
                        error_msg += "Check permissions."
                    self.logger.log_event("permission_error", error_msg)
                    if self.error_callback:
                        self.error_callback(error_msg)
                    return False
            else:
                # デバイスが存在しない場合、利用可能なポートを提案
                available_ports = []
                for prefix in ['/dev/ttyUSB', '/dev/ttyACM', '/dev/ttyS']:
                    for i in range(10):
                        candidate = f"{prefix}{i}"
                        if os.path.exists(candidate):
                            available_ports.append(candidate)
                error_msg = f"{self.port} does not exist. "
                if available_ports:
                    error_msg += f"Available ports: {', '.join(available_ports)}"
                else:
                    error_msg += "No serial ports found."
                self.logger.log_event("port_not_found", error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False

        try:
            self.logger.log_event("connecting", f"Attempting to connect to {self.port} at {self.baudrate} bps")

            # シリアル接続設定
            kwargs = {
                'url': self.port,
                'baudrate': self.baudrate,
                'bytesize': self.bytesize,
                'parity': self.parity,
                'stopbits': self.stopbits,
                'timeout': self.timeout,
                'rtscts': self.rtscts,
                'dsrdtr': self.dsrdtr,
                'xonxoff': self.xonxoff
            }
            # Linux 環境の場合は exclusive=True を追加（他プロセス排他制御）
            if sys.platform.startswith('linux'):
                kwargs['exclusive'] = True

            self.reader, self.writer = await serial_asyncio.open_serial_connection(**kwargs)
            self.is_connected = True
            self.receive_task = asyncio.create_task(self._read_loop())
            self.logger.log_event("connected", f"Successfully connected to {self.port}")
            return True

        except serial.SerialException as e:
            error_msg = str(e)
            if "Permission denied" in error_msg:
                error_msg = "Permission denied. Run: sudo usermod -a -G dialout $USER && logout"
            elif "could not open port" in error_msg:
                error_msg = f"Could not open {self.port}. Check if device exists and is not in use."
            self.logger.log_event("connect_serial_exception", error_msg, {"error": str(e)})
            if self.error_callback:
                self.error_callback(error_msg)
            self.is_connected = False
            return False

        except Exception as e:
            self.logger.log_event("connect_exception", f"Unexpected error: {e}", {"error": str(e)})
            if self.error_callback:
                self.error_callback(f"Unexpected error: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """シリアル接続終了 (Windows でのハング対策込み)"""
        if not self.is_connected and not self.writer and not self.receive_task:
            self.logger.log_event("disconnect_attempt_while_disconnected", "Already disconnected or not connected.")
            return

        self.is_connected = False
        self.logger.log_event("disconnect_start", "Starting disconnect procedure.")

        if self.receive_task:
            if not self.receive_task.done():
                self.logger.log_event("disconnect_info", "Cancelling receive_task...")
                self.receive_task.cancel()
                try:
                    await asyncio.wait_for(self.receive_task, timeout=0.5)
                    self.logger.log_event("disconnect_info", "Receive_task awaited or timed out.")
                except asyncio.CancelledError:
                    self.logger.log_event("disconnect_info", "Receive task cancelled as expected.")
                except asyncio.TimeoutError:
                    self.logger.log_event("disconnect_warning", "Timeout waiting for receive_task after cancel.")
                except Exception as e:
                    self.logger.log_event("disconnect_error", f"Error awaiting receive_task: {e}")
            else:
                self.logger.log_event("disconnect_info", "Receive_task was already done.")
            self.receive_task = None

        if self.writer:
            self.logger.log_event("disconnect_info", "Closing writer.")
            try:
                if sys.platform == "win32":
                    if hasattr(self.writer, "transport") and self.writer.transport:
                        transport_closing = False
                        if hasattr(self.writer.transport, "is_closing"):
                            transport_closing = self.writer.transport.is_closing()
                        if not transport_closing:
                            self.logger.log_event("disconnect_info", "Aborting transport (Windows).")
                            try:
                                self.writer.transport.abort()
                            except Exception as e:
                                self.logger.log_event("disconnect_error", f"Error aborting transport: {e}")
                        else:
                            self.logger.log_event("disconnect_info", "Transport was already closing (Windows).")

                if not self.writer.is_closing():
                    self.writer.close()
                    self.logger.log_event("disconnect_info", "writer.close() called.")
                else:
                    self.logger.log_event("disconnect_info", "Writer was already closing.")

                try:
                    wait_closed = self.writer.wait_closed()
                    if wait_closed is not None:
                        if sys.platform != "win32":
                            await asyncio.wait_for(wait_closed, timeout=0.5)
                        else:
                            try:
                                await asyncio.wait_for(wait_closed, timeout=0.1)
                            except asyncio.TimeoutError:
                                self.logger.log_event("disconnect_warning", "Writer wait_closed() timed out (Windows).")
                        self.logger.log_event("disconnect_info", "Writer closed successfully or timed out.")
                    else:
                        self.logger.log_event("disconnect_info", "writer.wait_closed() returned None.")
                except asyncio.TimeoutError:
                    self.logger.log_event("disconnect_warning", "Writer close timeout (non-Windows).")
                except Exception as e:
                    self.logger.log_event("disconnect_error", f"Error during writer.wait_closed(): {e}")

            except Exception as e:
                self.logger.log_event("disconnect_error", f"Error during writer close: {e}")
            finally:
                self.writer = None

        self.reader = None
        self.logger.log_event("disconnected", "Serial connection resources released.")

    async def send_string(self, data_str: str, encoding: str = 'utf-8') -> bool:
        if not self.is_connected or not self.writer:
            self.logger.log_event("send_error_not_connected", "Cannot send data: Not connected.")
            if self.error_callback:
                self.error_callback("Cannot send data: Not connected.")
            return False
        try:
            data_bytes = data_str.encode(encoding)
            self.writer.write(data_bytes)
            await self.writer.drain()
            if self.receive_callback:
                self.receive_callback(data_bytes, "TX")
            self.logger.log_event("data_sent", f"Sent {len(data_bytes)} bytes", {
                "length": len(data_bytes), "data_str": data_str
            })
            return True
        except ConnectionResetError as e:
            self.logger.log_event("send_connection_reset", f"Connection reset during send: {e}", {"error": str(e)})
            if self.error_callback:
                self.error_callback(f"Connection reset during send: {e}")
            await self.disconnect()
            return False
        except Exception as e:
            self.logger.log_event("send_exception", f"Error sending data: {e}", {"error": str(e)})
            if self.error_callback:
                self.error_callback(f"Error sending data: {e}")
            return False

    async def send_bytes(self, data_bytes: bytes) -> bool:
        if not self.is_connected or not self.writer:
            self.logger.log_event("send_error_not_connected_bytes", "Cannot send bytes: Not connected.")
            if self.error_callback:
                self.error_callback("Cannot send bytes: Not connected.")
            return False
        try:
            self.writer.write(data_bytes)
            await self.writer.drain()
            if self.receive_callback:
                self.receive_callback(data_bytes, "TX")
            self.logger.log_event("data_sent_bytes", f"Sent {len(data_bytes)} bytes", {
                "length": len(data_bytes), "raw_hex": data_bytes.hex()
            })
            return True
        except ConnectionResetError as e:
            self.logger.log_event("send_bytes_connection_reset", f"Connection reset during send_bytes: {e}", {"error": str(e)})
            if self.error_callback:
                self.error_callback(f"Connection reset during send_bytes: {e}")
            await self.disconnect()
            return False
        except Exception as e:
            self.logger.log_event("send_exception_bytes", f"Error sending bytes: {e}", {"error": str(e)})
            if self.error_callback:
                self.error_callback(f"Error sending bytes: {e}")
            return False

    def get_config_summary(self) -> str:
        return (
            f"Port: {self.port}, Baud: {self.baudrate}, Size: {self.bytesize}, "
            f"Parity: {self.parity}, Stopbits: {self.stopbits}, Timeout: {self.timeout}"
        )

    def export_log_to_json(self, output_path: Optional[str] = None) -> None:
        log_entries = self.logger.get_logs()
        if not log_entries:
            self.logger.log_event('json_export_empty', "No log entries to export.")
            return

        if output_path is None:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"serial_log_{timestamp_str}.json"

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(log_entries, f, indent=4, ensure_ascii=False)
            self.logger.log_event('json_export_success', f"Exported {len(log_entries)} log entries to {output_path}")
        except Exception as e:
            self.logger.log_event('json_export_error', f"Failed to export log to JSON: {e}")

    def get_connection_status(self) -> Dict[str, Any]:
        """接続状態の詳細情報を取得"""
        status = {
            "is_connected": self.is_connected,
            "port": self.port,
            "baudrate": self.baudrate,
            "platform": sys.platform,
            "python_version": sys.version,
            "has_reader": self.reader is not None,
            "has_writer": self.writer is not None,
            "receive_task_running": self.receive_task is not None and not self.receive_task.done() if self.receive_task else False
        }

        if self.writer and hasattr(self.writer, "transport") and self.writer.transport:
            try:
                status["transport_closing"] = self.writer.transport.is_closing() if hasattr(self.writer.transport, "is_closing") else "unknown_or_not_supported"
            except Exception:
                status["transport_closing"] = "error_checking_status"
        else:
            status["transport_closing"] = "no_transport"
        return status

    async def safe_shutdown(self):
        """プログラム終了時のクリーンアップ処理 (より安全なシャットダウン)"""
        self.logger.log_event("shutdown_start", "Starting safe shutdown procedure")

        if self.is_connected:
            self.logger.log_event("shutdown_info", "Connection active, attempting disconnect.")
            await self.disconnect()
        else:
            self.logger.log_event("shutdown_info", "Connection already inactive.")

        self.logger.flush_logs_to_file()
        self.logger.log_event("shutdown_complete", "Safe shutdown procedure completed.")


async def example_usage():
    """使用例"""
    serial_comm = ModernSerialComm()

    def handle_received_data_example(data: bytes, direction: str):
        try:
            print(f"{datetime.now().isoformat()} {direction}: {data.decode('utf-8', errors='replace').strip()}")
        except Exception:
            print(f"{datetime.now().isoformat()} {direction} (raw): {data.hex()}")

    def handle_error_example(error_msg: str):
        print(f"SERIAL ERROR: {error_msg}")

    serial_comm.set_receive_callback(handle_received_data_example)
    serial_comm.set_error_callback(handle_error_example)

    try:
        print("Attempting to connect...")
        if await serial_comm.connect():
            print(f"Connected! Config: {serial_comm.get_config_summary()}")
            await serial_comm.send_string("Hello from ModernSerialComm!\r\n")
            print("Waiting for data for 5 seconds (Press Ctrl+C to interrupt)...")
            try:
                if serial_comm.receive_task:
                    await asyncio.wait_for(asyncio.shield(serial_comm.receive_task), timeout=5.0)
            except asyncio.TimeoutError:
                print("5 seconds elapsed.")
            except asyncio.CancelledError:
                print("\nOperation cancelled by user during wait.")
            print("Disconnecting...")
        else:
            print("Failed to connect.")

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received by user.")

    except Exception as e:
        print(f"An unexpected error occurred in example_usage: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("Cleaning up in example_usage...")
        await serial_comm.safe_shutdown()

        if sys.platform == "win32":
            await asyncio.sleep(0.25)
        else:
            await asyncio.sleep(0.1)

        print("Cleanup completed in example_usage.")


if __name__ == "__main__":
    # Windows の場合は特別なイベントループポリシーを設定
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        config_file = "serial_config_windows.ini"
    elif sys.platform.startswith("linux"):
        config_file = "serial_config_linux.ini"
    else:
        config_file = "serial_config.ini"  # それ以外は汎用設定を使用

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main():
        # 指定した設定ファイルを使ってインスタンス化
        serial_comm = ModernSerialComm(config_file)

        def handle_received_data(data: bytes, direction: str):
            try:
                print(f"{datetime.now().isoformat()} {direction}: {data.decode('utf-8', errors='replace').strip()}")
            except Exception:
                print(f"{datetime.now().isoformat()} {direction} (raw): {data.hex()}")

        def handle_error(error_msg: str):
            print(f"SERIAL ERROR: {error_msg}")

        serial_comm.set_receive_callback(handle_received_data)
        serial_comm.set_error_callback(handle_error)

        try:
            print("Attempting to connect...")
            if await serial_comm.connect():
                print(f"Connected! Config: {serial_comm.get_config_summary()}")
                await serial_comm.send_string("Hello from cross-platform serial comm!\r\n")
                print("Waiting for data for 5 seconds...")
                try:
                    if serial_comm.receive_task:
                        await asyncio.wait_for(asyncio.shield(serial_comm.receive_task), timeout=5.0)
                except asyncio.TimeoutError:
                    print("5 seconds elapsed.")
            else:
                print("Failed to connect.")
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received by user.")
        finally:
            print("Cleaning up...")
            await serial_comm.safe_shutdown()
            if sys.platform == "win32":
                await asyncio.sleep(0.25)
            else:
                await asyncio.sleep(0.1)
            print("Cleanup completed.")

    try:
        loop.run_until_complete(main())
    finally:
        print("Ensuring all tasks are cancelled before closing loop.")
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()
        print("Event loop closed.")
