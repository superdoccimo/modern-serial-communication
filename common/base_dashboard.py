#!/usr/bin/env python3
"""
Base Dashboard - 基底ダッシュボードクラス
すべてのダッシュボードアプリケーションの共通基盤
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    DataTable, Header, Footer, RichLog, Sparkline, Button, Input
)
from textual.binding import Binding
import asyncio
import sys
import os
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

# 共通モジュールインポート
try:
    from .localization import LocalizationManager
    from .config_manager import ConfigManager
    from .ui_components import SerialStats, SendPanel, StatusBar
    from .port_utils import detect_available_ports, get_platform_default_port, validate_port_access
except ImportError:
    # 単体実行時の絶対インポート
    from common.localization import LocalizationManager
    from common.config_manager import ConfigManager
    from common.ui_components import SerialStats, SendPanel, StatusBar
    from common.port_utils import detect_available_ports, get_platform_default_port, validate_port_access

# シリアル通信ライブラリ
try:
    from modern_serial_comm import ModernSerialComm, SerialConfig
except ImportError:
    try:
        import sys
        sys.path.append('..')
        from modern_serial_comm import ModernSerialComm, SerialConfig
    except ImportError:
        print("Error: modern_serial_comm.py が見つかりません")
        sys.exit(1)


class BaseDashboard(App):
    """すべてのダッシュボードの基底クラス"""
    
    # デフォルトCSS（サブクラスで上書き可能）
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #left_panel {
        width: 45;
        height: 100%;
        layout: vertical;
        margin: 0 1;
    }
    
    #main_area {
        width: 1fr;
        height: 100%;
        layout: vertical;
    }
    
    .panel-title {
        text-style: bold;
        color: $accent;
        margin: 1 0 0 0;
    }
    
    .button-row {
        height: 3;
        align: center middle;
        margin: 1 0;
    }
    
    Button {
        margin: 0 1;
    }
    
    #connection_panel {
        height: auto;
        border: solid $success;
        padding: 1;
        margin-bottom: 1;
    }
    
    #send_panel {
        height: auto;
        border: solid $warning;
        padding: 1;
        margin-bottom: 1;
    }
    
    #stats_panel {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }
    
    #data_table {
        height: 50%;
        border: solid $primary;
    }
    
    #sparkline {
        height: 20%;
        border: solid $secondary;
        padding: 1;
    }
    
    #log_view {
        height: 30%;
        border: solid $primary;
        overflow-y: scroll;
    }
    
    Input {
        margin: 1 0;
    }
    """
    
    # デフォルトキーバインド
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "clear_data", "Clear Data", show=True),
        Binding("s", "save_data", "Save CSV", show=True),
        Binding("d", "detect_ports", "Detect Ports", show=True),
        Binding("r", "reconnect", "Reconnect", show=False),
    ]
    
    def __init__(self, 
                 language: str = "jp",
                 config_file: Optional[str] = None,
                 **kwargs):
        """
        基底ダッシュボード初期化
        
        Args:
            language: 表示言語 ("jp" または "en")
            config_file: 設定ファイルパス
            **kwargs: その他のApp引数
        """
        super().__init__(**kwargs)
        
        # 多言語対応
        self.loc = LocalizationManager(language)
        
        # 設定管理
        self.config_manager = ConfigManager(config_file)
        
        # シリアル通信
        self.serial_comm: Optional[ModernSerialComm] = None
        self.connected = False
        
        # データ管理
        self.data_buffer: List[Dict[str, Any]] = []
        self.sparkline_data: List[float] = []
        
        # 設定値
        app_config = self.config_manager.get_app_config()
        self.max_data_rows = app_config['max_data_rows']
        self.max_sparkline_points = app_config['max_sparkline_points']
        
        # タイトル設定
        self.title = self.loc.get("app_title")
        self.sub_title = self.loc.get("app_subtitle")
    
    def compose(self) -> ComposeResult:
        """基本レイアウト構成（サブクラスで上書き必須）"""
        yield Header()
        
        with Horizontal():
            # 左パネル（サブクラスで実装）
            with Vertical(id="left_panel"):
                yield from self.compose_left_panel()
            
            # メインエリア
            with Vertical(id="main_area"):
                yield from self.compose_main_area()
        
        yield Footer()
    
    def compose_left_panel(self) -> ComposeResult:
        """左パネル構成（サブクラスで実装）"""
        yield SendPanel(self.loc, id="send_panel")
        yield SerialStats(self.loc, id="stats_panel")
    
    def compose_main_area(self) -> ComposeResult:
        """メインエリア構成"""
        yield DataTable(id="data_table")
        yield Sparkline(id="sparkline", data=[], summary_function=max)
        yield RichLog(id="log_view", highlight=True)
    
    def on_mount(self) -> None:
        """アプリ起動時の初期化"""
        self.setup_data_table()
        self.setup_initial_log()
        self.setup_auto_port_detection()
    
    def setup_data_table(self):
        """データテーブル初期化"""
        table = self.query_one("#data_table", DataTable)
        table.add_columns(
            self.loc.get("table_time"),
            self.loc.get("table_direction"), 
            self.loc.get("table_data"),
            self.loc.get("table_length")
        )
        table.cursor_type = "row"
    
    def setup_initial_log(self):
        """初期ログメッセージ表示"""
        self.log_message(self.loc.get("app_started"))
        self.log_message(self.loc.get("app_help"))
    
    def setup_auto_port_detection(self):
        """自動ポート検出実行"""
        self.action_detect_ports()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタンクリック処理（共通）"""
        button_id = event.button.id
        
        # 共通ボタン処理
        if button_id == "send_btn":
            await self.send_data()
        elif button_id == "clear_btn":
            self.clear_send_input()
        elif button_id == "detect_ports_btn":
            self.action_detect_ports()
        elif button_id == "preset_btn":
            self.set_preset_port()
        else:
            # サブクラス固有の処理
            await self.handle_custom_button(event)
    
    async def handle_custom_button(self, event: Button.Pressed) -> None:
        """カスタムボタン処理（サブクラスで実装）"""
        pass
    
    def log_message(self, message: str):
        """ログメッセージ出力"""
        log = self.query_one("#log_view", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")
    
    def action_detect_ports(self) -> None:
        """ポート検出アクション"""
        self.log_message(self.loc.get("detecting_ports"))
        
        ports = detect_available_ports()
        self.log_message(self.loc.get("ports_detected", len(ports)))
        
        # 最初の5つをログに出力
        for port, desc in ports[:5]:
            self.log_message(f"   • {port} - {desc}")
        
        # サブクラスでのポート検出後処理
        self.on_ports_detected(ports)
    
    def on_ports_detected(self, ports: List[tuple]):
        """ポート検出後の処理（サブクラスで実装）"""
        pass
    
    def set_preset_port(self) -> None:
        """プリセットポート設定（サブクラスで実装）"""
        preset_port = get_platform_default_port()
        self.log_message(self.loc.get("preset_port_set", preset_port))
        # サブクラスで具体的な設定処理を実装
    
    async def connect_serial(self, port: str) -> bool:
        """
        シリアル接続
        
        Args:
            port: 接続ポート
            
        Returns:
            bool: 接続成功の場合True
        """
        if not port.strip():
            self.log_message(self.loc.get("port_not_entered"))
            return False
        
        # ポート検証
        is_valid, error_msg = validate_port_access(port)
        if not is_valid:
            self.log_message(f"❌ {error_msg}")
            return False
        
        try:
            # 設定に基づいてModernSerialCommインスタンス作成
            serial_config = self.config_manager.get_serial_config(port)
            
            # 既存のシリアル通信があれば切断
            if self.serial_comm:
                await self.serial_comm.disconnect()
            
            # 新しいインスタンス作成
            self.serial_comm = ModernSerialComm()
            self.serial_comm.port = serial_config['port']
            self.serial_comm.baudrate = serial_config['baudrate']
            self.serial_comm.bytesize = serial_config['bytesize']
            self.serial_comm.parity = serial_config['parity']
            self.serial_comm.stopbits = serial_config['stopbits']
            self.serial_comm.timeout = serial_config['timeout']
            self.serial_comm.rtscts = serial_config['rtscts']
            self.serial_comm.dsrdtr = serial_config['dsrdtr']
            self.serial_comm.xonxoff = serial_config['xonxoff']
            
            # コールバック設定
            self.serial_comm.set_receive_callback(self.on_data_received)
            self.serial_comm.set_error_callback(self.on_serial_error)
            
            # 接続実行
            self.log_message(self.loc.get("connecting"))
            if await self.serial_comm.connect():
                self.connected = True
                self.log_message(self.loc.get("connected", port))
                self.update_connection_ui(True, port)
                return True
            else:
                self.log_message(self.loc.get("connection_failed", port))
                return False
                
        except Exception as e:
            self.log_message(self.loc.get("connection_error", str(e)))
            return False
    
    async def disconnect_serial(self):
        """シリアル切断"""
        if self.serial_comm and self.connected:
            await self.serial_comm.disconnect()
            self.connected = False
            self.log_message(self.loc.get("disconnected"))
            self.update_connection_ui(False)
    
    def update_connection_ui(self, connected: bool, port: str = ""):
        """接続状態に応じたUI更新（サブクラスで実装）"""
        pass
    
    async def send_data(self):
        """データ送信"""
        if not self.connected or not self.serial_comm:
            self.log_message(self.loc.get("not_connected"))
            return
        
        # 送信データ取得（サブクラスで実装）
        data = self.get_send_data()
        if not data:
            return
        
        # 改行コード追加
        if not data.endswith(('\r\n', '\r', '\n')):
            data += '\r\n'
        
        if await self.serial_comm.send_string(data):
            self.log_message(self.loc.get("data_sent", data.strip()))
            self.clear_send_input()
            
            # 統計更新
            self.update_stats("TX", len(data.encode()))
            
            # データテーブル追加
            self.add_to_data_table("TX", data.strip(), len(data.encode()))
        else:
            self.log_message(self.loc.get("send_failed"))
    
    def get_send_data(self) -> str:
        """送信データ取得（サブクラスで実装）"""
        try:
            send_input = self.query_one("#send_input", Input)
            return send_input.value.strip()
        except:
            return ""
    
    def clear_send_input(self):
        """送信入力フィールドクリア"""
        try:
            send_input = self.query_one("#send_input", Input)
            send_input.value = ""
        except:
            pass
    
    def on_data_received(self, data: bytes, direction: str):
        """データ受信処理"""
        self.call_later(self._handle_received_data, data, direction)
    
    def on_serial_error(self, error_msg: str):
        """シリアルエラー処理"""
        self.call_later(self.log_message, f"❌ {error_msg}")
    
    def _handle_received_data(self, data: bytes, direction: str):
        """データ受信処理（UIスレッド）"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if direction == "RX":
                self.log_message(self.loc.get("data_received", data_str))
                self.add_to_data_table("RX", data_str, len(data))
                self.update_stats("RX", len(data))
                self.update_sparkline(len(data))
        except Exception as e:
            self.log_message(self.loc.get("data_processing_error", str(e)))
    
    def add_to_data_table(self, direction: str, data: str, length: int):
        """データテーブルに行追加"""
        table = self.query_one("#data_table", DataTable)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # データ表示制限
        display_data = data[:50] + "..." if len(data) > 50 else data
        dir_display = self.loc.get("table_rx") if direction == "RX" else self.loc.get("table_tx")
        
        table.add_row(timestamp, dir_display, display_data, str(length))
        
        # バッファに保存
        self.data_buffer.append({
            'timestamp': datetime.now(),
            'direction': direction,
            'data': data,
            'length': length
        })
        
        # 行数制限
        if table.row_count > self.max_data_rows:
            table.remove_row(0)
            self.data_buffer.pop(0)
    
    def update_stats(self, direction: str, byte_count: int):
        """統計更新"""
        try:
            stats = self.query_one("#stats_panel", SerialStats)
            stats.update_stats(direction, byte_count)
        except:
            pass
    
    def update_sparkline(self, data_length: int):
        """スパークライン更新"""
        try:
            sparkline = self.query_one("#sparkline", Sparkline)
            self.sparkline_data.append(data_length)
            
            if len(self.sparkline_data) > self.max_sparkline_points:
                self.sparkline_data.pop(0)
            
            sparkline.data = self.sparkline_data
        except:
            pass
    
    def action_clear_data(self) -> None:
        """データクリア"""
        try:
            table = self.query_one("#data_table", DataTable)
            table.clear()
            
            sparkline = self.query_one("#sparkline", Sparkline)
            self.sparkline_data.clear()
            sparkline.data = []
            
            self.data_buffer.clear()
            
            # 統計リセット
            stats = self.query_one("#stats_panel", SerialStats)
            stats.reset_stats()
            
            self.log_message(self.loc.get("data_cleared"))
        except Exception as e:
            self.log_message(f"❌ Clear error: {e}")
    
    def action_save_data(self) -> None:
        """CSV保存"""
        if not self.data_buffer:
            self.log_message(self.loc.get("no_data_to_save"))
            return
        
        filename = f"serial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    self.loc.get("table_time"),
                    self.loc.get("table_direction"),
                    self.loc.get("table_data"),
                    self.loc.get("table_length")
                ])
                
                for entry in self.data_buffer:
                    writer.writerow([
                        entry['timestamp'].isoformat(),
                        entry['direction'],
                        entry['data'],
                        entry['length']
                    ])
            
            self.log_message(self.loc.get("data_saved", filename, len(self.data_buffer)))
        except Exception as e:
            self.log_message(self.loc.get("save_error", str(e)))
    
    async def action_reconnect(self) -> None:
        """再接続"""
        if self.connected and self.serial_comm:
            port = self.serial_comm.port
            await self.disconnect_serial()
            await asyncio.sleep(1)  # 1秒待機
            await self.connect_serial(port)
    
    async def action_quit(self) -> None:
        """アプリ終了"""
        if self.serial_comm and self.connected:
            await self.serial_comm.safe_shutdown()
        self.exit()


