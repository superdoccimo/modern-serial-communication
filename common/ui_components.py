#!/usr/bin/env python3
"""
UI Components - 共通UIコンポーネント
再利用可能なTextual UIウィジェット
"""

from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, Input, Label, Select
from textual.app import ComposeResult
from datetime import datetime
from typing import List, Tuple, Optional, Callable
import sys

try:
    from .localization import LocalizationManager
    from .port_utils import detect_available_ports, get_platform_default_port, format_port_list
except ImportError:
    # 単体実行時の絶対インポート
    from common.localization import LocalizationManager
    from common.port_utils import detect_available_ports, get_platform_default_port, format_port_list


class SerialStats(Static):
    """統計情報表示ウィジェット"""
    
    def __init__(self, localization: Optional[LocalizationManager] = None, **kwargs):
        super().__init__(**kwargs)
        self.loc = localization or LocalizationManager()
        self.rx_count = 0
        self.tx_count = 0
        self.rx_bytes = 0
        self.tx_bytes = 0
        self.start_time = datetime.now()
        self.update_display()
    
    def update_stats(self, direction: str, byte_count: int):
        """統計を更新"""
        if direction == "RX":
            self.rx_count += 1
            self.rx_bytes += byte_count
        elif direction == "TX":
            self.tx_count += 1
            self.tx_bytes += byte_count
        self.update_display()
    
    def reset_stats(self):
        """統計をリセット"""
        self.rx_count = 0
        self.tx_count = 0
        self.rx_bytes = 0
        self.tx_bytes = 0
        self.start_time = datetime.now()
        self.update_display()
    
    def update_display(self):
        """表示を更新"""
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        rate = self.rx_count / max(elapsed.total_seconds(), 1)
        
        content = f"""{self.loc.get('statistics')}
━━━━━━━━━━━━━━━━
{self.loc.get('stats_received', f"{self.rx_count:,}", f"{self.rx_bytes:,}")}
{self.loc.get('stats_sent', f"{self.tx_count:,}", f"{self.tx_bytes:,}")}
{self.loc.get('stats_time', elapsed_str)}
{self.loc.get('stats_rate', rate)}"""
        
        self.update(content)


class SendPanel(Container):
    """データ送信パネル"""
    
    def __init__(self, localization: Optional[LocalizationManager] = None, **kwargs):
        super().__init__(**kwargs)
        self.loc = localization or LocalizationManager()
    
    def compose(self) -> ComposeResult:
        yield Label(self.loc.get("data_send"), classes="panel-title")
        yield Input(
            placeholder=self.loc.get("send_placeholder"), 
            id="send_input"
        )
        with Horizontal(classes="button-row"):
            yield Button(self.loc.get("send"), id="send_btn", variant="primary")
            yield Button(self.loc.get("clear"), id="clear_btn", variant="default")


class ConnectionPanel(Container):
    """接続制御パネル（基本版）"""
    
    def __init__(self, 
                 localization: Optional[LocalizationManager] = None,
                 use_select: bool = False,
                 **kwargs):
        super().__init__(**kwargs)
        self.loc = localization or LocalizationManager()
        self.use_select = use_select
    
    def compose(self) -> ComposeResult:
        yield Label(self.loc.get("port_control"), classes="panel-title")
        
        if self.use_select:
            # Selectウィジェットを使用
            yield self._create_port_select()
        else:
            # 手動入力を使用
            yield self._create_port_input()
        
        with Horizontal(classes="button-row"):
            yield Button(self.loc.get("connect"), id="connect_btn", variant="success")
            yield Button(self.loc.get("disconnect"), id="disconnect_btn", variant="error", disabled=True)
        
        with Horizontal(classes="button-row"):
            yield Button(self.loc.get("detect_ports"), id="detect_ports_btn", variant="default")
            yield Button(self.loc.get("preset"), id="preset_btn", variant="default")
    
    def _create_port_select(self) -> Select:
        """ポート選択ウィジェット作成"""
        ports = detect_available_ports()
        options = [(port, f"{port} - {desc[:30]}") for port, desc in ports]
        
        return Select(
            options,
            prompt=self.loc.get("select_port"),
            id="port_select"
        )
    
    def _create_port_input(self) -> Input:
        """ポート入力ウィジェット作成"""
        default_port = get_platform_default_port()
        
        return Input(
            placeholder=self.loc.get("port_placeholder", default_port),
            id="port_input",
            value=default_port
        )


