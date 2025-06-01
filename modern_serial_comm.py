#!/usr/bin/env python3
"""
Modern Serial Communication Library
Python replacement for Serial

GitHub: [https://github.com/superdoccimo/modern-serial-communication.git]
License: MIT
Author: [Mamu Minokamo]
"""

import asyncio
import serial_asyncio
import json
import configparser
import logging
import datetime as dt
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import sys


class SerialConfig:
    """シリアル通信設定管理"""
    
    def __init__(self, config_path: str = "serial_config.ini"):
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """設定ファイル読み込み"""
        if self.config_path.exists():
            self.config.read(self.config_path, encoding='utf-8')
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """デフォルト設定作成"""
        self.config['SERIAL'] = {
            'port': 'loop://',  # テスト用ループバック
            'baudrate': '9600',
            'bytesize': '8',
            'parity': 'N',
            'stopbits': '1',
            'timeout': '1.0'
        }
        
        self.config['NETWORK'] = {
            'tcp_host': 'localhost',
            'tcp_port': '5000',
            'use_tcp': 'false'
        }
        
        self.config['LOGGING'] = {
            'level': 'INFO',
            'format': 'json_lines',
            'output_file': 'serial_log.jsonl'
        }
        
        self.save_config()
    
    def save_config(self):
        """設定ファイル保存"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get_serial_params(self) -> Dict[str, Any]:
        """シリアル通信パラメータ取得"""
        serial_section = self.config['SERIAL']
        
        if self.config.getboolean('NETWORK', 'use_tcp', fallback=False):
            # TCP接続の場合（VM環境対応）
            host = self.config.get('NETWORK', 'tcp_host')
            port = self.config.get('NETWORK', 'tcp_port')
            url = f'socket://{host}:{port}'
        else:
            # 直接シリアルポート接続
            url = serial_section.get('port')
        
        return {
            'url': url,
            'baudrate': serial_section.getint('baudrate'),
            'bytesize': serial_section.getint('bytesize'),
            'parity': serial_section.get('parity'),
            'stopbits': serial_section.getint('stopbits'),
            'timeout': serial_section.getfloat('timeout')
        }


class SerialLogger:
    """JSON Lines形式でのログ出力"""
    
    def __init__(self, config: SerialConfig):
        self.config = config
        self.setup_logging()
    
    def setup_logging(self):
        """ログ設定"""
        log_level = getattr(logging, self.config.config.get('LOGGING', 'level', fallback='INFO'))
        
        # コンソール出力
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        
        self.logger = logging.getLogger(__name__)
        
        # JSON Lines ファイル出力
        self.log_file = Path(self.config.config.get('LOGGING', 'output_file', fallback='serial_log.jsonl'))
    
    def log_data(self, direction: str, data: bytes, timestamp: Optional[dt.datetime] = None):
        """データ送受信ログ"""
        if timestamp is None:
            timestamp = dt.datetime.now()
        
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'direction': direction,  # 'RX' or 'TX'
            'data_hex': data.hex(),
            'data_ascii': data.decode('ascii', errors='ignore'),
            'length': len(data)
        }
        
        # コンソール出力
        self.logger.info(f"{direction}: {log_entry['data_ascii'][:50]}{'...' if len(log_entry['data_ascii']) > 50 else ''}")
        
        # JSON Lines ファイル出力
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def log_event(self, event_type: str, message: str, **kwargs):
        """イベントログ"""
        log_entry = {
            'timestamp': dt.datetime.now().isoformat(),
            'type': 'event',
            'event_type': event_type,
            'message': message,
            **kwargs
        }
        
        self.logger.info(f"Event: {event_type} - {message}")
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


class ModernSerialComm:
    """モダンなシリアル通信クラス"""
    
    def __init__(self, config_path: str = "serial_config.ini"):
        self.config = SerialConfig(config_path)
        self.logger = SerialLogger(self.config)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.is_connected = False
        self.receive_callback: Optional[Callable[[bytes], None]] = None
        self.receive_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """シリアル接続開始"""
        try:
            params = self.config.get_serial_params()
            self.logger.log_event('connect_attempt', f"Connecting to {params['url']}")
            
            self.reader, self.writer = await serial_asyncio.open_serial_connection(**params)
            self.is_connected = True
            
            # 受信タスク開始
            self.receive_task = asyncio.create_task(self._receive_loop())
            
            self.logger.log_event('connected', f"Successfully connected to {params['url']}")
            return True
            
        except Exception as e:
            self.logger.log_event('connect_error', f"Connection failed: {str(e)}")
            return False
    
    async def disconnect(self):
        """シリアル接続終了"""
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
        
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        
        self.is_connected = False
        self.logger.log_event('disconnected', "Serial connection closed")
    
    async def send(self, data: bytes) -> bool:
        """データ送信"""
        if not self.is_connected or not self.writer:
            return False
        
        try:
            self.writer.write(data)
            await self.writer.drain()
            self.logger.log_data('TX', data)
            return True
        except Exception as e:
            self.logger.log_event('send_error', f"Send failed: {str(e)}")
            return False
    
    async def send_string(self, text: str, encoding: str = 'ascii') -> bool:
        """文字列送信"""
        return await self.send(text.encode(encoding))
    
    def set_receive_callback(self, callback: Callable[[bytes], None]):
        """受信コールバック設定"""
        self.receive_callback = callback
    
    async def _receive_loop(self):
        """受信ループ（バックグラウンドタスク）"""
        while self.is_connected and self.reader:
            try:
                # 1行または一定バイト数まで受信
                data = await self.reader.readuntil(b'\r\n')
                
                if data:
                    self.logger.log_data('RX', data)
                    
                    # コールバック呼び出し
                    if self.receive_callback:
                        self.receive_callback(data)
                
            except asyncio.IncompleteReadError as e:
                # 部分的なデータでも処理
                if e.partial:
                    self.logger.log_data('RX', e.partial)
                    if self.receive_callback:
                        self.receive_callback(e.partial)
            except Exception as e:
                self.logger.log_event('receive_error', f"Receive error: {str(e)}")
                break
    
    async def export_to_csv(self, output_path: str, start_time: Optional[dt.datetime] = None):
        """CSV形式でデータエクスポート"""
        import csv
        
        # JSON Linesログを読み込んでCSV変換
        log_entries = []
        if self.logger.log_file.exists():
            with open(self.logger.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('direction') in ['RX', 'TX']:
                            if start_time is None or dt.datetime.fromisoformat(entry['timestamp']) >= start_time:
                                log_entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        # CSV出力
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'direction', 'data_ascii', 'data_hex', 'length']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in log_entries:
                writer.writerow({
                    'timestamp': entry['timestamp'],
                    'direction': entry['direction'],
                    'data_ascii': entry['data_ascii'],
                    'data_hex': entry['data_hex'],
                    'length': entry['length']
                })
        
        self.logger.log_event('csv_export', f"Exported {len(log_entries)} entries to {output_path}")


# 使用例
async def example_usage():
    """使用例"""
    
    # シリアル通信インスタンス作成
    serial_comm = ModernSerialComm()
    
    # 受信データ処理関数
    def handle_received_data(data: bytes):
        print(f"Received: {data.decode('ascii', errors='ignore').strip()}")
    
    # 受信コールバック設定
    serial_comm.set_receive_callback(handle_received_data)
    
    # 接続
    if await serial_comm.connect():
        print("Connected successfully!")
        
        # データ送信例
        await serial_comm.send_string("Hello Serial World!\r\n")
        
        # 10秒間受信待機
        await asyncio.sleep(10)
        
        # CSV出力
        await serial_comm.export_to_csv("serial_data.csv")
        
        # 切断
        await serial_comm.disconnect()
    else:
        print("Connection failed!")


if __name__ == "__main__":
    # 実行例
    asyncio.run(example_usage())