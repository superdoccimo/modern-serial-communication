#!/usr/bin/env python3
"""
Enhanced Serial Communication Dashboard
ポート自動検出・選択機能付き
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    DataTable, Header, Footer, Static, 
    Button, Input, Label, Log, Sparkline, RichLog, Select
)
from textual.reactive import reactive
from textual import events
from textual.binding import Binding
import asyncio
import json
import sys
import glob
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# 先ほど作成したライブラリをインポート
try:
    from modern_serial_comm import ModernSerialComm, SerialConfig
except ImportError:
    print("Error: modern_serial_comm.py が見つかりません")
    print("同じディレクトリに配置してください")
    sys.exit(1)


def detect_available_ports() -> List[tuple]:
    """利用可能なシリアルポートを検出"""
    ports = []
    
    try:
        import serial.tools.list_ports
        for port in serial.tools.list_ports.comports():
            description = f"{port.device} - {port.description}"
            ports.append((port.device, description))
    except ImportError:
        # pyserial.tools.list_ports が使えない場合の手動検出
        if sys.platform == "win32":
            # Windows COM ポート
            for i in range(1, 21):
                port_name = f"COM{i}"
                ports.append((port_name, f"COM Port {i}"))
        else:
            # Linux/Unix シリアルポート
            patterns = ['/dev/ttyS*', '/dev/ttyUSB*', '/dev/ttyACM*', '/dev/ttyAMA*']
            for pattern in patterns:
                for device in glob.glob(pattern):
                    if os.path.exists(device):
                        ports.append((device, f"Serial Device {os.path.basename(device)}"))
    
    # テスト用ループバック追加
    ports.append(("loop://", "Loop back (テスト用)"))
    
    return ports


class PortSelector(Container):
    """ポート選択ウィジェット"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.available_ports = detect_available_ports()
    
    def compose(self) -> ComposeResult:
        yield Label("🔌 ポート選択", classes="panel-title")
        
        # 利用可能ポートの選択肢作成 (表示名, 値) の形式
        port_options = [(f"{port} - {desc}", port) for port, desc in self.available_ports]
        
        if port_options:
            # デフォルト選択（プラットフォーム別）
            default_port = "/dev/ttyS0" if sys.platform != "win32" else "COM2"
            
            # デフォルトが利用可能ポートにあるか確認
            default_value = None
            for port, desc in self.available_ports:
                if port == default_port:
                    default_value = port  # 値部分を設定
                    break
            
            # デフォルトが見つからない場合は最初のポート
            if not default_value and self.available_ports:
                default_value = self.available_ports[0][0]
            
            yield Select(
                port_options,
                value=default_value,
                id="port_select"
            )
        else:
            yield Label("❌ 利用可能なポートが見つかりません")
        
        yield Label("または手動入力:", classes="small-label")
        yield Input(placeholder="手動でポート名を入力...", id="manual_port_input")


class ConnectionPanel(Container):
    """接続制御パネル"""
    
    def compose(self) -> ComposeResult:
        yield PortSelector(id="port_selector")
        with Horizontal(classes="button-row"):
            yield Button("接続", id="connect_btn", variant="success")
            yield Button("切断", id="disconnect_btn", variant="error", disabled=True)
            yield Button("ポート更新", id="refresh_ports_btn", variant="default")