class EnhancedConnectionPanel(ConnectionPanel):
    """拡張接続制御パネル（ポート検出付き）"""
    
    def __init__(self, 
                 localization: Optional[LocalizationManager] = None,
                 use_select: bool = True,
                 **kwargs):
        super().__init__(localization, use_select, **kwargs)
    
    def compose(self) -> ComposeResult:
        yield Label(self.loc.get("port_control"), classes="panel-title")
        
        if self.use_select:
            yield self._create_port_select()
        else:
            yield self._create_port_input()
        
        # 接続ボタン
        with Horizontal(classes="button-row"):
            yield Button(self.loc.get("connect"), id="connect_btn", variant="success")
            yield Button(self.loc.get("disconnect"), id="disconnect_btn", variant="error", disabled=True)
        
        # 制御ボタン
        with Horizontal(classes="button-row"):
            yield Button(self.loc.get("detect_ports"), id="detect_ports_btn", variant="default")
            yield Button(self.loc.get("preset"), id="preset_btn", variant="default")
        
        # ポート情報表示
        yield PortInfoPanel(self.loc)


class PortInfoPanel(Static):
    """ポート情報表示パネル"""
    
    def __init__(self, localization: Optional[LocalizationManager] = None, **kwargs):
        super().__init__(**kwargs)
        self.loc = localization or LocalizationManager()
        self.update_port_list()
    
    def update_port_list(self):
        """ポート一覧を更新"""
        ports = detect_available_ports()
        content = format_port_list(ports, max_items=8)
        self.update(content)


class DualPortConnectionPanel(Container):
    """デュアルポート接続パネル"""
    
    def __init__(self, localization: Optional[LocalizationManager] = None, **kwargs):
        super().__init__(**kwargs)
        self.loc = localization or LocalizationManager()
    
    def compose(self) -> ComposeResult:
        yield Label(self.loc.get("port_control"), classes="panel-title")
        
        # 受信ポート
        with Horizontal():
            yield Label("📥 RX:")
            yield Input(
                placeholder=self.loc.get("port_placeholder", "/dev/ttyS0"),
                id="rx_port_input",
                value=get_platform_default_port()
            )
        
        # 送信ポート
        with Horizontal():
            yield Label("📤 TX:")
            yield Input(
                placeholder=self.loc.get("port_placeholder", "/dev/ttyS1"),
                id="tx_port_input",
                value=get_platform_default_port()
            )
        
        # 接続ボタン
        with Horizontal(classes="button-row"):
            yield Button(self.loc.get("connect"), id="connect_btn", variant="success")
            yield Button(self.loc.get("disconnect"), id="disconnect_btn", variant="error", disabled=True)
        
        # 制御ボタン
        with Horizontal(classes="button-row"):
            yield Button(self.loc.get("detect_ports"), id="detect_ports_btn", variant="default")
            yield Button("RX/TX 同期", id="sync_ports_btn", variant="default")


