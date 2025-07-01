#!/usr/bin/env python3
"""
Hybrid Communication Dashboard
シリアル通信 + ネットワーク通信対応版
別PCへの送信も可能
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    DataTable, Header, Footer, Static, 
    Button, Input, Label, RichLog, Sparkline, Checkbox, Select
)
from textual.binding import Binding
import asyncio
import sys
import glob
import os
import socket
import threading
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# ライブラリインポート
try:
    from modern_serial_comm import ModernSerialComm, SerialConfig
except ImportError:
    print("Warning: modern_serial_comm.py が見つかりません（シリアル機能は制限されます）")
    ModernSerialComm = None
    SerialConfig = None


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


def get_local_ip():
    """ローカルIPアドレス取得"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"


class NetworkManager:
    """ネットワーク通信管理クラス"""
    
    def __init__(self, on_data_received=None):
        self.on_data_received = on_data_received
        self.server_socket = None
        self.client_connections = []
        self.is_server_running = False
        self.server_thread = None
    
    async def start_server(self, port: int = 9999):
        """TCPサーバー開始"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', port))
            self.server_socket.listen(5)
            self.is_server_running = True
            
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            return True
        except Exception as e:
            print(f"サーバー開始エラー: {e}")
            return False
    
    def _server_loop(self):
        """サーバーループ（別スレッド）"""
        while self.is_server_running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.client_connections.append((client_socket, addr))
                
                # クライアント処理スレッド開始
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.is_server_running:
                    print(f"サーバーループエラー: {e}")
                break
    
    def _handle_client(self, client_socket, addr):
        """クライアント処理"""
        try:
            while self.is_server_running:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                if self.on_data_received:
                    self.on_data_received(data, f"NET_RX_{addr[0]}")
                    
        except Exception as e:
            print(f"クライアント処理エラー {addr}: {e}")
        finally:
            client_socket.close()
            self.client_connections = [
                (s, a) for s, a in self.client_connections if a != addr
            ]
    
    async def send_to_tcp_client(self, host: str, port: int, data: bytes):
        """TCPクライアントとして送信"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                s.connect((host, port))
                s.send(data)
                return True
        except Exception as e:
            print(f"TCP送信エラー ({host}:{port}): {e}")
            return False
    
    def broadcast_to_clients(self, data: bytes):
        """接続中のクライアントに一斉送信"""
        disconnected = []
        for client_socket, addr in self.client_connections:
            try:
                client_socket.send(data)
            except:
                disconnected.append((client_socket, addr))
        
        # 切断されたクライアントを削除
        for client_socket, addr in disconnected:
            try:
                client_socket.close()
            except:
                pass
            self.client_connections = [
                (s, a) for s, a in self.client_connections if a != addr
            ]
    
    def stop_server(self):
        """サーバー停止"""
        self.is_server_running = False
        
        # クライアント接続をクローズ
        for client_socket, addr in self.client_connections:
            try:
                client_socket.close()
            except:
                pass
        self.client_connections.clear()
        
        # サーバーソケットクローズ
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None


class HybridConnectionPanel(Container):
    """ハイブリッド接続パネル（シリアル+ネットワーク）"""
    
    def compose(self) -> ComposeResult:
        yield Label("🔌 接続設定", classes="panel-title")
        
        # 通信方式選択
        yield Label("📡 通信方式:", classes="port-label")
        yield Select(
            [
                ("シリアル通信", "serial"),
                ("ネットワーク（サーバー）", "network_server"),
                ("ネットワーク（クライアント）", "network_client"),
                ("ハイブリッド（シリアル+ネットワーク）", "hybrid")
            ],
            id="comm_type_select",
            allow_blank=False
        )
        
        # シリアルポート設定
        yield Label("📥 受信ポート/IP:", classes="port-label")
        yield Input(
            placeholder="COM2 または 0.0.0.0", 
            id="rx_port_input", 
            value="COM2" if sys.platform == "win32" else "/dev/ttyS0"
        )
        
        # 送受信分離チェックボックス
        yield Checkbox("送受信を分離", id="separate_ports_checkbox")
        
        # 送信ポート/宛先設定
        yield Label("📤 送信ポート/宛先:", classes="port-label", id="tx_port_label")
        yield Input(
            placeholder="COM1 または 192.168.1.100:9999", 
            id="tx_port_input", 
            value="COM1" if sys.platform == "win32" else "/dev/ttyS1"
        )
        
        # ネットワークポート設定
        yield Label("🌐 ネットワークポート:", classes="port-label", id="network_port_label")
        yield Input(
            placeholder="9999", 
            id="network_port_input", 
            value="9999"
        )
        
        # 接続ボタン
        with Horizontal(classes="button-row"):
            yield Button("接続", id="connect_btn", variant="success")
            yield Button("切断", id="disconnect_btn", variant="error", disabled=True)
        
        # 操作ボタン
        with Horizontal(classes="button-row"):
            yield Button("ポート検出", id="detect_ports_btn", variant="default")
            yield Button("IP確認", id="ip_info_btn", variant="default")


