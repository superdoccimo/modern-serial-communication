#!/usr/bin/env python3
"""
Dual Port Serial Communication Dashboard
Supports separate transmit and receive ports.
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

# Library import
try:
    from modern_serial_comm import ModernSerialComm, SerialConfig
except ImportError:
    print("Error: modern_serial_comm.py not found")
    sys.exit(1)


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
    
    # Add test loopback
    ports.append(("loop://", "Loop back (test)"))
    return ports


class DualPortConnectionPanel(Container):
    """Connection panel with TX/RX separation"""
    
    def compose(self) -> ComposeResult:
        yield Label("🔌 Connection Settings", classes="panel-title")
        
        # Default ports per platform
        if sys.platform == "win32":
            default_rx_port = "COM2"
            default_tx_port = "COM1"
        else:
            default_rx_port = "/dev/ttyS0"
            default_tx_port = "/dev/ttyS0"
        
        # Receive port
        yield Label("📥 Receive Port:", classes="port-label")
        yield Input(
            placeholder=f"for RX e.g., {default_rx_port}",
            id="rx_port_input", 
            value=default_rx_port
        )
        
        # Separate transmit and receive
        yield Checkbox("Separate ports", id="separate_ports_checkbox")
        
        # Transmit port (hidden initially)
        yield Label("📤 Transmit Port:", classes="port-label", id="tx_port_label")
        yield Input(
            placeholder=f"for TX e.g., {default_tx_port}",
            id="tx_port_input", 
            value=default_tx_port
        )
        
        # Connect buttons
        with Horizontal(classes="button-row"):
            yield Button("Connect", id="connect_btn", variant="success")
            yield Button("Disconnect", id="disconnect_btn", variant="error", disabled=True)
        
        # Utility buttons
        with Horizontal(classes="button-row"):
            yield Button("Detect Ports", id="detect_ports_btn", variant="default")
            yield Button("Preset", id="preset_btn", variant="default")


class ConnectionStatus(Static):
    """Widget to show connection status"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_status(False, None, None)
    
    def update_status(self, connected: bool, rx_port: Optional[str], tx_port: Optional[str]):
        """Update the displayed connection state"""
        if connected:
            if rx_port == tx_port:
                content = f"""🔗 Status: ✅ Connected
━━━━━━━━━━━━━━━━
📍 Port: {rx_port}
📊 Mode: Single port
🔄 Bidirectional"""
            else:
                content = f"""🔗 Status: ✅ Connected
━━━━━━━━━━━━━━━━
📥 RX: {rx_port}
📤 TX: {tx_port}
📊 Mode: Dual port
🔄 Separate"""
        else:
            content = """🔗 Status: ❌ Disconnected
━━━━━━━━━━━━━━━━
📍 Port: None
📊 Mode: Idle
🔄 Stopped"""
        
        self.update(content)


class SendPanel(Container):
    """Panel for sending data"""
    
    def compose(self) -> ComposeResult:
        yield Label("📤 Send Data", classes="panel-title")
        yield Input(placeholder="Enter data to send...", id="send_input")
        with Horizontal(classes="button-row"):
            yield Button("Send", id="send_btn", variant="primary")
            yield Button("Clear", id="clear_btn", variant="default")


class SerialStats(Static):
    """Widget showing statistics"""
    
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
        
        content = f"""📊 Stats
━━━━━━━━━━━━━━━━
📥 RX: {self.rx_count:,} ({self.rx_bytes:,} B)
📤 TX: {self.tx_count:,} ({self.tx_bytes:,} B)
⏱️  Time: {elapsed_str}
📈 Rate: {rate:.1f} pkt/s"""
        
        self.update(content)