class ConfigPanel(Container):
    """設定パネル"""
    
    def __init__(self, localization: Optional[LocalizationManager] = None, **kwargs):
        super().__init__(**kwargs)
        self.loc = localization or LocalizationManager()
    
    def on_mount(self) -> None:
        """マウント時にデフォルト値を設定"""
        try:
            self.query_one("#baudrate_select", Select).value = "9600"
            self.query_one("#databits_select", Select).value = "8"
            self.query_one("#parity_select", Select).value = "N"
            self.query_one("#stopbits_select", Select).value = "1"
        except Exception:
            # ウィジェットがまだ利用できない場合は無視
            pass
    
    def compose(self) -> ComposeResult:
        yield Label("⚙️ 設定", classes="panel-title")
        
        # ボーレート選択
        with Horizontal():
            yield Label("Baud:")
            yield Select(
                [("9600", "9600"), ("19200", "19200"), ("38400", "38400"), 
                 ("57600", "57600"), ("115200", "115200")],
                id="baudrate_select"
            )
        
        # データビット
        with Horizontal():
            yield Label("Data:")
            yield Select(
                [("8", "8"), ("7", "7"), ("6", "6"), ("5", "5")],
                id="databits_select"
            )
        
        # パリティ
        with Horizontal():
            yield Label("Parity:")
            yield Select(
                [("N", "None"), ("E", "Even"), ("O", "Odd")],
                id="parity_select"
            )
        
        # ストップビット
        with Horizontal():
            yield Label("Stop:")
            yield Select(
                [("1", "1"), ("2", "2")],
                id="stopbits_select"
            )
        
        # 設定ボタン
        with Horizontal(classes="button-row"):
            yield Button("設定適用", id="apply_config_btn", variant="primary")
            yield Button("デフォルト", id="default_config_btn", variant="default")


class StatusBar(Static):
    """ステータスバー"""
    
    def __init__(self, localization: Optional[LocalizationManager] = None, **kwargs):
        super().__init__(**kwargs)
        self.loc = localization or LocalizationManager()
        self.connected = False
        self.port = ""
        self.update_status()
    
    def set_connection_status(self, connected: bool, port: str = ""):
        """接続状態を更新"""
        self.connected = connected
        self.port = port
        self.update_status()
    
    def update_status(self):
        """ステータス表示を更新"""
        if self.connected:
            status = f"✅ Connected to {self.port}"
            style = "green"
        else:
            status = "❌ Disconnected"
            style = "red"
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        content = f"[{style}]{status}[/] | {timestamp} | {sys.platform}"
        self.update(content)


class LogPanel(Container):
    """ログ表示パネル"""
    
    def __init__(self, 
                 localization: Optional[LocalizationManager] = None,
                 max_lines: int = 100,
                 **kwargs):
        super().__init__(**kwargs)
        self.loc = localization or LocalizationManager()
        self.max_lines = max_lines
        self.log_lines = []
    
    def compose(self) -> ComposeResult:
        yield Label("📝 ログ", classes="panel-title")
        yield Static("", id="log_content")
    
    def add_log(self, message: str, level: str = "INFO"):
        """ログメッセージを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        self.log_lines.append(log_entry)
        
        # 最大行数を超えた場合は古いものを削除
        if len(self.log_lines) > self.max_lines:
            self.log_lines.pop(0)
        
        # 表示更新
        content = "\n".join(self.log_lines)
        log_static = self.query_one("#log_content", Static)
        log_static.update(content)
    
    def clear_log(self):
        """ログをクリア"""
        self.log_lines.clear()
        log_static = self.query_one("#log_content", Static)
        log_static.update("")


if __name__ == "__main__":
    """テスト用簡易アプリ"""
    from textual.app import App
    from textual.widgets import Header, Footer
    
    class TestApp(App):
        """テストアプリケーション"""
        
        CSS = """
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
        """
        
        def compose(self) -> ComposeResult:
            yield Header()
            
            with Horizontal():
                with Vertical():
                    yield EnhancedConnectionPanel()
                    yield SendPanel()
                    yield SerialStats()
                
                with Vertical():
                    yield ConfigPanel()
                    yield LogPanel()
            
            yield StatusBar()
            yield Footer()
    
    # テスト実行
    if __name__ == "__main__":
        app = TestApp()
        app.run()