class HybridConnectionStatus(Static):
    """ハイブリッド接続状態表示"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_status(False, "none", {})
    
    def update_status(self, connected: bool, comm_type: str, details: dict):
        """接続状態更新"""
        if connected:
            if comm_type == "serial":
                rx_port = details.get('rx_port', 'N/A')
                tx_port = details.get('tx_port', 'N/A')
                if rx_port == tx_port:
                    content = f"""🔗 状態: ✅ シリアル接続
━━━━━━━━━━━━━━━━
📍 ポート: {rx_port}
📊 モード: 単一ポート
🔄 双方向通信"""
                else:
                    content = f"""🔗 状態: ✅ シリアル接続
━━━━━━━━━━━━━━━━
📥 受信: {rx_port}
📤 送信: {tx_port}
📊 モード: デュアルポート"""
            
            elif comm_type == "network_server":
                port = details.get('port', 'N/A')
                local_ip = details.get('local_ip', 'N/A')
                clients = details.get('clients', 0)
                content = f"""🔗 状態: ✅ ネットワークサーバー
━━━━━━━━━━━━━━━━
🌐 アドレス: {local_ip}:{port}
👥 接続数: {clients}
📊 モード: TCP Server"""
            
            elif comm_type == "network_client":
                target = details.get('target', 'N/A')
                content = f"""🔗 状態: ✅ ネットワーククライアント
━━━━━━━━━━━━━━━━
🎯 送信先: {target}
📊 モード: TCP Client
🔄 送信専用"""
            
            elif comm_type == "hybrid":
                serial_port = details.get('serial_port', 'N/A')
                network_port = details.get('network_port', 'N/A')
                clients = details.get('clients', 0)
                content = f"""🔗 状態: ✅ ハイブリッド接続
━━━━━━━━━━━━━━━━
🔌 シリアル: {serial_port}
🌐 ネットワーク: :{network_port}
👥 接続数: {clients}
📊 モード: Serial + Network"""
        else:
            content = """🔗 状態: ❌ 未接続
