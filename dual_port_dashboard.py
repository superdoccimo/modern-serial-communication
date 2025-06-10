#!/usr/bin/env python3
"""
Dual Port Serial Communication Dashboard
送信ポート・受信ポート分離対応版
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    DataTable, Header, Footer, Static, 
    Button, Input, Label, RichLog, Sparkline, Checkbox
)
from textual.binding import Binding
import asyncio
import sys
import glob
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# ライブラリインポート
try:
    from modern_serial_comm import ModernSerialComm, SerialConfig
except ImportError:
    print("Error: modern_serial_comm.py が見つかりません")
    sys.exit(1)


def detect_available_ports() -> List[tuple]:
    """利用可能なシリアルポートを検出"""
    ports = []
    
    try:
        import serial.tools.list_ports
        for port in serial.tools.list_ports.comports():
            ports.append((port.device, port.description or "Unknown"))
    except ImportError:
        # 手動検出
        if sys.platform == "win32":
            for i in range(1, 21):
                ports.append((f"COM{i}", f"COM Port {i}"))
        else:
            patterns = ['/dev/ttyS*', '/dev/ttyUSB*', '/dev/ttyACM*']
            for pattern in patterns:
                for device in glob.glob(pattern):
                    if os.path.exists(device):
                        ports.append((device, f"Serial Device {os.path.basename(device)}"))
    
    # テスト用追加
    ports.append(("loop://", "Loop back (テスト用)"))
    return ports


class DualPortConnectionPanel(Container):
    """送受信ポート分離対応接続パネル"""
    
    def compose(self) -> ComposeResult:
        yield Label("🔌 接続設定", classes="panel-title")
        
        # プラットフォーム別デフォルトポート
        if sys.platform == "win32":
            default_rx_port = "COM2"
            default_tx_port = "COM1"
        else:
            default_rx_port = "/dev/ttyS0"
            default_tx_port = "/dev/ttyS0"
        
        # 受信ポート設定
        yield Label("📥 受信ポート:", classes="port-label")
        yield Input(
            placeholder=f"受信用 (例: {default_rx_port})", 
            id="rx_port_input", 
            value=default_rx_port
        )
        
        # 送受信分離チェックボックス
        yield Checkbox("送受信ポートを分離", id="separate_ports_checkbox")
        
        # 送信ポート設定（初期は非表示）
        yield Label("📤 送信ポート:", classes="port-label", id="tx_port_label")
        yield Input(
            placeholder=f"送信用 (例: {default_tx_port})", 
            id="tx_port_input", 
            value=default_tx_port
        )
        
        # 接続ボタン
        with Horizontal(classes="button-row"):
            yield Button("接続", id="connect_btn", variant="success")
            yield Button("切断", id="disconnect_btn", variant="error", disabled=True)
        
        # 操作ボタン
        with Horizontal(classes="button-row"):
            yield Button("ポート検出", id="detect_ports_btn", variant="default")
            yield Button("設定値", id="preset_btn", variant="default")


class ConnectionStatus(Static):
    """接続状態表示ウィジェット"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_status(False, None, None)
    
    def update_status(self, connected: bool, rx_port: Optional[str], tx_port: Optional[str]):
        """接続状態更新"""
        if connected:
            if rx_port == tx_port:
                content = f"""🔗 接続状態: ✅ 接続中
━━━━━━━━━━━━━━━━
📍 ポート: {rx_port}
📊 モード: 単一ポート
🔄 双方向通信"""
            else:
                content = f"""🔗 接続状態: ✅ 接続中
━━━━━━━━━━━━━━━━
📥 受信: {rx_port}
📤 送信: {tx_port}
📊 モード: デュアルポート
🔄 分離通信"""
        else:
            content = """🔗 接続状態: ❌ 未接続
━━━━━━━━━━━━━━━━
📍 ポート: なし
📊 モード: 待機中
🔄 通信停止"""
        
        self.update(content)


class SendPanel(Container):
    """データ送信パネル"""
    
    def compose(self) -> ComposeResult:
        yield Label("📤 データ送信", classes="panel-title")
        yield Input(placeholder="送信データを入力...", id="send_input")
        with Horizontal(classes="button-row"):
            yield Button("送信", id="send_btn", variant="primary")
            yield Button("クリア", id="clear_btn", variant="default")


class SerialStats(Static):
    """統計情報表示ウィジェット"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rx_count = 0
        self.tx_count = 0
        self.rx_bytes = 0
        self.tx_bytes = 0
        self.start_time = datetime.now()
        self.update_display()
    
    def update_stats(self, direction: str, byte_count: int):
        if direction == "RX":
            self.rx_count += 1
            self.rx_bytes += byte_count
        elif direction == "TX":
            self.tx_count += 1
            self.tx_bytes += byte_count
        self.update_display()
    
    def update_display(self):
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        rate = self.rx_count / max(elapsed.total_seconds(), 1)
        
        content = f"""📊 統計情報
