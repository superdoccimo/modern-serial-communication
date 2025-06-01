#!/usr/bin/env python3
"""
Textual-based Serial Communication Dashboard
Real-time monitoring in terminal UI

Requirements:
pip install textual rich

Usage:
python serial_dashboard.py
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    DataTable, Header, Footer, Static, 
    Button, Input, Label, Log, Sparkline
)
from textual.reactive import reactive
from textual import events
from textual.binding import Binding
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
import sys
from pathlib import Path

# 先ほど作成したライブラリをインポート
try:
    from modern_serial_comm import ModernSerialComm, SerialConfig
except ImportError:
    print("Error: modern_serial_comm.py が見つかりません")
    print("同じディレクトリに配置してください")
    sys.exit(1)


class SerialStats(Static):
    """統計情報表示ウィジェット"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rx_count = 0
        self.tx_count = 0
        self.rx_bytes = 0
        self.tx_bytes = 0
        self.start_time = datetime.now()
    
    def update_stats(self, direction: str, byte_count: int):
        """統計更新"""
        if direction == "RX":
            self.rx_count += 1
            self.rx_bytes += byte_count
        elif direction == "TX":
            self.tx_count += 1
            self.tx_bytes += byte_count
        
        # 経過時間計算
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]  # ミリ秒除去
        
        # 表示更新
        self.update(f"""
📊 統計情報
━━━━━━━━━━━━━━━━━━━━
📥 受信: {self.rx_count:,} パケット ({self.rx_bytes:,} bytes)
📤 送信: {self.tx_count:,} パケット ({self.tx_bytes:,} bytes)
⏱️  経過時間: {elapsed_str}
📈 平均レート: {self.rx_count / max(elapsed.total_seconds(), 1):.1f} pkt/sec
        """.strip())