if __name__ == "__main__":
    """テスト用のシンプルなダッシュボード"""
    from textual.widgets import Input, Label
    
    class TestDashboard(BaseDashboard):
        """テスト用ダッシュボード"""
        
        def compose_left_panel(self) -> ComposeResult:
            yield Label(self.loc.get("port_control"), classes="panel-title")
            yield Input(
                placeholder=self.loc.get("port_placeholder", get_platform_default_port()),
                id="port_input",
                value=get_platform_default_port()
            )
            with Horizontal(classes="button-row"):
                yield Button(self.loc.get("connect"), id="connect_btn", variant="success")
                yield Button(self.loc.get("disconnect"), id="disconnect_btn", variant="error", disabled=True)
            
            yield from super().compose_left_panel()
        
        async def handle_custom_button(self, event: Button.Pressed) -> None:
            if event.button.id == "connect_btn":
                port_input = self.query_one("#port_input", Input)
                await self.connect_serial(port_input.value)
            elif event.button.id == "disconnect_btn":
                await self.disconnect_serial()
        
        def update_connection_ui(self, connected: bool, port: str = ""):
            try:
                connect_btn = self.query_one("#connect_btn", Button)
                disconnect_btn = self.query_one("#disconnect_btn", Button)
                
                connect_btn.disabled = connected
                disconnect_btn.disabled = not connected
            except:
                pass
    
    # テスト実行
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = TestDashboard()
    app.run()