━━━━━━━━━━━━━━━━
📍 ポート: なし
📊 モード: 待機中
🔄 通信停止"""
        
        self.update(content)


class HybridSendPanel(Container):
    """ハイブリッド送信パネル"""
    
    def compose(self) -> ComposeResult:
        yield Label("📤 データ送信", classes="panel-title")
        
        # 送信先選択
        yield Label("🎯 送信先:", classes="port-label")
        yield Select(
            [
                ("シリアルポート", "serial"),
                ("ネットワーク", "network"),
                ("全て（ブロードキャスト）", "broadcast")
            ],
            id="send_target_select",
            allow_blank=False
        )
        
        yield Input(placeholder="送信データを入力...", id="send_input")
        with Horizontal(classes="button-row"):
            yield Button("送信", id="send_btn", variant="primary")
            yield Button("クリア", id="clear_btn", variant="default")


class HybridDashboard(App):
    """ハイブリッド通信ダッシュボード"""
    
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #left_panel {
        width: 50;
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
        height: 45%;
        border: solid $success;
        padding: 1;
        margin-bottom: 1;
        overflow-y: auto;
    }
    
    #send_panel {
        height: 25%;
        border: solid $warning;
        padding: 1;
        margin-bottom: 1;
        overflow-y: auto;
    }
    
    #status_panel {
        height: 30%;
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
    
    Select {
        margin: 1 0;
    }
    
    #tx_port_label {
        display: none;
    }
    
    #tx_port_input {
        display: none;
    }
    
    #network_port_label {
        display: none;
    }
    
    #network_port_input {
        display: none;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "clear_data", "Clear Data", show=True),
        Binding("s", "save_data", "Save CSV", show=True),
        Binding("d", "detect_ports", "Detect Ports", show=True),
        Binding("i", "ip_info", "IP Info", show=True),
    ]
    
    TITLE = "🌐 Hybrid Communication Dashboard"
    SUB_TITLE = "Serial + Network communication support"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_comm = None
        self.network_manager = NetworkManager(self.on_data_received)
        self.data_buffer = []
        self.sparkline_data = []
        self.connected = False
        self.communication_type = "serial"
        self.connection_details = {}
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            # 左側パネル
            with Vertical(id="left_panel"):
                yield HybridConnectionPanel(id="connection_panel")
                yield HybridSendPanel(id="send_panel")
                yield HybridConnectionStatus(id="status_panel")
            
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
        table.add_columns("時刻", "方向", "データ", "長さ", "送信元/先")
        table.cursor_type = "row"
        
        # ログ初期化
        log = self.query_one("#log_view", RichLog)
        log.write("🌐 Hybrid Communication Dashboard 起動完了\n")
        log.write("💡 シリアル通信とネットワーク通信の両方に対応\n")
        log.write("🎯 通信方式を選択して別PCとの通信も可能\n")
        log.write(f"📍 ローカルIP: {get_local_ip()}\n")
        
        # 初期表示設定
        self.update_ui_visibility("serial")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """セレクトボックス変更処理"""
        if event.select.id == "comm_type_select":
            self.communication_type = event.value
            self.update_ui_visibility(event.value)
            self.log_message(f"🔄 通信方式変更: {event.value}")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """チェックボックス変更処理"""
        if event.checkbox.id == "separate_ports_checkbox":
            self.update_port_separation_ui(event.value)
    
    def update_ui_visibility(self, comm_type: str):
        """通信方式に応じたUI表示制御"""
        tx_label = self.query_one("#tx_port_label", Label)
        tx_input = self.query_one("#tx_port_input", Input)
        net_label = self.query_one("#network_port_label", Label)
        net_input = self.query_one("#network_port_input", Input)
        
        if comm_type in ["network_server", "network_client", "hybrid"]:
            net_label.styles.display = "block"
            net_input.styles.display = "block"
        else:
            net_label.styles.display = "none"
            net_input.styles.display = "none"
        
        if comm_type == "network_client":
            tx_label.styles.display = "block"
            tx_input.styles.display = "block"
            # プレースホルダー更新
            tx_input.placeholder = "送信先 (例: 192.168.1.100:9999)"
        elif comm_type == "serial":
            separate_checkbox = self.query_one("#separate_ports_checkbox", Checkbox)
            if separate_checkbox.value:
                tx_label.styles.display = "block"
                tx_input.styles.display = "block"
            else:
                tx_label.styles.display = "none"
                tx_input.styles.display = "none"
            tx_input.placeholder = "送信ポート (例: COM1)"
        else:
            tx_label.styles.display = "none"
            tx_input.styles.display = "none"
    
    def update_port_separation_ui(self, separate: bool):
        """ポート分離UI更新"""
        if self.communication_type == "serial":
            tx_label = self.query_one("#tx_port_label", Label)
            tx_input = self.query_one("#tx_port_input", Input)
            
            if separate:
                tx_label.styles.display = "block"
                tx_input.styles.display = "block"
            else:
                tx_label.styles.display = "none"
                tx_input.styles.display = "none"
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタンクリック処理"""
        button_id = event.button.id
        
        if button_id == "connect_btn":
            await self.connect_communication()
        elif button_id == "disconnect_btn":
            await self.disconnect_communication()
        elif button_id == "detect_ports_btn":
            self.action_detect_ports()
        elif button_id == "ip_info_btn":
            self.action_ip_info()
        elif button_id == "send_btn":
            await self.send_data()
        elif button_id == "clear_btn":
            self.query_one("#send_input", Input).value = ""
    
    async def connect_communication(self):
        """通信接続"""
        comm_type = self.communication_type
        
        try:
            if comm_type == "serial":
                await self.connect_serial()
            elif comm_type == "network_server":
                await self.connect_network_server()
            elif comm_type == "network_client":
                await self.connect_network_client()
            elif comm_type == "hybrid":
                await self.connect_hybrid()
                
        except Exception as e:
            self.log_message(f"❌ 接続エラー: {str(e)}")
    
    async def connect_serial(self):
        """シリアル接続"""
        if not ModernSerialComm:
            self.log_message("❌ modern_serial_comm.py が必要です")
            return
        
        rx_port = self.query_one("#rx_port_input", Input).value.strip()
        if not rx_port:
            self.log_message("❌ 受信ポートを入力してください")
            return
        
        # プラットフォーム別設定ファイルを選択
        if sys.platform == "win32":
            config_file = "serial_config_windows.ini"
        else:
            config_file = "serial_config_linux.ini"

        if not os.path.exists(config_file):
            # 設定ファイルが無い場合は手動設定
            config = SerialConfig()
            config.config.set('SERIAL', 'port', rx_port)
            config.config.set('SERIAL', 'baudrate', '9600')

            self.serial_comm = ModernSerialComm()
            self.serial_comm.config_manager = config
            self.serial_comm._load_settings_from_config()
        else:
            # 既存設定ファイルを使用
            self.serial_comm = ModernSerialComm(config_file)
            self.serial_comm.config_manager.config.set('SERIAL', 'port', rx_port)
            self.serial_comm._load_settings_from_config()
        self.serial_comm.set_receive_callback(self.on_data_received)
        
        if await self.serial_comm.connect():
            self.connected = True
            self.connection_details = {'rx_port': rx_port, 'tx_port': rx_port}
            self.update_connection_status()
            self.log_message(f"✅ シリアルポート {rx_port} に接続しました")
        else:
            self.log_message(f"❌ シリアルポート {rx_port} への接続に失敗")
    
    async def connect_network_server(self):
        """ネットワークサーバー接続"""
        port_str = self.query_one("#network_port_input", Input).value.strip()
        try:
            port = int(port_str) if port_str else 9999
        except ValueError:
            self.log_message("❌ 有効なポート番号を入力してください")
            return
        
        if await self.network_manager.start_server(port):
            self.connected = True
            local_ip = get_local_ip()
            self.connection_details = {
                'port': port,
                'local_ip': local_ip,
                'clients': 0
            }
            self.update_connection_status()
            self.log_message(f"✅ ネットワークサーバー開始: {local_ip}:{port}")
        else:
            self.log_message(f"❌ ネットワークサーバー開始に失敗")
    
    async def connect_network_client(self):
        """ネットワーククライアント設定"""
        target = self.query_one("#tx_port_input", Input).value.strip()
        if not target:
            self.log_message("❌ 送信先を入力してください（例: 192.168.1.100:9999）")
            return
        
        self.connected = True
        self.connection_details = {'target': target}
        self.update_connection_status()
        self.log_message(f"✅ ネットワーククライアント設定完了: {target}")
    
    async def connect_hybrid(self):
        """ハイブリッド接続"""
        # シリアル接続
        await self.connect_serial()
        if not self.connected:
            return
        
        # ネットワークサーバー追加
        port_str = self.query_one("#network_port_input", Input).value.strip()
        try:
            port = int(port_str) if port_str else 9999
        except ValueError:
            port = 9999
        
        if await self.network_manager.start_server(port):
            serial_port = self.connection_details.get('rx_port', 'N/A')
            self.connection_details = {
                'serial_port': serial_port,
                'network_port': port,
                'clients': 0
            }
            self.update_connection_status()
            self.log_message(f"✅ ハイブリッド接続完了: シリアル({serial_port}) + ネットワーク(:{port})")
        else:
            self.log_message("⚠️ ネットワーク部分の開始に失敗（シリアルのみで継続）")
    
    async def disconnect_communication(self):
        """通信切断"""
        if self.serial_comm:
            await self.serial_comm.disconnect()
            self.serial_comm = None
        
        self.network_manager.stop_server()
        
        self.connected = False
        self.connection_details = {}
        self.update_connection_status()
        self.log_message("🔌 通信を切断しました")
    
    def update_connection_status(self):
        """接続状態更新"""
        status = self.query_one("#status_panel", HybridConnectionStatus)
        status.update_status(self.connected, self.communication_type, self.connection_details)
        
        # ボタン状態更新
        self.query_one("#connect_btn", Button).disabled = self.connected
        self.query_one("#disconnect_btn", Button).disabled = not self.connected
    
    async def send_data(self):
        """データ送信"""
        if not self.connected:
            self.log_message("❌ 接続されていません")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            return
        
        # 改行コード追加
        if not data.endswith(('\r\n', '\r', '\n')):
            data += '\r\n'
        
        send_target = self.query_one("#send_target_select", Select).value
        success = False
        
        try:
            if send_target == "serial" and self.serial_comm:
                success = await self.serial_comm.send_string(data)
                if success:
                    self.log_message(f"📤 シリアル送信: {data.strip()}")
                    self.add_to_data_table("TX", data.strip(), len(data.encode()), "Serial")
            
            elif send_target == "network":
                if self.communication_type == "network_client":
                    # クライアントとして送信
                    target = self.connection_details.get('target', '')
                    if ':' in target:
                        host, port_str = target.rsplit(':', 1)
                        port = int(port_str)
                        success = await self.network_manager.send_to_tcp_client(host, port, data.encode())
                        if success:
                            self.log_message(f"📤 ネットワーク送信: {data.strip()} → {target}")
                            self.add_to_data_table("TX", data.strip(), len(data.encode()), target)
                else:
                    # サーバーとして接続クライアントに送信
                    self.network_manager.broadcast_to_clients(data.encode())
                    clients = len(self.network_manager.client_connections)
                    success = clients > 0
                    if success:
                        self.log_message(f"📤 ネットワーク配信: {data.strip()} → {clients}台")
                        self.add_to_data_table("TX", data.strip(), len(data.encode()), f"Network({clients})")
            
            elif send_target == "broadcast":
                # 全送信先に配信
                if self.serial_comm:
                    await self.serial_comm.send_string(data)
                    self.log_message(f"📤 シリアル送信: {data.strip()}")
                
                if self.network_manager.is_server_running:
                    self.network_manager.broadcast_to_clients(data.encode())
                    clients = len(self.network_manager.client_connections)
                    if clients > 0:
                        self.log_message(f"📤 ネットワーク配信: {data.strip()} → {clients}台")
                
                success = True
                self.add_to_data_table("TX", data.strip(), len(data.encode()), "Broadcast")
            
            if success:
                send_input.value = ""
            else:
                self.log_message("❌ 送信に失敗しました")
                
        except Exception as e:
            self.log_message(f"❌ 送信エラー: {str(e)}")
    
    def on_data_received(self, data: bytes, source: str):
        """データ受信処理"""
        self.call_later(self._handle_received_data, data, source)
    
    def _handle_received_data(self, data: bytes, source: str):
        """データ受信処理（UIスレッド）"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if source.startswith("NET_RX_"):
                # ネットワーク受信
                client_ip = source.replace("NET_RX_", "")
                self.log_message(f"📥 ネットワーク受信 ({client_ip}): {data_str}")
                self.add_to_data_table("RX", data_str, len(data), f"Net_{client_ip}")
            else:
                # シリアル受信
                port = self.serial_comm.port if self.serial_comm else "unknown"
                self.log_message(f"📥 シリアル受信 ({port}): {data_str}")
                self.add_to_data_table("RX", data_str, len(data), f"Serial_{port}")
            
            self.update_sparkline(len(data))
            
        except Exception as e:
            self.log_message(f"❌ データ処理エラー: {str(e)}")
    
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
    
    def action_detect_ports(self) -> None:
        """ポート検出アクション"""
        self.log_message("🔍 ポート検出中...")
        ports = detect_available_ports()
        self.log_message(f"🔌 {len(ports)} 個のポートを検出しました")
        
        for port, desc in ports[:8]:
            self.log_message(f"   • {port} - {desc}")
    
    def action_ip_info(self) -> None:
        """IP情報表示"""
        local_ip = get_local_ip()
        self.log_message(f"📍 ローカルIP: {local_ip}")
        
        # ネットワーク接続情報
        if self.network_manager.is_server_running:
            clients = len(self.network_manager.client_connections)
            self.log_message(f"👥 接続クライアント数: {clients}")
            for client_socket, addr in self.network_manager.client_connections:
                self.log_message(f"   • {addr[0]}:{addr[1]}")
        
        # システム情報
        try:
            hostname = socket.gethostname()
            self.log_message(f"🖥️ ホスト名: {hostname}")
        except:
            pass
    
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
        filename = f"hybrid_comm_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
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
            await self.disconnect_communication()
        self.exit()


def main():
    """メイン実行関数"""
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = HybridDashboard()
    app.run()


if __name__ == "__main__":
    main()