class EnhancedSerialDashboard(App):
    """拡張版シリアルダッシュボード"""
    
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #left_panel {
        width: 40;
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
    
    .small-label {
        margin: 1 0 0 0;
        color: $text-muted;
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
    
    Select, Input {
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "clear_data", "Clear Data", show=True),
        Binding("s", "save_data", "Save CSV", show=True),
        Binding("r", "refresh_ports", "Refresh Ports", show=True),
    ]
    
    TITLE = "📡 Enhanced Serial Communication Dashboard"
    SUB_TITLE = "Auto-detect ports & Cross-platform support"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_comm = None
        self.data_buffer = []
        self.sparkline_data = []
        self.connected = False
    
    def compose(self) -> ComposeResult:
        """UI構成"""
        yield Header()
        
        with Horizontal():
            # 左側パネル
            with Vertical(id="left_panel"):
                yield ConnectionPanel(id="connection_panel")
                yield SendPanel(id="send_panel")
                yield SerialStats(id="stats_panel")
            
            # 右側メインエリア
            with Vertical(id="main_area"):
                # データテーブル
                yield DataTable(id="data_table")
                
                # スパークライン
                yield Sparkline(
                    id="sparkline",
                    data=[],
                    summary_function=max
                )
                
                # ログビュー
                yield RichLog(id="log_view", highlight=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """アプリ起動時の初期化"""
        # データテーブルの列設定
        table = self.query_one("#data_table", DataTable)
        table.add_columns("時刻", "方向", "データ", "長さ")
        table.cursor_type = "row"
        
        # ログ初期化
        log = self.query_one("#log_view", RichLog)
        log.write("📡 Enhanced Serial Dashboard 起動完了\n")
        log.write("🔍 利用可能ポートを自動検出しました\n")
        log.write("💡 'q'で終了、'c'でデータクリア、's'でCSV保存、'r'でポート更新\n")
        
        # 検出されたポート表示
        ports = detect_available_ports()
        log.write(f"🔌 検出されたポート: {len(ports)} 個\n")
        for port, desc in ports[:5]:  # 最初の5つを表示
            log.write(f"   • {port} - {desc}\n")
        
        # スパークライン初期化
        sparkline = self.query_one("#sparkline", Sparkline)
        sparkline.data = []
    
    def get_selected_port(self) -> str:
        """選択されたポートを取得"""
        try:
            # Select ウィジェットから選択されたポート
            port_select = self.query_one("#port_select", Select)
            selected_port = port_select.value
            
            # 手動入力があるかチェック
            manual_input = self.query_one("#manual_port_input", Input)
            manual_port = manual_input.value.strip()
            
            if manual_port:
                return manual_port
            elif selected_port:
                return selected_port
            else:
                return ""
                
        except Exception as e:
            self.log_message(f"❌ ポート取得エラー: {e}")
            return ""
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタンクリック処理"""
        button_id = event.button.id
        
        if button_id == "connect_btn":
            await self.connect_serial()
        elif button_id == "disconnect_btn":
            await self.disconnect_serial()
        elif button_id == "refresh_ports_btn":
            await self.refresh_ports()
        elif button_id == "send_btn":
            await self.send_data()
        elif button_id == "clear_btn":
            self.query_one("#send_input", Input).value = ""
    
    async def refresh_ports(self):
        """ポート一覧を更新"""
        self.log_message("🔄 ポート一覧を更新中...")
        
        # 新しいポート一覧取得
        ports = detect_available_ports()
        
        # Select ウィジェット更新
        try:
            port_select = self.query_one("#port_select", Select)
            port_options = [(desc, port) for port, desc in ports]
            
            # 現在の選択を保持
            current_value = port_select.value
            
            # オプション更新（Textualの制限により、新しいSelectを作成する必要がある場合）
            self.log_message(f"🔌 {len(ports)} 個のポートを検出しました")
            
        except Exception as e:
            self.log_message(f"❌ ポート更新エラー: {e}")
    
    def action_refresh_ports(self) -> None:
        """ポート更新アクション"""
        asyncio.create_task(self.refresh_ports())
    
    async def connect_serial(self):
        """シリアル接続"""
        port = self.get_selected_port()
        
        if not port:
            self.log_message("❌ ポートを選択してください")
            return
        
        try:
            # プラットフォーム別設定ファイル選択
            if sys.platform == "win32":
                config_file = "serial_config_windows.ini"
            else:
                config_file = "serial_config_linux.ini"
            
            # シリアル通信オブジェクト作成
            self.serial_comm = ModernSerialComm(config_file)
            
            # 選択されたポートを設定
            self.serial_comm.config_manager.config.set('SERIAL', 'port', port)
            self.serial_comm._load_settings_from_config()
            
            # コールバック設定
            self.serial_comm.set_receive_callback(self.on_data_received)
            
            # 接続試行
            if await self.serial_comm.connect():
                self.connected = True
                self.log_message(f"✅ {port} に接続しました")
                
                # ボタン状態更新
                self.query_one("#connect_btn", Button).disabled = True
                self.query_one("#disconnect_btn", Button).disabled = False
                
            else:
                self.log_message(f"❌ {port} への接続に失敗しました")
                
        except Exception as e:
            self.log_message(f"❌ 接続エラー: {str(e)}")
    
    async def disconnect_serial(self):
        """シリアル切断"""
        if self.serial_comm and self.connected:
            await self.serial_comm.disconnect()
            self.connected = False
            self.log_message("🔌 接続を切断しました")
            
            # ボタン状態更新
            self.query_one("#connect_btn", Button).disabled = False
            self.query_one("#disconnect_btn", Button).disabled = True
    
    # [残りのメソッドは元のSerialDashboardと同じ]
    # send_data, on_data_received, _handle_received_data, 
    # add_to_data_table, update_sparkline, log_message,
    # action_clear_data, action_save_data, action_quit
    
    async def send_data(self):
        """データ送信"""
        if not self.connected or not self.serial_comm:
            self.log_message("❌ 接続されていません")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            return
        
        # 改行コード追加
        if not data.endswith(('\r\n', '\r', '\n')):
            data += '\r\n'
        
        if await self.serial_comm.send_string(data):
            self.log_message(f"📤 送信: {data.strip()}")
            send_input.value = ""
            
            # 統計更新
            stats = self.query_one("#stats_panel", SerialStats)
            stats.update_stats("TX", len(data.encode()))
            
            # データテーブルに追加
            self.add_to_data_table("TX", data.strip(), len(data.encode()))
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
                self.log_message(f"📥 受信: {data_str}")
                self.add_to_data_table("RX", data_str, len(data))
                
                stats = self.query_one("#stats_panel", SerialStats)
                stats.update_stats("RX", len(data))
                
                self.update_sparkline(len(data))
                
        except Exception as e:
            self.log_message(f"❌ データ処理エラー: {str(e)}")
    
    def add_to_data_table(self, direction: str, data: str, length: int):
        """データテーブルに行追加"""
        table = self.query_one("#data_table", DataTable)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        display_data = data[:50] + "..." if len(data) > 50 else data
        dir_display = "📥 RX" if direction == "RX" else "📤 TX"
        
        table.add_row(timestamp, dir_display, display_data, str(length))
        
        self.data_buffer.append({
            'timestamp': datetime.now(),
            'direction': direction,
            'data': data,
            'length': length
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
                writer.writerow(['timestamp', 'direction', 'data', 'length'])
                
                for entry in self.data_buffer:
                    writer.writerow([
                        entry['timestamp'].isoformat(),
                        entry['direction'],
                        entry['data'],
                        entry['length']
                    ])
            
            self.log_message(f"💾 {filename} に保存しました ({len(self.data_buffer)} 件)")
        except Exception as e:
            self.log_message(f"❌ 保存エラー: {str(e)}")
    
    async def action_quit(self) -> None:
        """アプリ終了"""
        if self.serial_comm and self.connected:
            await self.serial_comm.disconnect()
        self.exit()


# SendPanel と SerialStats は元のコードと同じ
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
        """統計更新"""
        if direction == "RX":
            self.rx_count += 1
            self.rx_bytes += byte_count
        elif direction == "TX":
            self.tx_count += 1
            self.tx_bytes += byte_count
        
        self.update_display()
    
    def update_display(self):
        """表示更新"""
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


def main():
    """メイン実行関数"""
    import sys
    
    # Windowsイベントループ設定
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # アプリ実行
    app = EnhancedSerialDashboard()
    app.run()


if __name__ == "__main__":
    main()
