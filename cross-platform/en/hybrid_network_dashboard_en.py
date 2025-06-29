#!/usr/bin/env python3
"""
Hybrid Communication Dashboard
Supports serial and network communication
Allows sending to other PCs
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

# Import libraries
try:
    from modern_serial_comm import ModernSerialComm, SerialConfig
except ImportError:
    print("Warning: modern_serial_comm.py not found (serial features limited)")
    ModernSerialComm = None
    SerialConfig = None


def detect_available_ports() -> List[tuple]:
    """Detect available serial ports"""
    ports = []
    
    try:
        import serial.tools.list_ports
        for port in serial.tools.list_ports.comports():
            ports.append((port.device, port.description or "Unknown"))
    except ImportError:
        # Manual detection
        if sys.platform == "win32":
            for i in range(1, 21):
                ports.append((f"COM{i}", f"COM Port {i}"))
        else:
            patterns = ['/dev/ttyS*', '/dev/ttyUSB*', '/dev/ttyACM*']
            for pattern in patterns:
                for device in glob.glob(pattern):
                    if os.path.exists(device):
                        ports.append((device, f"Serial Device {os.path.basename(device)}"))
    
    # Test use
    ports.append(("loop://", "Loop back (for testing)"))
    return ports


def get_local_ip():
    """Get local IP address"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"


class NetworkManager:
    """Network communication manager"""
    
    def __init__(self, on_data_received=None):
        self.on_data_received = on_data_received
        self.server_socket = None
        self.client_connections = []
        self.is_server_running = False
        self.server_thread = None
    
    async def start_server(self, port: int = 9999):
        """Start TCP server"""
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
            print(f"Server start error: {e}")
            return False
    
    def _server_loop(self):
        """Server loop (thread)"""
        while self.is_server_running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.client_connections.append((client_socket, addr))
                
                # Start client handling thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.is_server_running:
                    print(f"Server loop error: {e}")
                break
    
    def _handle_client(self, client_socket, addr):
        """Client handling"""
        try:
            while self.is_server_running:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                if self.on_data_received:
                    self.on_data_received(data, f"NET_RX_{addr[0]}")
                    
        except Exception as e:
            print(f"Client handling error {addr}: {e}")
        finally:
            client_socket.close()
            self.client_connections = [
                (s, a) for s, a in self.client_connections if a != addr
            ]
    
    async def send_to_tcp_client(self, host: str, port: int, data: bytes):
        """Send as TCP client"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                s.connect((host, port))
                s.send(data)
                return True
        except Exception as e:
            print(f"TCPSend error ({host}:{port}): {e}")
            return False
    
    def broadcast_to_clients(self, data: bytes):
        """Broadcast to connected clients"""
        disconnected = []
        for client_socket, addr in self.client_connections:
            try:
                client_socket.send(data)
            except:
                disconnected.append((client_socket, addr))
        
        # Remove disconnected clients
        for client_socket, addr in disconnected:
            try:
                client_socket.close()
            except:
                pass
            self.client_connections = [
                (s, a) for s, a in self.client_connections if a != addr
            ]
    
    def stop_server(self):
        """Stop server"""
        self.is_server_running = False
        
        # Close client connections
        for client_socket, addr in self.client_connections:
            try:
                client_socket.close()
            except:
                pass
        self.client_connections.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None


class HybridConnectionPanel(Container):
    """Hybrid connection panel (Serial + Network)"""
    
    def compose(self) -> ComposeResult:
        yield Label("🔌 Connection Settings", classes="panel-title")
        
        # Select communication type
        yield Label("📡 Communication Type:", classes="port-label")
        yield Select(
            [
                ("Serial Communication", "serial"),
                ("Network (Server)", "network_server"),
                ("Network (Client)", "network_client"),
                ("Hybrid (Serial + Network)", "hybrid")
            ],
            id="comm_type_select",
            allow_blank=False
        )
        
        # Serial port settings
        yield Label("📥 RX Port/IP:", classes="port-label")
        yield Input(
            placeholder="COM2 or 0.0.0.0", 
            id="rx_port_input", 
            value="COM2" if sys.platform == "win32" else "/dev/ttyS0"
        )
        
        # Separate TX/RX checkbox
        yield Checkbox("Separate TX/RX", id="separate_ports_checkbox")
        
        # TX port/destination settings
        yield Label("📤 TX Port/Destination:", classes="port-label", id="tx_port_label")
        yield Input(
            placeholder="COM1 or 192.168.1.100:9999", 
            id="tx_port_input", 
            value="COM1" if sys.platform == "win32" else "/dev/ttyS1"
        )
        
        # Network port setting
        yield Label("🌐 Network Port:", classes="port-label", id="network_port_label")
        yield Input(
            placeholder="9999", 
            id="network_port_input", 
            value="9999"
        )
        
        # Connect button
        with Horizontal(classes="button-row"):
            yield Button("Connect", id="connect_btn", variant="success")
            yield Button("Disconnect", id="disconnect_btn", variant="error", disabled=True)
        
        # Action buttons
        with Horizontal(classes="button-row"):
            yield Button("Detect Ports", id="detect_ports_btn", variant="default")
            yield Button("IP Info", id="ip_info_btn", variant="default")


class HybridConnectionStatus(Static):
    """Hybrid Connection Status"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_status(False, "none", {})
    
    def update_status(self, connected: bool, comm_type: str, details: dict):
        """Update connection status"""
        if connected:
            if comm_type == "serial":
                rx_port = details.get('rx_port', 'N/A')
                tx_port = details.get('tx_port', 'N/A')
                if rx_port == tx_port:
                    content = f"""🔗 Status: ✅ Serial Connected
━━━━━━━━━━━━━━━━
📍 Port: {rx_port}
📊 Mode: Single port
🔄 Bidirectional"""
                else:
                    content = f"""🔗 Status: ✅ Serial Connected
━━━━━━━━━━━━━━━━
📥 RX: {rx_port}
📤 TX: {tx_port}
📊 Mode: Dual port"""
            
            elif comm_type == "network_server":
                port = details.get('port', 'N/A')
                local_ip = details.get('local_ip', 'N/A')
                clients = details.get('clients', 0)
                content = f"""🔗 Status: ✅ Network Server
━━━━━━━━━━━━━━━━
🌐 Address: {local_ip}:{port}
👥 Clients: {clients}
📊 Mode: TCP Server"""
            
            elif comm_type == "network_client":
                target = details.get('target', 'N/A')
                content = f"""🔗 Status: ✅ Network Client
━━━━━━━━━━━━━━━━
🎯 Destination: {target}
📊 Mode: TCP Client
🔄 Transmit only"""
            
            elif comm_type == "hybrid":
                serial_port = details.get('serial_port', 'N/A')
                network_port = details.get('network_port', 'N/A')
                clients = details.get('clients', 0)
                content = f"""🔗 Status: ✅ Hybrid Connection
━━━━━━━━━━━━━━━━
🔌 Serial: {serial_port}
🌐 Network: :{network_port}
👥 Clients: {clients}
📊 Mode: Serial + Network"""
        else:
            content = """🔗 Status: ❌ Disconnected
━━━━━━━━━━━━━━━━
📍 Port: None
📊 Mode: Idle
🔄 Communication stopped"""
        
        self.update(content)


