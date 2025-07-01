#!/usr/bin/env python3
"""
Complete Remote Client Dashboard
Full client to connect to the hybrid dashboard from another PC
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
import time


def get_local_ip():
    """Get local IP address"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"


class RemoteClientManager:
    """Remote connection manager"""
    
    def __init__(self, on_data_received=None, on_connection_status=None, heartbeat_interval: float = 30.0):
        self.on_data_received = on_data_received
        self.on_connection_status = on_connection_status
        self.socket = None
        self.connected = False
        self.receive_thread = None
        self.heartbeat_thread = None
        self.heartbeat_interval = heartbeat_interval
        self.target_host = None
        self.target_port = None
    
    async def connect(self, host: str, port: int):
        """Connect to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            self.socket.connect((host, port))
            self.socket.settimeout(None)
            
            self.target_host = host
            self.target_port = port
            self.connected = True
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            # Start heartbeat thread
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            if self.on_connection_status:
                self.on_connection_status(True, f"{host}:{port}")
            
            return True
            
        except Exception as e:
            if self.on_connection_status:
                self.on_connection_status(False, f"Connection error: {str(e)}")
            return False
    
    def _receive_loop(self):
        """Data receive loop"""
        buffer = b""
        
        while self.connected and self.socket:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                
                buffer += data
                
                # Handle by line
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line and self.on_data_received:
                        self.on_data_received(line, f"{self.target_host}:{self.target_port}")
                        
            except Exception as e:
                if self.connected:
                    if self.on_connection_status:
                        self.on_connection_status(False, f"Receive error: {str(e)}")
                break
        
        self.connected = False
        if self.on_connection_status:
            self.on_connection_status(False, "Connection closed")

    def _heartbeat_loop(self):
        """Send heartbeat periodically to keep connection"""
        while self.connected and self.socket:
            time.sleep(self.heartbeat_interval)
            if not self.connected or not self.socket:
                break
            try:
                self.socket.send(b"HEARTBEAT\n")
            except Exception as e:
                if self.connected:
                    if self.on_connection_status:
                        self.on_connection_status(False, f"Heartbeat error: {str(e)}")
                break
    
    async def send_data(self, data: str):
        """Send data"""
        if not self.connected or not self.socket:
            return False
        
        try:
            if not data.endswith('\n'):
                data += '\n'
            
            self.socket.send(data.encode('utf-8'))
            return True
            
        except Exception as e:
            if self.on_connection_status:
                self.on_connection_status(False, f"Send error: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect"""
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=1.0)

        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        
        if self.on_connection_status:
            self.on_connection_status(False, "Disconnected")


class RemoteConnectionPanel(Container):
    """Remote connection panel"""
    
    def compose(self) -> ComposeResult:
        yield Label("🌐 Remote Connection Settings", classes="panel-title")
        
        yield Label("📍 Server address:", classes="port-label")
        yield Input(
            placeholder="e.g., 192.168.1.100", 
            id="server_host_input", 
            value="192.168.1.100"
        )
        
        yield Label("🌐 Port number:", classes="port-label")
        yield Input(
            placeholder="e.g., 9999", 
            id="server_port_input", 
            value="9999"
        )
        
        # Connect button
        with Horizontal(classes="button-row"):
            yield Button("Connect", id="connect_btn", variant="success")
            yield Button("Disconnect", id="disconnect_btn", variant="error", disabled=True)
        
        # Action buttons
        with Horizontal(classes="button-row"):
            yield Button("IP Info", id="ip_info_btn", variant="default")
            yield Button("Test Connection", id="ping_btn", variant="default")


class RemoteConnectionStatus(Static):
    """Remote connection status"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_status(False, "Not connected")
    
    def update_status(self, connected: bool, details: str):
        """Update status"""
        local_ip = get_local_ip()
        
        if connected:
            content = f"""🔗 Status: ✅ Connected
━━━━━━━━━━━━━━━━
🎯 Server: {details}
📍 Local IP: {local_ip}
📊 Mode: Remote client
🔄 Receiving data"""
        else:
            content = f"""🔗 Status: ❌ Disconnected
━━━━━━━━━━━━━━━━
📍 Local IP: {local_ip}
📊 Mode: Idle
🔄 Communication stopped
💡 Details: {details}"""
        
        self.update(content)


class RemoteSendPanel(Container):
    """Remote send panel"""
    
    def compose(self) -> ComposeResult:
        yield Label("📤 Send data", classes="panel-title")
        yield Input(placeholder="Enter data to send...", id="send_input")
        with Horizontal(classes="button-row"):
            yield Button("Send", id="send_btn", variant="primary")
            yield Button("Clear", id="clear_btn", variant="default")


class RemoteStats(Static):
    """Remote statistics"""
    
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
        """Reset stats"""
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
        
        content = f"""📊 Communication statistics