class ConnectionPanel(Container):
    """接続制御パネル"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connected = False
    
    def compose(self) -> ComposeResult:
        yield Label("🔌 接続制御", classes="panel-title")
        yield Input(placeholder="COM1 または socket://host:port", id="port_input")
        with Horizontal(classes="button-row"):
            # 修正点1: classes="success" / "error" を追加
            yield Button("🟢接続", id="connect_btn", classes="success")
            yield Button("🔴切断", id="disconnect_btn", classes="error", disabled=True)


class SendPanel(Container):
    """データ送信パネル"""
    
    def compose(self) -> ComposeResult:
        yield Label("📤 データ送信", classes="panel-title")
        yield Input(placeholder="送信データを入力...", id="send_input")
        yield Horizontal(
            # 修正点1: classes="primary" を追加
            Button("📤送信", id="send_btn", classes="primary"),
            Button("🗑️クリア", id="clear_btn"),
            classes="button-row"
        )


class SerialDashboard(App):
    """メインダッシュボードアプリ"""
    
    CSS = """
    .panel-title {
        color: $accent;
        text-style: bold;
        margin: 1;
    }
    
    .button-row {
        height: 3;
        margin: 1;
    }
    
    #data_table {
        height: 1fr;
    }
    
    #sparkline {
        height: 8;
        margin: 1;
    }
    
    #log_view {
        height: 8;
        border: solid $primary;
    }
    
    #stats_panel {
        width: 30;
        border: solid $accent;
    }
    
    #connection_panel {
        height: 10;
        border: solid $success;
    }
    
    #send_panel {
        height: 10;
        border: solid $warning;
    }
    
    /* 修正点2: ボタンのCSSクラス名を変更 */
    /* --- ボタン共通 --- */
    Button {
        min-width: 10;          /* 狭すぎて文字が折り返すのを防止 */
        height: 3;
        content-align: center middle;
        text-style: bold;
    }

    /* --- 個別カラー --- */
    Button.success {
        background: green;
        color: white;
        border: solid white;
    }

    Button.error {
        background: red;
        color: white;
        border: solid white;
    }

    /* 送信ボタンは primary で統一 */
    Button.primary {
        background: blue;
        color: white;
        border: solid white;
    }
    
    Button:disabled {
        background: gray;
        color: black;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "clear_data", "Clear Data", show=True),
        Binding("s", "save_data", "Save CSV", show=True),
        Binding("r", "toggle_recording", "Record", show=True),
    ]
    
    TITLE = "📡 Modern Serial Communication Dashboard"
    SUB_TITLE = "Python-powered real-time monitoring"
    
    # リアクティブ属性
    connected = reactive(False)
    recording = reactive(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_comm: ModernSerialComm = None
        self.data_buffer: List[Dict[str, Any]] = []
        self.sparkline_data: List[int] = []
    
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
                
                # スパークライン（データ量の可視化）
                yield Sparkline(id="sparkline", summary_function=max)
                
                # ログビュー
                yield Log(id="log_view")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """アプリ起動時の初期化"""
        # データテーブルの列設定
        table = self.query_one("#data_table", DataTable)
        table.add_columns("時刻", "方向", "データ", "長さ")
        
        # ログ初期化
        log = self.query_one("#log_view", Log)
        log.write_line("📡 Serial Dashboard 起動完了")
        log.write_line("💡 'q'で終了、'c'でデータクリア、's'でCSV保存")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタンクリック処理"""
        button_id = event.button.id
        
        if button_id == "connect_btn":
            await self.connect_serial()
        elif button_id == "disconnect_btn":
            await self.disconnect_serial()
        elif button_id == "send_btn":
            await self.send_data()
        elif button_id == "clear_btn":
            self.query_one("#send_input", Input).value = ""
    
    async def connect_serial(self):
        """シリアル接続"""
        port_input = self.query_one("#port_input", Input)
        port = port_input.value.strip()
        
        if not port:
            self.log_message("❌ ポートを指定してください")
            return
        
        try:
            # 設定作成（動的にポート変更）
            config = SerialConfig()
            if port.startswith("socket://"):
                config.config.set('NETWORK', 'use_tcp', 'true')
                host_port = port.replace("socket://", "").split(":")
                config.config.set('NETWORK', 'tcp_host', host_port[0])
                config.config.set('NETWORK', 'tcp_port', host_port[1])
            else:
                config.config.set('SERIAL', 'port', port)
            
            # シリアル通信オブジェクト作成
            self.serial_comm = ModernSerialComm()
            self.serial_comm.config = config
            self.serial_comm.set_receive_callback(self.on_data_received)
            
            # 接続試行
            if await self.serial_comm.connect():
                self.connected = True
                self.log_message(f"✅ {port} に接続しました")
                
                # UIの状態更新
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
            
            # UIの状態更新
            self.query_one("#connect_btn", Button).disabled = False
            self.query_one("#disconnect_btn", Button).disabled = True
    
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
        else:
            self.log_message("❌ 送信に失敗しました")
    
    def on_data_received(self, data: bytes):
        """データ受信コールバック"""
        timestamp = datetime.now()
        data_str = data.decode('ascii', errors='ignore').strip()
        
        # データテーブルに追加
        table = self.query_one("#data_table", DataTable)
        table.add_row(
            timestamp.strftime("%H:%M:%S.%f")[:-3],  # ミリ秒まで
            "📥 RX",
            data_str[:50] + ("..." if len(data_str) > 50 else ""),
            str(len(data))
        )
        
        # スパークラインデータ更新
        sparkline = self.query_one("#sparkline", Sparkline)
        self.sparkline_data.append(len(data))
        if len(self.sparkline_data) > 100:  # 最新100件のみ保持
            self.sparkline_data.pop(0)
        sparkline.data = self.sparkline_data
        
        # バッファに保存
        self.data_buffer.append({
            'timestamp': timestamp,
            'direction': 'RX',
            'data': data_str,
            'length': len(data)
        })
        
        # 統計更新
        stats = self.query_one("#stats_panel", SerialStats)
        stats.update_stats("RX", len(data))
        
        # ログ出力
        self.log_message(f"📥 受信: {data_str}")
    
    def log_message(self, message: str):
        """ログメッセージ出力"""
        log = self.query_one("#log_view", Log)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write_line(f"[{timestamp}] {message}")
    
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
    
    def action_toggle_recording(self) -> None:
        """記録開始/停止"""
        self.recording = not self.recording
        status = "開始" if self.recording else "停止"
        self.log_message(f"🔴 記録を{status}しました")
    
    async def on_unmount(self) -> None:
        """アプリ終了時のクリーンアップ"""
        if self.serial_comm and self.connected:
            await self.serial_comm.disconnect()


def main():
    """メイン実行関数"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("""
Serial Dashboard - Modern Serial Communication Tool

Usage:
    python serial_dashboard.py

Controls:
    q: Quit
    c: Clear data
    s: Save to CSV
    r: Toggle recording

Connection Examples:
    COM1          - Direct serial port
    socket://localhost:5000  - TCP connection (for VM environments)
    loop://       - Loopback for testing
            """)
            return
    
    # アプリ実行
    app = SerialDashboard()
    app.run()


if __name__ == "__main__":
    main()