class DualPortDashboard(App):
    """Dashboard supporting separate TX and RX ports"""
    
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
        self.rx_serial_comm = None  # for receiving
        self.tx_serial_comm = None  # for transmitting
        self.data_buffer = []
        self.sparkline_data = []
        self.connected = False
        self.dual_port_mode = False
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            # Left panel
            with Vertical(id="left_panel"):
                yield DualPortConnectionPanel(id="connection_panel")
                yield SendPanel(id="send_panel")
                yield SerialStats(id="stats_panel")
                yield ConnectionStatus(id="status_panel")
            
            # Right main area
            with Vertical(id="main_area"):
                yield DataTable(id="data_table")
                yield Sparkline(id="sparkline", data=[], summary_function=max)
                yield RichLog(id="log_view", highlight=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize when the app starts"""
        # Initialize data table
        table = self.query_one("#data_table", DataTable)
        table.add_columns("Time", "Dir", "Data", "Len", "Port")
        table.cursor_type = "row"
        
        # Initialize log
        log = self.query_one("#log_view", RichLog)
        log.write("📡 Dual Port Serial Dashboard started\n")
        log.write("💡 Use the checkbox to separate TX and RX ports\n")
        log.write("🔧 Press 't' to toggle dual port, 'd' to detect ports\n")
        
        # Set initial state
        self.update_port_visibility(False)
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state change"""
        if event.checkbox.id == "separate_ports_checkbox":
            self.dual_port_mode = event.value
            self.update_port_visibility(event.value)
            self.log_message(f"🔄 Dual port mode: {'enabled' if event.value else 'disabled'}")
    
    def update_port_visibility(self, show_tx_port: bool):
        """Show or hide the TX port input"""
        tx_label = self.query_one("#tx_port_label", Label)
        tx_input = self.query_one("#tx_port_input", Input)
        
        if show_tx_port:
            tx_label.styles.display = "block"
            tx_input.styles.display = "block"
        else:
            tx_label.styles.display = "none"
            tx_input.styles.display = "none"
    
    def action_toggle_dual_port(self) -> None:
        """Toggle dual port mode"""
        checkbox = self.query_one("#separate_ports_checkbox", Checkbox)
        checkbox.value = not checkbox.value
        self.dual_port_mode = checkbox.value
        self.update_port_visibility(checkbox.value)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Button click handler"""
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
        """Detect available ports"""
        self.log_message("🔍 Detecting ports...")
        ports = detect_available_ports()
        self.log_message(f"🔌 Detected {len(ports)} ports")
        
        for port, desc in ports[:8]:  # log first 8
            self.log_message(f"   • {port} - {desc}")
    
    def set_preset_port(self) -> None:
        """Apply preset ports"""
        # Recommended ports by platform
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
        
        self.log_message(f"🎯 Preset applied - RX: {rx_preset}, TX: {tx_preset}")
    
    async def connect_serial(self):
        """Establish serial connection"""
        rx_port = self.query_one("#rx_port_input", Input).value.strip()
        
        if not rx_port:
            self.log_message("❌ Please enter the receive port")
            return
        
        try:
            # Choose config file per platform
            if sys.platform == "win32":
                config_file = "serial_config_windows.ini"
            else:
                config_file = "serial_config_linux.ini"
            
            # Create RX connection
            if not os.path.exists(config_file):
                self.log_message(f"⚠️ {config_file} not found, using manual settings")
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
            
            # Set receive callback
            self.rx_serial_comm.set_receive_callback(self.on_data_received)
            
            # Try RX connection
            if not await self.rx_serial_comm.connect():
                self.log_message(f"❌ Failed to connect RX port {rx_port}")
                return
            
            self.log_message(f"✅ Connected RX port {rx_port}")
            
            # In dual port mode also connect TX
            if self.dual_port_mode:
                tx_port = self.query_one("#tx_port_input", Input).value.strip()
                
                if not tx_port:
                    self.log_message("❌ Please enter the transmit port")
                    await self.rx_serial_comm.disconnect()
                    return
                
                if tx_port != rx_port:
                    # Create TX connection
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
                    
                    # Try TX connection
                    if await self.tx_serial_comm.connect():
                        self.log_message(f"✅ Connected TX port {tx_port}")
                    else:
                        self.log_message(f"❌ Failed to connect TX port {tx_port}")
                        await self.rx_serial_comm.disconnect()
                        return
                else:
                    # Use RX port for TX if same
                    self.tx_serial_comm = self.rx_serial_comm
                    self.log_message(f"📍 Using same port {tx_port} for RX/TX")
            else:
                # Single port mode
                self.tx_serial_comm = self.rx_serial_comm
                tx_port = rx_port
            
            self.connected = True
            
            # Update button state
            self.query_one("#connect_btn", Button).disabled = True
            self.query_one("#disconnect_btn", Button).disabled = False
            
            # Update connection status
            status = self.query_one("#status_panel", ConnectionStatus)
            status.update_status(True, rx_port, tx_port if self.dual_port_mode else rx_port)
            
        except Exception as e:
            self.log_message(f"❌ Connection error: {str(e)}")
    
    async def disconnect_serial(self):
        """Disconnect serial ports"""
        if self.connected:
            if self.rx_serial_comm:
                await self.rx_serial_comm.disconnect()
                self.log_message("🔌 RX port disconnected")
            
            if self.tx_serial_comm and self.tx_serial_comm != self.rx_serial_comm:
                await self.tx_serial_comm.disconnect()
                self.log_message("🔌 TX port disconnected")
            
            self.rx_serial_comm = None
            self.tx_serial_comm = None
            self.connected = False
            
            # Update button state
            self.query_one("#connect_btn", Button).disabled = False
            self.query_one("#disconnect_btn", Button).disabled = True
            
            # Update connection status
            status = self.query_one("#status_panel", ConnectionStatus)
            status.update_status(False, None, None)
    
    async def send_data(self):
        """Send entered data"""
        if not self.connected or not self.tx_serial_comm:
            self.log_message("❌ Transmit port is not connected")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            return
        
        # Append line ending if missing
        if not data.endswith(('\r\n', '\r', '\n')):
            data += '\r\n'
        
        if await self.tx_serial_comm.send_string(data):
            tx_port = self.tx_serial_comm.port
            self.log_message(f"📤 Sent ({tx_port}): {data.strip()}")
            send_input.value = ""
            
            # Update stats
            stats = self.query_one("#stats_panel", SerialStats)
            stats.update_stats("TX", len(data.encode()))
            
            # Add to data table
            self.add_to_data_table("TX", data.strip(), len(data.encode()), tx_port)
        else:
            self.log_message("❌ Failed to send")
    
    def on_data_received(self, data: bytes, direction: str):
        """Callback for incoming data"""
        self.call_later(self._handle_received_data, data, direction)
    
    def _handle_received_data(self, data: bytes, direction: str):
        """Process received data on the UI thread"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if direction == "RX":
                rx_port = self.rx_serial_comm.port if self.rx_serial_comm else "unknown"
                self.log_message(f"📥 Received ({rx_port}): {data_str}")
                self.add_to_data_table("RX", data_str, len(data), rx_port)
                
                stats = self.query_one("#stats_panel", SerialStats)
                stats.update_stats("RX", len(data))
                
                self.update_sparkline(len(data))
        except Exception as e:
            self.log_message(f"❌ Data handling error: {str(e)}")
    
    def add_to_data_table(self, direction: str, data: str, length: int, port: str):
        """Add a row to the data table"""
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
        """Update sparkline graph"""
        sparkline = self.query_one("#sparkline", Sparkline)
        self.sparkline_data.append(data_length)
        
        if len(self.sparkline_data) > 100:
            self.sparkline_data.pop(0)
        
        sparkline.data = self.sparkline_data
    
    def log_message(self, message: str):
        """Output a log message"""
        log = self.query_one("#log_view", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")
    
    def action_clear_data(self) -> None:
        """Clear all displayed data"""
        table = self.query_one("#data_table", DataTable)
        table.clear()
        
        sparkline = self.query_one("#sparkline", Sparkline)
        self.sparkline_data.clear()
        sparkline.data = []
        
        self.data_buffer.clear()
        self.log_message("🗑️ Cleared data")
    
    def action_save_data(self) -> None:
        """Save data to CSV"""
        if not self.data_buffer:
            self.log_message("💾 No data to save")
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
            
            self.log_message(f"💾 Saved to {filename} ({len(self.data_buffer)} records)")
        except Exception as e:
            self.log_message(f"❌ Save error: {str(e)}")
    
    async def action_quit(self) -> None:
        """Exit the application"""
        if self.connected:
            await self.disconnect_serial()
        self.exit()


def main():
    """Entry point"""
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = DualPortDashboard()
    app.run()


if __name__ == "__main__":
    main()