━━━━━━━━━━━━━━━━
📥 Received: {self.rx_count:,} ({self.rx_bytes:,} B)
📤 Sent: {self.tx_count:,} ({self.tx_bytes:,} B)
⏱️  Time: {elapsed_str}
📈 Receive rate: {rate:.1f} pkt/s"""
        
        self.update(content)


class RemoteClientDashboard(App):
    """Remote Client Dashboard"""
    
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
            # Left panel
            with Vertical(id="left_panel"):
                yield RemoteConnectionPanel(id="connection_panel")
                yield RemoteSendPanel(id="send_panel")
                yield RemoteStats(id="stats_panel")
                yield RemoteConnectionStatus(id="status_panel")
            
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
        table.add_columns("Time", "Direction", "Data", "Length", "Source")
        table.cursor_type = "row"
        
        # Initialize logs
        log = self.query_one("#log_view", RichLog)
        log.write("📡 Remote Client Dashboard started\n")
        log.write("🌐 Can connect to hybrid dashboard on another PC\n")
        log.write(f"📍 Local IP: {get_local_ip()}\n")
        log.write("💡 Press 'r' to reconnect, 'i' for IP info\n")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
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
        """Connect to server"""
        host = self.query_one("#server_host_input", Input).value.strip()
        port_str = self.query_one("#server_port_input", Input).value.strip()
        
        if not host:
            self.log_message("❌ Please enter server host")
            return
        
        try:
            port = int(port_str) if port_str else 9999
        except ValueError:
            self.log_message("❌ Please enter a valid port number")
            return
        
        self.log_message(f"🔄 Connecting to {host}:{port}...")
        if await self.client_manager.connect(host, port):
            self.connected = True
            self.update_button_states()
            self.log_message(f"✅ Connected to {host}:{port}")
            
            # Reset stats
            stats = self.query_one("#stats_panel", RemoteStats)
            stats.reset_stats()
        else:
            self.log_message(f"❌ Failed to connect to {host}:{port}")
    
    async def disconnect_from_server(self):
        """Disconnect from server"""
        self.client_manager.disconnect()
        self.connected = False
        self.update_button_states()
    
    async def test_connection(self):
        """Test Connection"""
        host = self.query_one("#server_host_input", Input).value.strip()
        port_str = self.query_one("#server_port_input", Input).value.strip()
        
        if not host:
            self.log_message("❌ Please enter host to test")
            return
        
        try:
            port = int(port_str) if port_str else 9999
        except ValueError:
            port = 9999
        
        self.log_message(f"🔍 Testing connection to {host}:{port}...")
        
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5.0)
            result = test_socket.connect_ex((host, port))
            test_socket.close()
            
            if result == 0:
                self.log_message(f"✅ Connection test successful to {host}:{port}")
            else:
                self.log_message(f"❌ Connection test failed to {host}:{port} (Error code: {result})")
                
        except Exception as e:
            self.log_message(f"❌ Connection test error: {str(e)}")
    
    def update_button_states(self):
        """Update button states"""
        self.query_one("#connect_btn", Button).disabled = self.connected
        self.query_one("#disconnect_btn", Button).disabled = not self.connected
    
    def on_connection_status(self, connected: bool, details: str):
        """Handle connection status changes"""
        self.call_later(self._update_connection_status, connected, details)
    
    def _update_connection_status(self, connected: bool, details: str):
        """Update status (UI thread)"""
        self.connected = connected
        status = self.query_one("#status_panel", RemoteConnectionStatus)
        status.update_status(connected, details)
        self.update_button_states()
        self.log_message(f"🔗 Connection status changed: {details}")
    
    def on_data_received(self, data: bytes, source: str):
        """Data receive handler"""
        self.call_later(self._handle_received_data, data, source)
    
    def _handle_received_data(self, data: bytes, source: str):
        """Handle received data (UI thread)"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if data_str:
                self.log_message(f"📥 Received ({source}): {data_str}")
                self.add_to_data_table("RX", data_str, len(data), source)
                
                # Update stats
                stats = self.query_one("#stats_panel", RemoteStats)
                stats.update_stats("RX", len(data))
                
                self.update_sparkline(len(data))
                
        except Exception as e:
            self.log_message(f"❌ Data processing error: {str(e)}")
    
    async def send_data(self):
        """Send data"""
        if not self.connected:
            self.log_message("❌ Not connected to server")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            return
        
        if await self.client_manager.send_data(data):
            self.log_message(f"📤 Sent: {data}")
            send_input.value = ""
            
            # Update stats
            stats = self.query_one("#stats_panel", RemoteStats)
            stats.update_stats("TX", len(data.encode()))
            
            # Add to data table
            self.add_to_data_table("TX", data, len(data.encode()), "Local")
        else:
            self.log_message("❌ Send failed")
    
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
    
    def action_ip_info(self) -> None:
        """Show IP info"""
        local_ip = get_local_ip()
        self.log_message(f"📍 Local IP: {local_ip}")
        
        if self.connected:
            target = f"{self.client_manager.target_host}:{self.client_manager.target_port}"
            self.log_message(f"🎯 Connected target: {target}")
        
        # Attempt to get network info
        try:
            hostname = socket.gethostname()
            self.log_message(f"🖥️ Host name: {hostname}")
        except:
            pass
    
    async def action_reconnect(self) -> None:
        """Reconnect"""
        if self.connected:
            await self.disconnect_from_server()
            # Wait a moment
            await asyncio.sleep(1)
        
        await self.connect_to_server()
    
    def action_clear_data(self) -> None:
        """Clear data"""
        table = self.query_one("#data_table", DataTable)
        table.clear()
        
        sparkline = self.query_one("#sparkline", Sparkline)
        self.sparkline_data.clear()
        sparkline.data = []
        
        self.data_buffer.clear()
        
        # Reset stats
        stats = self.query_one("#stats_panel", RemoteStats)
        stats.reset_stats()
        
        self.log_message("🗑️ Data cleared")
    
    def action_save_data(self) -> None:
        """Save CSV"""
        if not self.data_buffer:
            self.log_message("💾 No data to save")
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
            
            self.log_message(f"💾 {filename} Saved to {len(self.data_buffer)} entries)")
        except Exception as e:
            self.log_message(f"❌ Save error: {str(e)}")
    
    async def action_quit(self) -> None:
        """Exit application"""
        if self.connected:
            self.client_manager.disconnect()
        self.exit()


def main():
    """Main function"""
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = RemoteClientDashboard()
    app.run()


if __name__ == "__main__":
    main()