class HybridSendPanel(Container):
    """Hybrid Send Panel"""
    
    def compose(self) -> ComposeResult:
        yield Label("📤 Send Data", classes="panel-title")
        
        # Select destination
        yield Label("🎯 Destination:", classes="port-label")
        yield Select(
            [
                ("Serial port", "serial"),
                ("Network", "network"),
                ("All (Broadcast)", "broadcast")
            ],
            id="send_target_select",
            allow_blank=False
        )
        
        yield Input(placeholder="Enter data to send...", id="send_input")
        with Horizontal(classes="button-row"):
            yield Button("Send", id="send_btn", variant="primary")
            yield Button("Clear", id="clear_btn", variant="default")


class HybridDashboard(App):
    """Hybrid Communication Dashboard"""
    
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
            # Left panel
            with Vertical(id="left_panel"):
                yield HybridConnectionPanel(id="connection_panel")
                yield HybridSendPanel(id="send_panel")
                yield HybridConnectionStatus(id="status_panel")
            
            # Right main area
            with Vertical(id="main_area"):
                yield DataTable(id="data_table")
                yield Sparkline(id="sparkline", data=[], summary_function=max)
                yield RichLog(id="log_view", highlight=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize on startup"""
        # Initialize data table
        table = self.query_one("#data_table", DataTable)
        table.add_columns("Time", "Direction", "Data", "Length", "Source/Dest")
        table.cursor_type = "row"
        
        # Initialize logs
        log = self.query_one("#log_view", RichLog)
        log.write("🌐 Hybrid Communication Dashboard started\n")
        log.write("💡 Supports both serial and network communication\n")
        log.write("🎯 Select communication type to communicate with another PC\n")
        log.write(f"📍 Local IP: {get_local_ip()}\n")
        
        # Initial display settings
        self.update_ui_visibility("serial")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select box changes"""
        if event.select.id == "comm_type_select":
            self.communication_type = event.value
            self.update_ui_visibility(event.value)
            self.log_message(f"🔄 Communication type changed: {event.value}")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes"""
        if event.checkbox.id == "separate_ports_checkbox":
            self.update_port_separation_ui(event.value)
    
    def update_ui_visibility(self, comm_type: str):
        """Update UI based on communication type"""
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
            # Update placeholder
            tx_input.placeholder = "Destination (e.g., 192.168.1.100:9999)"
        elif comm_type == "serial":
            separate_checkbox = self.query_one("#separate_ports_checkbox", Checkbox)
            if separate_checkbox.value:
                tx_label.styles.display = "block"
                tx_input.styles.display = "block"
            else:
                tx_label.styles.display = "none"
                tx_input.styles.display = "none"
            tx_input.placeholder = "TX port (e.g., COM1)"
        else:
            tx_label.styles.display = "none"
            tx_input.styles.display = "none"
    
    def update_port_separation_ui(self, separate: bool):
        """Update port separation UI"""
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
        """Handle button clicks"""
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
        """Start connection"""
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
            self.log_message(f"❌ Connection error: {str(e)}")
    
    async def connect_serial(self):
        """Serial Connected"""
        if not ModernSerialComm:
            self.log_message("❌ modern_serial_comm.py is required")
            return
        
        rx_port = self.query_one("#rx_port_input", Input).value.strip()
        if not rx_port:
            self.log_message("❌ Please enter RX port")
            return
        
        # Choose config file by platform
        if sys.platform == "win32":
            config_file = "serial_config_windows.ini"
        else:
            config_file = "serial_config_linux.ini"

        if not os.path.exists(config_file):
            # Manual settings if no config file
            config = SerialConfig()
            config.config.set('SERIAL', 'port', rx_port)
            config.config.set('SERIAL', 'baudrate', '9600')

            self.serial_comm = ModernSerialComm()
            self.serial_comm.config_manager = config
            self.serial_comm._load_settings_from_config()
        else:
            # Use existing config file
            self.serial_comm = ModernSerialComm(config_file)
            self.serial_comm.config_manager.config.set('SERIAL', 'port', rx_port)
            self.serial_comm._load_settings_from_config()
        self.serial_comm.set_receive_callback(self.on_data_received)
        
        if await self.serial_comm.connect():
            self.connected = True
            self.connection_details = {'rx_port': rx_port, 'tx_port': rx_port}
            self.update_connection_status()
            self.log_message(f"✅ Connected to serial port {rx_port}")
        else:
            self.log_message(f"❌ Failed to connect to serial port {rx_port}")
    
    async def connect_network_server(self):
        """Connect as network server"""
        port_str = self.query_one("#network_port_input", Input).value.strip()
        try:
            port = int(port_str) if port_str else 9999
        except ValueError:
            self.log_message("❌ Please enter a valid port number")
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
            self.log_message(f"✅ Network server started: {local_ip}:{port}")
        else:
            self.log_message(f"❌ Failed to start network server")
    
    async def connect_network_client(self):
        """Set up network client"""
        target = self.query_one("#tx_port_input", Input).value.strip()
        if not target:
            self.log_message("❌ Please enter destination (e.g., 192.168.1.100:9999)")
            return
        
        self.connected = True
        self.connection_details = {'target': target}
        self.update_connection_status()
        self.log_message(f"✅ Network client configured: {target}")
    
    async def connect_hybrid(self):
        """Hybrid Connection"""
        # Serial Connected
        await self.connect_serial()
        if not self.connected:
            return
        
        # Add network server
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
            self.log_message(f"✅ Hybrid connection ready: Serial({serial_port}) + Network(:{port})")
        else:
            self.log_message("⚠️ Failed to start network portion (continuing with serial only)")
    
    async def disconnect_communication(self):
        """Disconnect communication"""
        if self.serial_comm:
            await self.serial_comm.disconnect()
            self.serial_comm = None
        
        self.network_manager.stop_server()
        
        self.connected = False
        self.connection_details = {}
        self.update_connection_status()
        self.log_message("🔌 Communication disconnected")
    
    def update_connection_status(self):
        """Update connection status"""
        status = self.query_one("#status_panel", HybridConnectionStatus)
        status.update_status(self.connected, self.communication_type, self.connection_details)
        
        # Update button status
        self.query_one("#connect_btn", Button).disabled = self.connected
        self.query_one("#disconnect_btn", Button).disabled = not self.connected
    
    async def send_data(self):
        """Send Data"""
        if not self.connected:
            self.log_message("❌ Not connected")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            return
        
        # Append newline
        if not data.endswith(('\r\n', '\r', '\n')):
            data += '\r\n'
        
        send_target = self.query_one("#send_target_select", Select).value
        success = False
        
        try:
            if send_target == "serial" and self.serial_comm:
                success = await self.serial_comm.send_string(data)
                if success:
                    self.log_message(f"📤 Serial sent: {data.strip()}")
                    self.add_to_data_table("TX", data.strip(), len(data.encode()), "Serial")
            
            elif send_target == "network":
                if self.communication_type == "network_client":
                    # Send as client
                    target = self.connection_details.get('target', '')
                    if ':' in target:
                        host, port_str = target.rsplit(':', 1)
                        port = int(port_str)
                        success = await self.network_manager.send_to_tcp_client(host, port, data.encode())
                        if success:
                            self.log_message(f"📤 Network send: {data.strip()} → {target}")
                            self.add_to_data_table("TX", data.strip(), len(data.encode()), target)
                else:
                    # Send to connected clients as server
                    self.network_manager.broadcast_to_clients(data.encode())
                    clients = len(self.network_manager.client_connections)
                    success = clients > 0
                    if success:
                        self.log_message(f"📤 Network broadcast: {data.strip()} → {clients} clients")
                        self.add_to_data_table("TX", data.strip(), len(data.encode()), f"Network({clients})")
            
            elif send_target == "broadcast":
                # Broadcast to all destinations
                if self.serial_comm:
                    await self.serial_comm.send_string(data)
                    self.log_message(f"📤 Serial sent: {data.strip()}")
                
                if self.network_manager.is_server_running:
                    self.network_manager.broadcast_to_clients(data.encode())
                    clients = len(self.network_manager.client_connections)
                    if clients > 0:
                        self.log_message(f"📤 Network broadcast: {data.strip()} → {clients} clients")
                
                success = True
                self.add_to_data_table("TX", data.strip(), len(data.encode()), "Broadcast")
            
            if success:
                send_input.value = ""
            else:
                self.log_message("❌ Send failed")
                
        except Exception as e:
            self.log_message(f"❌ Send error: {str(e)}")
    
    def on_data_received(self, data: bytes, source: str):
        """Data receive handler"""
        self.call_later(self._handle_received_data, data, source)
    
    def _handle_received_data(self, data: bytes, source: str):
        """Handle received data (UI thread)"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if source.startswith("NET_RX_"):
                # Network RX
                client_ip = source.replace("NET_RX_", "")
                self.log_message(f"📥 Network RX ({client_ip}): {data_str}")
                self.add_to_data_table("RX", data_str, len(data), f"Net_{client_ip}")
            else:
                # Serial RX
                port = self.serial_comm.port if self.serial_comm else "unknown"
                self.log_message(f"📥 Serial RX ({port}): {data_str}")
                self.add_to_data_table("RX", data_str, len(data), f"Serial_{port}")
            
            self.update_sparkline(len(data))
            
        except Exception as e:
            self.log_message(f"❌ Data processing error: {str(e)}")
    
    def add_to_data_table(self, direction: str, data: str, length: int, source: str):
        """Add row to data table"""
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
        """Update sparkline"""
        sparkline = self.query_one("#sparkline", Sparkline)
        self.sparkline_data.append(data_length)
        
        if len(self.sparkline_data) > 100:
            self.sparkline_data.pop(0)
        
        sparkline.data = self.sparkline_data
    
    def log_message(self, message: str):
        """Output log message"""
        log = self.query_one("#log_view", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")
    
    def action_detect_ports(self) -> None:
        """Detect Ports action"""
        self.log_message("🔍 Detecting ports...")
        ports = detect_available_ports()
        self.log_message(f"🔌 {len(ports)} ports detected")
        
        for port, desc in ports[:8]:
            self.log_message(f"   • {port} - {desc}")
    
    def action_ip_info(self) -> None:
        """Show IP info"""
        local_ip = get_local_ip()
        self.log_message(f"📍 Local IP: {local_ip}")
        
        # Network connection info
        if self.network_manager.is_server_running:
            clients = len(self.network_manager.client_connections)
            self.log_message(f"👥 Connected clients: {clients}")
            for client_socket, addr in self.network_manager.client_connections:
                self.log_message(f"   • {addr[0]}:{addr[1]}")
        
        # System info
        try:
            hostname = socket.gethostname()
            self.log_message(f"🖥️ Host name: {hostname}")
        except:
            pass
    
    def action_clear_data(self) -> None:
        """Clear data"""
        table = self.query_one("#data_table", DataTable)
        table.clear()
        
        sparkline = self.query_one("#sparkline", Sparkline)
        self.sparkline_data.clear()
        sparkline.data = []
        
        self.data_buffer.clear()
        self.log_message("🗑️ Data cleared")
    
    def action_save_data(self) -> None:
        """Save CSV"""
        if not self.data_buffer:
            self.log_message("💾 No data to save")
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
            
            self.log_message(f"💾 {filename} saved to {len(self.data_buffer)} entries)")
        except Exception as e:
            self.log_message(f"❌ Save error: {str(e)}")
    
    async def action_quit(self) -> None:
        """Exit application"""
        if self.connected:
            await self.disconnect_communication()
        self.exit()


def main():
    """Main function"""
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = HybridDashboard()
    app.run()


if __name__ == "__main__":
    main()
