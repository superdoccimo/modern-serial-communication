#!/usr/bin/env python3
"""
Final Working Dual Port Serial Communication Dashboard
デバッグで確認された動作方式を使用
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


class FinalWorkingDashboard(App):
    """最終動作版デュアルポートダッシュボード"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #header_area {
        height: 18;
        layout: vertical;
        margin: 0;
        border: solid $success;
        padding: 1;
        overflow-y: auto;
    }
    
    #main_area {
        height: 1fr;
        layout: horizontal;
    }
    
    #control_panel {
        width: 35;
        height: 100%;
        layout: vertical;
        border: solid $primary;
        padding: 1;
        margin: 0 1 0 0;
        overflow-y: auto;
    }
    
    #data_area {
        width: 1fr;
        height: 100%;
        layout: vertical;
    }
    
    .input-row {
        height: 3;
        align: center middle;
        margin: 0;
    }
    
    .button-row {
        height: 3;
        align: center middle;
        margin: 1 0;
    }
    
    .send-row {
        height: 3;
        align: center middle;
        margin: 1 0;
    }
    
    .port-label-short {
        width: 6;
        text-align: right;
        margin: 0 1 0 0;
    }
    
    .port-input {
        width: 1fr;
        margin: 0;
    }
    
    .compact-btn {
        margin: 0 1;
        min-width: 6;
    }
    
    .send-input {
        width: 1fr;
        margin: 0 1 0 0;
    }
    
    .send-btn {
        margin: 0;
        min-width: 6;
    }
    
    .compact-checkbox {
        margin: 0;
        height: 3;
    }
    
    #data_table {
        height: 1fr;
        border: solid $primary;
    }
    
    #log_view {
        height: 30%;
        border: solid $secondary;
        overflow-y: scroll;
    }
    
    #status_bar {
        height: 3;
        border: solid $accent;
        padding: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "clear_data", "Clear", show=True),
        Binding("s", "save_data", "Save", show=True),
        Binding("d", "detect_ports", "Detect", show=True),
        Binding("t", "toggle_dual_port", "Toggle", show=True),
    ]
    
    TITLE = "📡 Final Working Dashboard"
    SUB_TITLE = "Confirmed working dual port communication"
    
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
        
        # ヘッダーエリア（接続制御）
        with Container(id="header_area"):
            # 1行目: 受信ポート（常に表示）
            with Horizontal(classes="input-row"):
                yield Label("📥RX:", classes="port-label-short")
                yield Input(
                    value="COM1" if sys.platform == "win32" else "/dev/ttyS0", 
                    id="rx_port_input", 
                    classes="port-input"
                )
            
            # 2行目: 送信ポート（常に表示、初期は無効化）
            with Horizontal(classes="input-row", id="tx_port_row"):
                yield Label("📤TX:", classes="port-label-short")
                yield Input(
                    value="COM2" if sys.platform == "win32" else "/dev/ttyS1", 
                    id="tx_port_input", 
                    classes="port-input",
                    disabled=True  # 初期は無効
                )
            
            # 3行目: チェックボックス
            yield Checkbox("送受信分離", id="separate_ports_checkbox", classes="compact-checkbox")
            
            # 4行目: 接続ボタン（常に表示）
            with Horizontal(classes="button-row"):
                yield Button("接続", id="connect_btn", variant="success", classes="compact-btn")
                yield Button("切断", id="disconnect_btn", variant="error", disabled=True, classes="compact-btn")
                yield Button("検出", id="detect_ports_btn", variant="default", classes="compact-btn")
            
            # 5行目: 送信エリア
            with Horizontal(classes="send-row"):
                yield Input(placeholder="送信データ...", id="send_input", classes="send-input")
                yield Button("送信", id="send_btn", variant="primary", classes="send-btn")
        
        # メインエリア
        with Horizontal(id="main_area"):
            # 左側: 制御パネル
            with Vertical(id="control_panel"):
                yield Label("🎛️ 制御")
                yield Button("クリア", id="clear_data_btn", variant="default")
                yield Button("保存", id="save_data_btn", variant="default")
                yield Label("💡 VMware接続例:")
                yield Label("Win: COM1↔COM2")
                yield Label("Lin: /dev/ttyS0↔/dev/ttyS1")
                yield Label("")
                yield Label("🎮 操作:")
                yield Label("q: 終了")
                yield Label("c: クリア") 
                yield Label("d: ポート検出")
                yield Label("t: 分離切替")
            
            # 右側: データエリア
            with Vertical(id="data_area"):
                yield DataTable(id="data_table")
                yield RichLog(id="log_view", highlight=True)
        
        # ステータスバー
        yield Static("🔴 未接続 | 📥0 📤0", id="status_bar")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """アプリ起動時の初期化"""
        # データテーブル初期化
        table = self.query_one("#data_table", DataTable)
        table.add_columns("時刻", "方向", "データ", "ポート")
        table.cursor_type = "row"
        
        # ログ初期化
        log = self.query_one("#log_view", RichLog)
        log.write("📡 Final Working Dashboard 起動\n")
        log.write("🎉 デバッグで動作確認済み\n")
        log.write("💡 VMware環境での双方向通信対応\n")
        
        # VMware設定例を表示
        if sys.platform == "win32":
            log.write("🖥️ Windows Host側での推奨設定:\n")
            log.write("   RX: COM1 (Linux側からの受信)\n")
            log.write("   TX: COM2 (Linux側への送信)\n")
        else:
            log.write("🐧 Linux Guest側での推奨設定:\n")
            log.write("   RX: /dev/ttyS0 (Windows側からの受信)\n")
            log.write("   TX: /dev/ttyS1 (Windows側への送信)\n")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """チェックボックス変更時の処理"""
        if event.checkbox.id == "separate_ports_checkbox":
            self.dual_port_mode = event.value
            self.update_tx_port_state(event.value)
            self.log_message(f"🔄 送受信分離: {'有効' if event.value else '無効'}")
    
    def update_tx_port_state(self, enable_tx_port: bool):
        """送信ポートの有効/無効切り替え"""
        tx_input = self.query_one("#tx_port_input", Input)
        tx_input.disabled = not enable_tx_port
        
        if enable_tx_port:
            tx_input.styles.opacity = 1.0
        else:
            tx_input.styles.opacity = 0.5
    
    def action_toggle_dual_port(self) -> None:
        """デュアルポートモード切り替え"""
        checkbox = self.query_one("#separate_ports_checkbox", Checkbox)
        checkbox.value = not checkbox.value
        self.dual_port_mode = checkbox.value
        self.update_tx_port_state(checkbox.value)
    
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
        elif button_id == "clear_data_btn":
            self.action_clear_data()
        elif button_id == "save_data_btn":
            self.action_save_data()
    
    def action_detect_ports(self) -> None:
        """ポート検出アクション"""
        self.log_message("🔍 ポート検出中...")
        ports = detect_available_ports()
        self.log_message(f"🔌 {len(ports)} 個のポートを検出")
        
        for port, desc in ports[:8]:
            self.log_message(f"  • {port} - {desc}")
    
    async def connect_serial(self):
        """シリアル接続（デバッグで確認された方式）"""
        rx_port = self.query_one("#rx_port_input", Input).value.strip()
        
        if not rx_port:
            self.log_message("❌ 受信ポートを入力してください")
            return
        
        self.log_message(f"🔌 接続開始: {rx_port}")
        
        try:
            # デバッグで確認された動作方式を使用
            config_file = "serial_config_windows.ini" if sys.platform == "win32" else "serial_config_linux.ini"
            
            # simple_dashboard.py と同じ方式
            if not os.path.exists(config_file):
                self.log_message(f"⚠️ {config_file} が見つかりません。手動設定を使用")
                config = SerialConfig()
                config.config.set('SERIAL', 'port', rx_port)
                config.config.set('SERIAL', 'baudrate', '9600')
                
                self.rx_serial_comm = ModernSerialComm()
                self.rx_serial_comm.config_manager = config
                self.rx_serial_comm._load_settings_from_config()
            else:
                self.log_message(f"📋 {config_file} を使用")
                self.rx_serial_comm = ModernSerialComm(config_file)
                self.rx_serial_comm.config_manager.config.set('SERIAL', 'port', rx_port)
                self.rx_serial_comm._load_settings_from_config()
            
            # 受信コールバック設定
            self.rx_serial_comm.set_receive_callback(self.on_data_received)
            
            # 接続試行
            if not await self.rx_serial_comm.connect():
                self.log_message(f"❌ 受信ポート {rx_port} 接続失敗")
                return
            
            self.log_message(f"✅ 受信ポート {rx_port} 接続成功")
            
            # デュアルポートモードの場合
            if self.dual_port_mode:
                tx_port = self.query_one("#tx_port_input", Input).value.strip()
                
                if not tx_port:
                    self.log_message("❌ 送信ポートを入力してください")
                    await self.rx_serial_comm.disconnect()
                    return
                
                if tx_port != rx_port:
                    self.log_message(f"🔌 送信ポート接続: {tx_port}")
                    
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
                        self.log_message(f"✅ 送信ポート {tx_port} 接続成功")
                    else:
                        self.log_message(f"❌ 送信ポート {tx_port} 接続失敗")
                        await self.rx_serial_comm.disconnect()
                        return
                else:
                    self.tx_serial_comm = self.rx_serial_comm
                    self.log_message(f"📍 送受信に同じポート {tx_port} を使用")
            else:
                self.tx_serial_comm = self.rx_serial_comm
                tx_port = rx_port
            
            self.connected = True
            
            # ボタン状態更新
            self.query_one("#connect_btn", Button).disabled = True
            self.query_one("#disconnect_btn", Button).disabled = False
            
            # ステータス更新
            self.update_status()
            
            self.log_message("🎉 接続完了！データ送受信可能です")
            self.log_message("💬 送信エリアにメッセージを入力して通信テストできます")
            
        except Exception as e:
            self.log_message(f"❌ 接続エラー: {str(e)}")
    
    async def disconnect_serial(self):
        """シリアル切断"""
        if self.connected:
            self.log_message("🔌 切断開始...")
            
            if self.rx_serial_comm:
                await self.rx_serial_comm.disconnect()
                self.log_message("🔌 受信ポート切断完了")
            
            if self.tx_serial_comm and self.tx_serial_comm != self.rx_serial_comm:
                await self.tx_serial_comm.disconnect()
                self.log_message("🔌 送信ポート切断完了")
            
            self.rx_serial_comm = None
            self.tx_serial_comm = None
            self.connected = False
            
            # ボタン状態更新
            self.query_one("#connect_btn", Button).disabled = False
            self.query_one("#disconnect_btn", Button).disabled = True
            
            self.update_status()
            self.log_message("✅ 全ポート切断完了")
    
    async def send_data(self):
        """データ送信"""
        if not self.connected or not self.tx_serial_comm:
            self.log_message("❌ 送信ポート未接続")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            self.log_message("❌ 送信データを入力してください")
            return
        
        if not data.endswith(('\r\n', '\r', '\n')):
            data += '\r\n'
        
        try:
            if await self.tx_serial_comm.send_string(data):
                tx_port = self.tx_serial_comm.port
                self.log_message(f"📤 送信成功({tx_port}): {data.strip()}")
                send_input.value = ""
                self.tx_count += 1
                self.add_to_data_table("TX", data.strip(), tx_port)
                self.update_status()
            else:
                self.log_message("❌ 送信失敗")
        except Exception as e:
            self.log_message(f"❌ 送信エラー: {str(e)}")
    
    def on_data_received(self, data: bytes, direction: str):
        """データ受信処理"""
        self.call_later(self._handle_received_data, data, direction)
    
    def _handle_received_data(self, data: bytes, direction: str):
        """データ受信処理（UIスレッド）"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if direction == "RX":
                rx_port = self.rx_serial_comm.port if self.rx_serial_comm else "unknown"
                self.log_message(f"📥 受信({rx_port}): {data_str}")
                self.add_to_data_table("RX", data_str, rx_port)
                self.rx_count += 1
                self.update_status()
        except Exception as e:
            self.log_message(f"❌ データ処理エラー: {str(e)}")
    
    def add_to_data_table(self, direction: str, data: str, port: str):
        """データテーブルに行追加"""
        table = self.query_one("#data_table", DataTable)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        display_data = data[:25] + "..." if len(data) > 25 else data
        dir_display = "📥" if direction == "RX" else "📤"
        
        table.add_row(timestamp, dir_display, display_data, port)
        
        self.data_buffer.append({
            'timestamp': datetime.now(),
            'direction': direction,
            'data': data,
            'port': port
        })
        
        if table.row_count > 200:
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
        self.log_message("🗑️ データクリア完了")
    
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
                writer.writerow(['timestamp', 'direction', 'data', 'port'])
                
                for entry in self.data_buffer:
                    writer.writerow([
                        entry['timestamp'].isoformat(),
                        entry['direction'],
                        entry['data'],
                        entry['port']
                    ])
            
            self.log_message(f"💾 {filename} 保存完了 ({len(self.data_buffer)}件)")
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
    
    app = FinalWorkingDashboard()
    app.run()


if __name__ == "__main__":
    main()