━━━━━━━━━━━━━━━━
📥 受信: {self.rx_count:,} ({self.rx_bytes:,} B)
📤 送信: {self.tx_count:,} ({self.tx_bytes:,} B)
⏱️  時間: {elapsed_str}
📈 速度: {rate:.1f} pkt/s"""
        
        self.update(content)


class DualPortDashboard(App):
    """送受信ポート分離対応ダッシュボード"""
    
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
        margin: 0;
    }
    
    .port-label {
        margin: 0;
        color: $text;
    }
    
    .button-row {
        height: 3;
        align: center middle;
        margin: 0;
    }
    
    Button {
        margin: 0 1;
    }
    
    #connection_panel {
        height: 35%;
        border: solid $success;
        padding: 1;
        margin-bottom: 1;
        overflow-y: auto;
    }
    
    #send_panel {
        height: 20%;
        border: solid $warning;
        padding: 1;
        margin-bottom: 1;
        overflow-y: auto;
    }
    
    #stats_panel {
        height: 25%;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
        overflow-y: auto;
    }
    
    #status_panel {
        height: 20%;
        border: solid $primary;
        padding: 1;
        overflow-y: auto;
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
    
    Checkbox {
        margin: 1 0;
    }
    
    #tx_port_label {
        display: none;
    }
    
    #tx_port_input {
        display: none;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "clear_data", "Clear Data", show=True),
        Binding("s", "save_data", "Save CSV", show=True),
        Binding("d", "detect_ports", "Detect Ports", show=True),
        Binding("t", "toggle_dual_port", "Toggle Dual Port", show=True),
    ]
    
    TITLE = "📡 Dual Port Serial Dashboard"
    SUB_TITLE = "Send/Receive port separation support"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rx_serial_comm = None  # 受信用
        self.tx_serial_comm = None  # 送信用
        self.data_buffer = []
        self.sparkline_data = []
        self.connected = False
        self.dual_port_mode = False
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            # 左側パネル
            with Vertical(id="left_panel"):
                yield DualPortConnectionPanel(id="connection_panel")
                yield SendPanel(id="send_panel")
                yield SerialStats(id="stats_panel")
                yield ConnectionStatus(id="status_panel")
            
            # 右側メインエリア
            with Vertical(id="main_area"):
                yield DataTable(id="data_table")
                yield Sparkline(id="sparkline", data=[], summary_function=max)
                yield RichLog(id="log_view", highlight=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """アプリ起動時の初期化"""
        # データテーブル初期化
        table = self.query_one("#data_table", DataTable)
        table.add_columns("時刻", "方向", "データ", "長さ", "ポート")
        table.cursor_type = "row"
        
        # ログ初期化
        log = self.query_one("#log_view", RichLog)
        log.write("📡 Dual Port Serial Dashboard 起動完了\n")
        log.write("💡 チェックボックスで送受信ポート分離が可能です\n")
        log.write("🔧 't'でデュアルポート切り替え、'd'でポート検出\n")
        
        # 初期状態設定
        self.update_port_visibility(False)
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """チェックボックス変更時の処理"""
        if event.checkbox.id == "separate_ports_checkbox":
            self.dual_port_mode = event.value
            self.update_port_visibility(event.value)
            self.log_message(f"🔄 デュアルポートモード: {'有効' if event.value else '無効'}")
    
    def update_port_visibility(self, show_tx_port: bool):
        """送信ポート入力欄の表示/非表示"""
        tx_label = self.query_one("#tx_port_label", Label)
        tx_input = self.query_one("#tx_port_input", Input)
        
        if show_tx_port:
            tx_label.styles.display = "block"
            tx_input.styles.display = "block"
        else:
            tx_label.styles.display = "none"
            tx_input.styles.display = "none"
    
    def action_toggle_dual_port(self) -> None:
        """デュアルポートモード切り替え"""
        checkbox = self.query_one("#separate_ports_checkbox", Checkbox)
        checkbox.value = not checkbox.value
        self.dual_port_mode = checkbox.value
        self.update_port_visibility(checkbox.value)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタンクリック処理"""
        button_id = event.button.id
        
        if button_id == "connect_btn":
            await self.connect_serial()
        elif button_id == "disconnect_btn":
            await self.disconnect_serial()
        elif button_id == "detect_ports_btn":
            self.action_detect_ports()
        elif button_id == "preset_btn":
            self.set_preset_port()
        elif button_id == "send_btn":
            await self.send_data()
        elif button_id == "clear_btn":
            self.query_one("#send_input", Input).value = ""
    
    def action_detect_ports(self) -> None:
        """ポート検出アクション"""
        self.log_message("🔍 ポート検出中...")
        ports = detect_available_ports()
        self.log_message(f"🔌 {len(ports)} 個のポートを検出しました")
        
        for port, desc in ports[:8]:  # 最初の8つをログに
            self.log_message(f"   • {port} - {desc}")
    
    def set_preset_port(self) -> None:
        """プリセットポート設定"""
        # プラットフォーム別推奨ポート
        if sys.platform == "win32":
            rx_preset = "COM2"
            tx_preset = "COM1"
        else:
            rx_preset = "/dev/ttyS0"
            tx_preset = "/dev/ttyS1"
        
        rx_input = self.query_one("#rx_port_input", Input)
        tx_input = self.query_one("#tx_port_input", Input)
        
        rx_input.value = rx_preset
        tx_input.value = tx_preset
        
        self.log_message(f"🎯 プリセット設定 - 受信: {rx_preset}, 送信: {tx_preset}")
    
    async def connect_serial(self):
        """シリアル接続"""
        rx_port = self.query_one("#rx_port_input", Input).value.strip()
        
        if not rx_port:
            self.log_message("❌ 受信ポートを入力してください")
            return
        
        try:
            # プラットフォーム別設定ファイル選択
            if sys.platform == "win32":
                config_file = "serial_config_windows.ini"
            else:
                config_file = "serial_config_linux.ini"
            
            # 受信用接続作成
            if not os.path.exists(config_file):
                self.log_message(f"⚠️ {config_file} が見つかりません。手動設定を使用します")
                rx_config = SerialConfig()
                rx_config.config.set('SERIAL', 'port', rx_port)
                rx_config.config.set('SERIAL', 'baudrate', '9600')
                
                self.rx_serial_comm = ModernSerialComm()
                self.rx_serial_comm.config_manager = rx_config
                self.rx_serial_comm._load_settings_from_config()
            else:
                self.rx_serial_comm = ModernSerialComm(config_file)
                self.rx_serial_comm.config_manager.config.set('SERIAL', 'port', rx_port)
                self.rx_serial_comm._load_settings_from_config()
            
            # 受信コールバック設定
            self.rx_serial_comm.set_receive_callback(self.on_data_received)
            
            # 受信接続試行
            if not await self.rx_serial_comm.connect():
                self.log_message(f"❌ 受信ポート {rx_port} への接続に失敗しました")
                return
            
            self.log_message(f"✅ 受信ポート {rx_port} に接続しました")
            
            # デュアルポートモードの場合、送信用も接続
            if self.dual_port_mode:
                tx_port = self.query_one("#tx_port_input", Input).value.strip()
                
                if not tx_port:
                    self.log_message("❌ 送信ポートを入力してください")
                    await self.rx_serial_comm.disconnect()
                    return
                
                if tx_port != rx_port:
                    # 送信用接続作成
                    if not os.path.exists(config_file):
                        tx_config = SerialConfig()
                        tx_config.config.set('SERIAL', 'port', tx_port)
                        tx_config.config.set('SERIAL', 'baudrate', '9600')
                        
                        self.tx_serial_comm = ModernSerialComm()
                        self.tx_serial_comm.config_manager = tx_config
                        self.tx_serial_comm._load_settings_from_config()
                    else:
                        self.tx_serial_comm = ModernSerialComm(config_file)
                        self.tx_serial_comm.config_manager.config.set('SERIAL', 'port', tx_port)
                        self.tx_serial_comm._load_settings_from_config()
                    
                    # 送信接続試行
                    if await self.tx_serial_comm.connect():
                        self.log_message(f"✅ 送信ポート {tx_port} に接続しました")
                    else:
                        self.log_message(f"❌ 送信ポート {tx_port} への接続に失敗しました")
                        await self.rx_serial_comm.disconnect()
                        return
                else:
                    # 同じポートの場合は受信用を送信にも使用
                    self.tx_serial_comm = self.rx_serial_comm
                    self.log_message(f"📍 送受信に同じポート {tx_port} を使用します")
            else:
                # シングルポートモードの場合
                self.tx_serial_comm = self.rx_serial_comm
                tx_port = rx_port
            
            self.connected = True
            
            # ボタン状態更新
            self.query_one("#connect_btn", Button).disabled = True
            self.query_one("#disconnect_btn", Button).disabled = False
            
            # 接続状態更新
            status = self.query_one("#status_panel", ConnectionStatus)
            status.update_status(True, rx_port, tx_port if self.dual_port_mode else rx_port)
            
        except Exception as e:
            self.log_message(f"❌ 接続エラー: {str(e)}")
    
    async def disconnect_serial(self):
        """シリアル切断"""
        if self.connected:
            if self.rx_serial_comm:
                await self.rx_serial_comm.disconnect()
                self.log_message("🔌 受信ポートを切断しました")
            
            if self.tx_serial_comm and self.tx_serial_comm != self.rx_serial_comm:
                await self.tx_serial_comm.disconnect()
                self.log_message("🔌 送信ポートを切断しました")
            
            self.rx_serial_comm = None
            self.tx_serial_comm = None
            self.connected = False
            
            # ボタン状態更新
            self.query_one("#connect_btn", Button).disabled = False
            self.query_one("#disconnect_btn", Button).disabled = True
            
            # 接続状態更新
            status = self.query_one("#status_panel", ConnectionStatus)
            status.update_status(False, None, None)
    
    async def send_data(self):
        """データ送信"""
        if not self.connected or not self.tx_serial_comm:
            self.log_message("❌ 送信ポートが接続されていません")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            return
        
        # 改行コード追加
        if not data.endswith(('\r\n', '\r', '\n')):
            data += '\r\n'
        
        if await self.tx_serial_comm.send_string(data):
            tx_port = self.tx_serial_comm.port
            self.log_message(f"📤 送信 ({tx_port}): {data.strip()}")
            send_input.value = ""
            
            # 統計更新
            stats = self.query_one("#stats_panel", SerialStats)
            stats.update_stats("TX", len(data.encode()))
            
            # データテーブルに追加
            self.add_to_data_table("TX", data.strip(), len(data.encode()), tx_port)
        else:
            self.log_message("❌ 送信に失敗しました")
    
    def on_data_received(self, data: bytes, direction: str):
        """データ受信処理"""
        self.call_later(self._handle_received_data, data, direction)
    
    def _handle_received_data(self, data: bytes, direction: str):
        """データ受信処理（UIスレッド）"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if direction == "RX":
                rx_port = self.rx_serial_comm.port if self.rx_serial_comm else "unknown"
                self.log_message(f"📥 受信 ({rx_port}): {data_str}")
                self.add_to_data_table("RX", data_str, len(data), rx_port)
                
                stats = self.query_one("#stats_panel", SerialStats)
                stats.update_stats("RX", len(data))
                
                self.update_sparkline(len(data))
        except Exception as e:
            self.log_message(f"❌ データ処理エラー: {str(e)}")
    
    def add_to_data_table(self, direction: str, data: str, length: int, port: str):
        """データテーブルに行追加"""
        table = self.query_one("#data_table", DataTable)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        display_data = data[:40] + "..." if len(data) > 40 else data
        dir_display = "📥 RX" if direction == "RX" else "📤 TX"
        
        table.add_row(timestamp, dir_display, display_data, str(length), port)
        
        self.data_buffer.append({
            'timestamp': datetime.now(),
            'direction': direction,
            'data': data,
            'length': length,
            'port': port
        })
        
        if table.row_count > 1000:
            table.remove_row(0)
    
    def update_sparkline(self, data_length: int):
        """スパークライン更新"""
        sparkline = self.query_one("#sparkline", Sparkline)
        self.sparkline_data.append(data_length)
        
        if len(self.sparkline_data) > 100:
            self.sparkline_data.pop(0)
        
        sparkline.data = self.sparkline_data
    
    def log_message(self, message: str):
        """ログメッセージ出力"""
        log = self.query_one("#log_view", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")
    
    def action_clear_data(self) -> None:
        """データクリア"""
        table = self.query_one("#data_table", DataTable)
        table.clear()
        
        sparkline = self.query_one("#sparkline", Sparkline)
        self.sparkline_data.clear()
        sparkline.data = []
        
        self.data_buffer.clear()
        self.log_message("🗑️ データをクリアしました")
    
    def action_save_data(self) -> None:
        """CSV保存"""
        if not self.data_buffer:
            self.log_message("💾 保存するデータがありません")
            return
        
        import csv
        filename = f"serial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'direction', 'data', 'length', 'port'])
                
                for entry in self.data_buffer:
                    writer.writerow([
                        entry['timestamp'].isoformat(),
                        entry['direction'],
                        entry['data'],
                        entry['length'],
                        entry['port']
                    ])
            
            self.log_message(f"💾 {filename} に保存しました ({len(self.data_buffer)} 件)")
        except Exception as e:
            self.log_message(f"❌ 保存エラー: {str(e)}")
    
    async def action_quit(self) -> None:
        """アプリ終了"""
        if self.connected:
            await self.disconnect_serial()
        self.exit()


def main():
    """メイン実行関数"""
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = DualPortDashboard()
    app.run()


if __name__ == "__main__":
    main()
