#!/usr/bin/env python3
"""
Ultra Compact Dual Port Serial Communication Dashboard
最小画面用超コンパクト版（修正済み）
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    DataTable, Header, Footer, Static, 
    Button, Input, Label, RichLog, Checkbox
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
        if sys.platform == "win32":
            for i in range(1, 21):
                ports.append((f"COM{i}", f"COM Port {i}"))
        else:
            patterns = ['/dev/ttyS*', '/dev/ttyUSB*', '/dev/ttyACM*']
            for pattern in patterns:
                for device in glob.glob(pattern):
                    if os.path.exists(device):
                        ports.append((device, f"Serial Device {os.path.basename(device)}"))
    
    ports.append(("loop://", "Loop back"))
    return ports

class UltraCompactDashboard(App):
    """ウルトラコンパクト版ダッシュボード（修正済み）"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #control_bar {
        height: 6;
        layout: vertical;
        border: solid $primary;
        padding: 0 1;
        margin: 0;
    }
    
    #main_content {
        height: 1fr;
        layout: horizontal;
    }
    
    #data_table {
        width: 70%;
        height: 100%;
        border: solid $primary;
    }
    
    #log_view {
        width: 30%;
        height: 100%;
        border: solid $secondary;
        overflow-y: scroll;
    }
    
    #status_bar {
        height: 2;
        border: solid $accent;
        padding: 0 1;
    }
    
    .control-row {
        height: 2;
        align: center middle;
        margin: 0;
    }
    
    .ultra-input {
        width: 12;
        margin: 0 1;
    }
    
    .ultra-btn {
        margin: 0 1;
        min-width: 6;
    }
    
    .ultra-label {
        width: 4;
        text-align: right;
        margin: 0;
    }
    
    .ultra-checkbox {
        margin: 0 1;
    }
    
    #tx_row {
        display: none;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "clear_data", "Clear", show=True),
        Binding("s", "save_data", "Save", show=True),
        Binding("t", "toggle_dual_port", "Toggle", show=True),
        Binding("d", "detect_ports", "Detect", show=True),
    ]
    
    TITLE = "📡 Ultra Compact Dashboard"
    SUB_TITLE = "Fixed connection method"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rx_serial_comm = None
        self.tx_serial_comm = None
        self.data_buffer = []
        self.connected = False
        self.dual_port_mode = False
        self.rx_count = 0
        self.tx_count = 0
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        # コントロールバー（超コンパクト）
        with Container(id="control_bar"):
            # 1行目: RXポート + 接続ボタン
            with Horizontal(classes="control-row"):
                yield Label("RX:", classes="ultra-label")
                yield Input(
                    value="COM2" if sys.platform == "win32" else "/dev/ttyS0", 
                    id="rx_port_input", 
                    classes="ultra-input"
                )
                yield Checkbox("分離", id="separate_ports_checkbox", classes="ultra-checkbox")
                yield Button("接続", id="connect_btn", variant="success", classes="ultra-btn")
                yield Button("切断", id="disconnect_btn", variant="error", disabled=True, classes="ultra-btn")
                yield Button("検出", id="detect_ports_btn", variant="default", classes="ultra-btn")
            
            # 2行目: TXポート + 送信（初期非表示）
            with Horizontal(classes="control-row", id="tx_row"):
                yield Label("TX:", classes="ultra-label")
                yield Input(
                    value="COM4" if sys.platform == "win32" else "/dev/ttyS1", 
                    id="tx_port_input", 
                    classes="ultra-input"
                )
                yield Input(placeholder="送信データ...", id="send_input", classes="ultra-input")
                yield Button("送信", id="send_btn", variant="primary", classes="ultra-btn")
        
        # メインコンテンツ
        with Horizontal(id="main_content"):
            yield DataTable(id="data_table")
            yield RichLog(id="log_view", highlight=True)
        
        # ステータスバー
        yield Static("🔴 未接続 | 📥0 📤0", id="status_bar")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """アプリ起動時の初期化"""
        # データテーブル初期化
        table = self.query_one("#data_table", DataTable)
        table.add_columns("時刻", "方向", "データ")
        table.cursor_type = "row"
        
        # ログ初期化
        log = self.query_one("#log_view", RichLog)
        log.write("📡 Ultra Compact Dashboard (Fixed)\n")
        log.write("🔧 接続方式を修正済み\n")
        log.write("💡 t:分離切替 d:検出\n")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """チェックボックス変更時の処理"""
        if event.checkbox.id == "separate_ports_checkbox":
            self.dual_port_mode = event.value
            self.update_port_visibility(event.value)
            self.log_message(f"分離: {'ON' if event.value else 'OFF'}")
    
    def update_port_visibility(self, show_tx_port: bool):
        """送信ポート行の表示/非表示"""
        tx_row = self.query_one("#tx_row", Horizontal)
        
        if show_tx_port:
            tx_row.styles.display = "block"
        else:
            tx_row.styles.display = "none"
    
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
        elif button_id == "send_btn":
            await self.send_data()
    
    def action_detect_ports(self) -> None:
        """ポート検出アクション"""
        ports = detect_available_ports()
        self.log_message(f"検出: {len(ports)}個")
        for port, _ in ports[:3]:
            self.log_message(f"  {port}")
    
    async def connect_serial(self):
        """シリアル接続（動作確認済み方式）"""
        rx_port = self.query_one("#rx_port_input", Input).value.strip()
        
        if not rx_port:
            self.log_message("❌ RXポート未入力")
            return
        
        try:
            # プラットフォーム別設定ファイル選択
            if sys.platform == "win32":
                config_file = "serial_config_windows.ini"
            else:
                config_file = "serial_config_linux.ini"
            
            # simple_dashboard.py と同じ方式（動作確認済み）
            if not os.path.exists(config_file):
                self.log_message(f"⚠️ {config_file} が見つかりません。手動設定を使用")
                config = SerialConfig()
                config.config.set('SERIAL', 'port', rx_port)
                config.config.set('SERIAL', 'baudrate', '9600')
                
                self.rx_serial_comm = ModernSerialComm()
                self.rx_serial_comm.config_manager = config
                self.rx_serial_comm._load_settings_from_config()
            else:
                # 設定ファイル使用
                self.rx_serial_comm = ModernSerialComm(config_file)
                self.rx_serial_comm.config_manager.config.set('SERIAL', 'port', rx_port)
                self.rx_serial_comm._load_settings_from_config()
            
            self.rx_serial_comm.set_receive_callback(self.on_data_received)
            
            if not await self.rx_serial_comm.connect():
                self.log_message(f"❌ RX {rx_port} 失敗")
                return
            
            self.log_message(f"✅ RX {rx_port}")
            
            # デュアルポートモードの場合
            if self.dual_port_mode:
                tx_port = self.query_one("#tx_port_input", Input).value.strip()
                
                if not tx_port:
                    self.log_message("❌ TXポート未入力")
                    await self.rx_serial_comm.disconnect()
                    return
                
                if tx_port != rx_port:
                    # 送信用接続（同じ方式）
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
                    
                    if await self.tx_serial_comm.connect():
                        self.log_message(f"✅ TX {tx_port}")
                    else:
                        self.log_message(f"❌ TX {tx_port} 失敗")
                        await self.rx_serial_comm.disconnect()
                        return
                else:
                    self.tx_serial_comm = self.rx_serial_comm
                    self.log_message(f"📍 TX=RX {tx_port}")
            else:
                self.tx_serial_comm = self.rx_serial_comm
                tx_port = rx_port
            
            self.connected = True
            
            # ボタン状態更新
            self.query_one("#connect_btn", Button).disabled = True
            self.query_one("#disconnect_btn", Button).disabled = False
            
            # ステータス更新
            self.update_status()
            
        except Exception as e:
            self.log_message(f"❌ エラー: {str(e)[:20]}...")
    
    # 以下のメソッドは元のコードと同じ
    async def disconnect_serial(self):
        """シリアル切断"""
        if self.connected:
            if self.rx_serial_comm:
                await self.rx_serial_comm.disconnect()
            
            if self.tx_serial_comm and self.tx_serial_comm != self.rx_serial_comm:
                await self.tx_serial_comm.disconnect()
            
            self.rx_serial_comm = None
            self.tx_serial_comm = None
            self.connected = False
            
            # ボタン状態更新
            self.query_one("#connect_btn", Button).disabled = False
            self.query_one("#disconnect_btn", Button).disabled = True
            
            self.update_status()
            self.log_message("🔌 切断完了")
    
    async def send_data(self):
        """データ送信"""
        if not self.connected or not self.tx_serial_comm:
            self.log_message("❌ TX未接続")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            return
        
        if not data.endswith(('\r\n', '\r', '\n')):
            data += '\r\n'
        
        if await self.tx_serial_comm.send_string(data):
            self.log_message(f"📤 {data.strip()}")
            send_input.value = ""
            self.tx_count += 1
            self.add_to_data_table("TX", data.strip())
            self.update_status()
        else:
            self.log_message("❌ 送信失敗")
    
    def on_data_received(self, data: bytes, direction: str):
        """データ受信処理"""
        self.call_later(self._handle_received_data, data, direction)
    
    def _handle_received_data(self, data: bytes, direction: str):
        """データ受信処理（UIスレッド）"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if direction == "RX":
                self.log_message(f"📥 {data_str}")
                self.add_to_data_table("RX", data_str)
                self.rx_count += 1
                self.update_status()
        except Exception as e:
            self.log_message(f"❌ 処理エラー")
    
    def add_to_data_table(self, direction: str, data: str):
        """データテーブルに行追加"""
        table = self.query_one("#data_table", DataTable)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        display_data = data[:25] + "..." if len(data) > 25 else data
        dir_display = "📥" if direction == "RX" else "📤"
        
        table.add_row(timestamp, dir_display, display_data)
        
        self.data_buffer.append({
            'timestamp': datetime.now(),
            'direction': direction,
            'data': data
        })
        
        if table.row_count > 100:  # 省メモリ
            table.remove_row(0)
    
    def update_status(self):
        """ステータスバー更新"""
        status = self.query_one("#status_bar", Static)
        
        if self.connected:
            if self.dual_port_mode and self.rx_serial_comm and self.tx_serial_comm:
                rx_port = self.rx_serial_comm.port
                tx_port = self.tx_serial_comm.port
                if rx_port == tx_port:
                    status_text = f"🟢 {rx_port} | 📥{self.rx_count} 📤{self.tx_count}"
                else:
                    status_text = f"🟢 RX:{rx_port} TX:{tx_port} | 📥{self.rx_count} 📤{self.tx_count}"
            else:
                port = self.rx_serial_comm.port if self.rx_serial_comm else "?"
                status_text = f"🟢 {port} | 📥{self.rx_count} 📤{self.tx_count}"
        else:
            status_text = f"🔴 未接続 | 📥{self.rx_count} 📤{self.tx_count}"
        
        status.update(status_text)
    
    def log_message(self, message: str):
        """ログメッセージ出力"""
        log = self.query_one("#log_view", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")
    
    def action_clear_data(self) -> None:
        """データクリア"""
        table = self.query_one("#data_table", DataTable)
        table.clear()
        self.data_buffer.clear()
        self.rx_count = 0
        self.tx_count = 0
        self.update_status()
        self.log_message("🗑️ クリア完了")
    
    def action_save_data(self) -> None:
        """CSV保存"""
        if not self.data_buffer:
            self.log_message("💾 データなし")
            return
        
        import csv
        filename = f"serial_data_{datetime.now().strftime('%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'direction', 'data'])
                
                for entry in self.data_buffer:
                    writer.writerow([
                        entry['timestamp'].isoformat(),
                        entry['direction'],
                        entry['data']
                    ])
            
            self.log_message(f"💾 {filename} 保存({len(self.data_buffer)})")
        except Exception as e:
            self.log_message(f"❌ 保存失敗")
    
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
    
    app = UltraCompactDashboard()
    app.run()

if __name__ == "__main__":
    main()
