#!/usr/bin/env python3
"""
Complete Remote Client Dashboard
別PCからハイブリッドダッシュボードに接続する完全版クライアント
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    DataTable, Header, Footer, Static, 
    Button, Input, Label, RichLog, Sparkline
)
from textual.binding import Binding
import asyncio
import socket
import threading
import json
import sys
from datetime import datetime
from typing import Optional


def get_local_ip():
    """ローカルIPアドレス取得"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"


class RemoteClientManager:
    """リモート接続管理クラス"""
    
    def __init__(self, on_data_received=None, on_connection_status=None):
        self.on_data_received = on_data_received
        self.on_connection_status = on_connection_status
        self.socket = None
        self.connected = False
        self.receive_thread = None
        self.target_host = None
        self.target_port = None
    
    async def connect(self, host: str, port: int):
        """サーバーに接続"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            self.socket.connect((host, port))
            
            self.target_host = host
            self.target_port = port
            self.connected = True
            
            # 受信スレッド開始
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            if self.on_connection_status:
                self.on_connection_status(True, f"{host}:{port}")
            
            return True
            
        except Exception as e:
            if self.on_connection_status:
                self.on_connection_status(False, f"接続エラー: {str(e)}")
            return False
    
    def _receive_loop(self):
        """データ受信ループ"""
        buffer = b""
        
        while self.connected and self.socket:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                
                buffer += data
                
                # 行単位で処理
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line and self.on_data_received:
                        self.on_data_received(line, f"{self.target_host}:{self.target_port}")
                        
            except Exception as e:
                if self.connected:
                    if self.on_connection_status:
                        self.on_connection_status(False, f"受信エラー: {str(e)}")
                break
        
        self.connected = False
        if self.on_connection_status:
            self.on_connection_status(False, "接続が切断されました")
    
    async def send_data(self, data: str):
        """データ送信"""
        if not self.connected or not self.socket:
            return False
        
        try:
            if not data.endswith('\n'):
                data += '\n'
            
            self.socket.send(data.encode('utf-8'))
            return True
            
        except Exception as e:
            if self.on_connection_status:
                self.on_connection_status(False, f"送信エラー: {str(e)}")
            return False
    
    def disconnect(self):
        """接続切断"""
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        
        if self.on_connection_status:
            self.on_connection_status(False, "切断しました")


class RemoteConnectionPanel(Container):
    """リモート接続パネル"""
    
    def compose(self) -> ComposeResult:
        yield Label("🌐 リモート接続設定", classes="panel-title")
        
        yield Label("📍 接続先サーバー:", classes="port-label")
        yield Input(
            placeholder="例: 192.168.1.100", 
            id="server_host_input", 
            value="192.168.1.100"
        )
        
        yield Label("🌐 ポート番号:", classes="port-label")
        yield Input(
            placeholder="例: 9999", 
            id="server_port_input", 
            value="9999"
        )
        
        # 接続ボタン
        with Horizontal(classes="button-row"):
            yield Button("接続", id="connect_btn", variant="success")
            yield Button("切断", id="disconnect_btn", variant="error", disabled=True)
        
        # 操作ボタン
        with Horizontal(classes="button-row"):
            yield Button("IP確認", id="ip_info_btn", variant="default")
            yield Button("接続テスト", id="ping_btn", variant="default")


class RemoteConnectionStatus(Static):
    """リモート接続状態表示"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_status(False, "未接続")
    
    def update_status(self, connected: bool, details: str):
        """接続状態更新"""
        local_ip = get_local_ip()
        
        if connected:
            content = f"""🔗 接続状態: ✅ 接続中
━━━━━━━━━━━━━━━━
🎯 サーバー: {details}
📍 ローカルIP: {local_ip}
📊 モード: リモートクライアント
🔄 データ受信中"""
        else:
            content = f"""🔗 接続状態: ❌ 未接続
━━━━━━━━━━━━━━━━
📍 ローカルIP: {local_ip}
📊 モード: 待機中
🔄 通信停止
💡 詳細: {details}"""
        
        self.update(content)


class RemoteSendPanel(Container):
    """リモート送信パネル"""
    
    def compose(self) -> ComposeResult:
        yield Label("📤 データ送信", classes="panel-title")
        yield Input(placeholder="送信データを入力...", id="send_input")
        with Horizontal(classes="button-row"):
            yield Button("送信", id="send_btn", variant="primary")
            yield Button("クリア", id="clear_btn", variant="default")


class RemoteStats(Static):
    """リモート統計情報"""
    
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
    
    def reset_stats(self):
        """統計リセット"""
        self.rx_count = 0
        self.tx_count = 0
        self.rx_bytes = 0
        self.tx_bytes = 0
        self.start_time = datetime.now()
        self.update_display()
    
    def update_display(self):
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        rate = self.rx_count / max(elapsed.total_seconds(), 1)
        
        content = f"""📊 通信統計
━━━━━━━━━━━━━━━━
📥 受信: {self.rx_count:,} ({self.rx_bytes:,} B)
📤 送信: {self.tx_count:,} ({self.tx_bytes:,} B)
⏱️  時間: {elapsed_str}
📈 受信速度: {rate:.1f} pkt/s"""
        
        self.update(content)


class RemoteClientDashboard(App):
    """リモートクライアントダッシュボード"""
    
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
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "clear_data", "Clear Data", show=True),
        Binding("s", "save_data", "Save CSV", show=True),
        Binding("r", "reconnect", "Reconnect", show=True),
        Binding("i", "ip_info", "IP Info", show=True),
    ]
    
    TITLE = "📡 Remote Client Dashboard"
    SUB_TITLE = "Connect to Hybrid Communication Server"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client_manager = RemoteClientManager(
            on_data_received=self.on_data_received,
            on_connection_status=self.on_connection_status
        )
        self.data_buffer = []
        self.sparkline_data = []
        self.connected = False
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            # 左側パネル
            with Vertical(id="left_panel"):
                yield RemoteConnectionPanel(id="connection_panel")
                yield RemoteSendPanel(id="send_panel")
                yield RemoteStats(id="stats_panel")
                yield RemoteConnectionStatus(id="status_panel")
            
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
        table.add_columns("時刻", "方向", "データ", "長さ", "送信元")
        table.cursor_type = "row"
        
        # ログ初期化
        log = self.query_one("#log_view", RichLog)
        log.write("📡 Remote Client Dashboard 起動完了\n")
        log.write("🌐 別PCのハイブリッドダッシュボードに接続可能\n")
        log.write(f"📍 このPCのIP: {get_local_ip()}\n")
        log.write("💡 'r'で再接続、'i'でIP情報表示\n")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタンクリック処理"""
        button_id = event.button.id
        
        if button_id == "connect_btn":
            await self.connect_to_server()
        elif button_id == "disconnect_btn":
            await self.disconnect_from_server()
        elif button_id == "ip_info_btn":
            self.action_ip_info()
        elif button_id == "ping_btn":
            await self.test_connection()
        elif button_id == "send_btn":
            await self.send_data()
        elif button_id == "clear_btn":
            self.query_one("#send_input", Input).value = ""
    
    async def connect_to_server(self):
        """サーバーに接続"""
        host = self.query_one("#server_host_input", Input).value.strip()
        port_str = self.query_one("#server_port_input", Input).value.strip()
        
        if not host:
            self.log_message("❌ サーバーホストを入力してください")
            return
        
        try:
            port = int(port_str) if port_str else 9999
        except ValueError:
            self.log_message("❌ 有効なポート番号を入力してください")
            return
        
        self.log_message(f"🔄 {host}:{port} に接続中...")
        
        if await self.client_manager.connect(host, port):
            self.connected = True
            self.update_button_states()
            self.log_message(f"✅ {host}:{port} に接続しました")
            
            # 統計リセット
            stats = self.query_one("#stats_panel", RemoteStats)
            stats.reset_stats()
        else:
            self.log_message(f"❌ {host}:{port} への接続に失敗しました")
    
    async def disconnect_from_server(self):
        """サーバーから切断"""
        self.client_manager.disconnect()
        self.connected = False
        self.update_button_states()
    
    async def test_connection(self):
        """接続テスト"""
        host = self.query_one("#server_host_input", Input).value.strip()
        port_str = self.query_one("#server_port_input", Input).value.strip()
        
        if not host:
            self.log_message("❌ テスト対象ホストを入力してください")
            return
        
        try:
            port = int(port_str) if port_str else 9999
        except ValueError:
            port = 9999
        
        self.log_message(f"🔍 {host}:{port} への接続テスト中...")
        
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5.0)
            result = test_socket.connect_ex((host, port))
            test_socket.close()
            
            if result == 0:
                self.log_message(f"✅ {host}:{port} への接続テスト成功")
            else:
                self.log_message(f"❌ {host}:{port} への接続テスト失敗 (エラーコード: {result})")
                
        except Exception as e:
            self.log_message(f"❌ 接続テストエラー: {str(e)}")
    
    def update_button_states(self):
        """ボタン状態更新"""
        self.query_one("#connect_btn", Button).disabled = self.connected
        self.query_one("#disconnect_btn", Button).disabled = not self.connected
    
    def on_connection_status(self, connected: bool, details: str):
        """接続状態変更時の処理"""
        self.call_later(self._update_connection_status, connected, details)
    
    def _update_connection_status(self, connected: bool, details: str):
        """接続状態更新（UIスレッド）"""
        self.connected = connected
        status = self.query_one("#status_panel", RemoteConnectionStatus)
        status.update_status(connected, details)
        self.update_button_states()
        self.log_message(f"🔗 接続状態変更: {details}")
    
    def on_data_received(self, data: bytes, source: str):
        """データ受信処理"""
        self.call_later(self._handle_received_data, data, source)
    
    def _handle_received_data(self, data: bytes, source: str):
        """データ受信処理（UIスレッド）"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if data_str:
                self.log_message(f"📥 受信 ({source}): {data_str}")
                self.add_to_data_table("RX", data_str, len(data), source)
                
                # 統計更新
                stats = self.query_one("#stats_panel", RemoteStats)
                stats.update_stats("RX", len(data))
                
                self.update_sparkline(len(data))
                
        except Exception as e:
            self.log_message(f"❌ データ処理エラー: {str(e)}")
    
    async def send_data(self):
        """データ送信"""
        if not self.connected:
            self.log_message("❌ サーバーに接続されていません")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            return
        
        if await self.client_manager.send_data(data):
            self.log_message(f"📤 送信: {data}")
            send_input.value = ""
            
            # 統計更新
            stats = self.query_one("#stats_panel", RemoteStats)
            stats.update_stats("TX", len(data.encode()))
            
            # データテーブルに追加
            self.add_to_data_table("TX", data, len(data.encode()), "Local")
        else:
            self.log_message("❌ 送信に失敗しました")
    
    def add_to_data_table(self, direction: str, data: str, length: int, source: str):
        """データテーブルに行追加"""
        table = self.query_one("#data_table", DataTable)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        display_data = data[:40] + "..." if len(data) > 40 else data
        dir_display = "📥 RX" if direction == "RX" else "📤 TX"
        
        table.add_row(timestamp, dir_display, display_data, str(length), source)
        
        self.data_buffer.append({
            'timestamp': datetime.now(),
            'direction': direction,
            'data': data,
            'length': length,
            'source': source
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
    
    def action_ip_info(self) -> None:
        """IP情報表示"""
        local_ip = get_local_ip()
        self.log_message(f"📍 このPCのIP: {local_ip}")
        
        if self.connected:
            target = f"{self.client_manager.target_host}:{self.client_manager.target_port}"
            self.log_message(f"🎯 接続先: {target}")
        
        # ネットワーク情報取得試行
        try:
            hostname = socket.gethostname()
            self.log_message(f"🖥️ ホスト名: {hostname}")
        except:
            pass
    
    async def action_reconnect(self) -> None:
        """再接続"""
        if self.connected:
            await self.disconnect_from_server()
            # 少し待機
            await asyncio.sleep(1)
        
        await self.connect_to_server()
    
    def action_clear_data(self) -> None:
        """データクリア"""
        table = self.query_one("#data_table", DataTable)
        table.clear()
        
        sparkline = self.query_one("#sparkline", Sparkline)
        self.sparkline_data.clear()
        sparkline.data = []
        
        self.data_buffer.clear()
        
        # 統計リセット
        stats = self.query_one("#stats_panel", RemoteStats)
        stats.reset_stats()
        
        self.log_message("🗑️ データをクリアしました")
    
    def action_save_data(self) -> None:
        """CSV保存"""
        if not self.data_buffer:
            self.log_message("💾 保存するデータがありません")
            return
        
        import csv
        filename = f"remote_client_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'direction', 'data', 'length', 'source'])
                
                for entry in self.data_buffer:
                    writer.writerow([
                        entry['timestamp'].isoformat(),
                        entry['direction'],
                        entry['data'],
                        entry['length'],
                        entry['source']
                    ])
            
            self.log_message(f"💾 {filename} に保存しました ({len(self.data_buffer)} 件)")
        except Exception as e:
            self.log_message(f"❌ 保存エラー: {str(e)}")
    
    async def action_quit(self) -> None:
        """アプリ終了"""
        if self.connected:
            self.client_manager.disconnect()
        self.exit()


def main():
    """メイン実行関数"""
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = RemoteClientDashboard()
    app.run()


if __name__ == "__main__":
    main()