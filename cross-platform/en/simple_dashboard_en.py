#!/usr/bin/env python3
"""
Simple Enhanced Serial Communication Dashboard
Input with port detection (without Select widget)
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    DataTable, Header, Footer, Static, 
    Button, Input, Label, RichLog, Sparkline
)
from textual.binding import Binding
import asyncio
import sys
import glob
import os
from datetime import datetime
from typing import List, Dict, Any

# Import library
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
    
    # Add loopback for testing
    ports.append(("loop://", "Loop back (test)"))
    return ports


class PortInfo(Static):
    """Widget to display port information"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_port_list()
    
    def update_port_list(self):
        """Refresh the list of ports"""
        ports = detect_available_ports()
        
        content = "🔌 Available ports:\n"
        content += "━━━━━━━━━━━━━━━━\n"
        
        if ports:
            for i, (port, desc) in enumerate(ports[:8]):  # show first eight
                content += f"{i+1:2d}. {port}\n"
                if len(desc) > 20:
                    content += f"    {desc[:20]}...\n"
                else:
                    content += f"    {desc}\n"
            
            if len(ports) > 8:
                content += f"... +{len(ports)-8} more\n"
        else:
            content += "❌ No ports found\n"
        
        self.update(content)


class SimpleConnectionPanel(Container):
    """Simple connection control panel"""
    
    def compose(self) -> ComposeResult:
        yield Label("🔌 Connection Control", classes="panel-title")
        
        # Default port per platform
        default_port = "/dev/ttyS0" if sys.platform != "win32" else "COM2"
        
        yield Input(
            placeholder=f"Port name (e.g. {default_port})",
            id="port_input", 
            value=default_port
        )
        
        with Horizontal(classes="button-row"):
            yield Button("Connect", id="connect_btn", variant="success")
            yield Button("Disconnect", id="disconnect_btn", variant="error", disabled=True)
        
        with Horizontal(classes="button-row"):
            yield Button("Detect Ports", id="detect_ports_btn", variant="default")
            yield Button("Preset", id="preset_btn", variant="default")


class SendPanel(Container):
    """Panel for sending data"""
    
    def compose(self) -> ComposeResult:
        yield Label("📤 Send Data", classes="panel-title")
        yield Input(placeholder="Enter data to send...", id="send_input")
        with Horizontal(classes="button-row"):
            yield Button("Send", id="send_btn", variant="primary")
            yield Button("Clear", id="clear_btn", variant="default")


class SerialStats(Static):
    """Widget to display statistics"""
    
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


class SimpleEnhancedDashboard(App):
    """Simplified enhanced dashboard"""
    
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
        margin: 1 0 0 0;
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
    
    #port_info_panel {
        height: auto;
        border: solid $primary;
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
    
    Input {
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "clear_data", "Clear Data", show=True),
        Binding("s", "save_data", "Save CSV", show=True),
        Binding("d", "detect_ports", "Detect Ports", show=True),
    ]
    
    TITLE = "📡 Simple Enhanced Serial Dashboard"
    SUB_TITLE = "Auto-detect ports & Cross-platform support"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_comm = None
        self.data_buffer = []
        self.sparkline_data = []
        self.connected = False
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            # Left panel
            with Vertical(id="left_panel"):
                yield SimpleConnectionPanel(id="connection_panel")
                yield SendPanel(id="send_panel")
                yield SerialStats(id="stats_panel")
                yield PortInfo(id="port_info_panel")
            
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
        table.add_columns("Time", "Dir", "Data", "Length")
        table.cursor_type = "row"
        
        # Initialize log
        log = self.query_one("#log_view", RichLog)
        log.write("📡 Simple Enhanced Serial Dashboard started\n")
        log.write("💡 Press 'd' to detect ports, 'q' to quit, 'c' to clear data, 's' to save CSV\n")
        
        # Detect ports on startup
        self.action_detect_ports()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
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
        """Action to detect ports"""
        self.log_message("🔍 Detecting ports...")
        
        # Update port information
        port_info = self.query_one("#port_info_panel", PortInfo)
        port_info.update_port_list()
        
        # Log detection results
        ports = detect_available_ports()
        self.log_message(f"🔌 Detected {len(ports)} ports")
        
        for port, desc in ports[:5]:  # log first five
            self.log_message(f"   • {port} - {desc}")
    
    def set_preset_port(self) -> None:
        """Set a preset port"""
        # Recommended port per platform
        if sys.platform == "win32":
            preset_port = "COM2"
        else:
            preset_port = "/dev/ttyS0"
        
        port_input = self.query_one("#port_input", Input)
        port_input.value = preset_port
        self.log_message(f"🎯 Preset port set: {preset_port}")
    
    async def connect_serial(self):
        """Establish a serial connection"""
        port_input = self.query_one("#port_input", Input)
        port = port_input.value.strip()
        
        if not port:
            self.log_message("❌ Please enter a port")
            return
        
        try:
            # Choose config file based on platform
            if sys.platform == "win32":
                config_file = "serial_config_windows.ini"
            else:
                config_file = "serial_config_linux.ini"
            
            # Create config manually if file does not exist
            if not os.path.exists(config_file):
                self.log_message(f"⚠️ {config_file} not found. Using manual settings")
                config = SerialConfig()
                config.config.set('SERIAL', 'port', port)
                config.config.set('SERIAL', 'baudrate', '9600')
                
                self.serial_comm = ModernSerialComm()
                self.serial_comm.config_manager = config
                self.serial_comm._load_settings_from_config()
            else:
                # Use configuration file
                self.serial_comm = ModernSerialComm(config_file)
                self.serial_comm.config_manager.config.set('SERIAL', 'port', port)
                self.serial_comm._load_settings_from_config()
            
            # Set callback
            self.serial_comm.set_receive_callback(self.on_data_received)
            
            # Attempt connection
            if await self.serial_comm.connect():
                self.connected = True
                self.log_message(f"✅ Connected to {port}")
                
                # Update button states
                self.query_one("#connect_btn", Button).disabled = True
                self.query_one("#disconnect_btn", Button).disabled = False
            else:
                self.log_message(f"❌ Failed to connect to {port}")
                
        except Exception as e:
            self.log_message(f"❌ Connection error: {str(e)}")
    
    async def disconnect_serial(self):
        """Disconnect the serial connection"""
        if self.serial_comm and self.connected:
            await self.serial_comm.disconnect()
            self.connected = False
            self.log_message("🔌 Disconnected")
            
            # Update button states
            self.query_one("#connect_btn", Button).disabled = False
            self.query_one("#disconnect_btn", Button).disabled = True
    
    async def send_data(self):
        """Send data"""
        if not self.connected or not self.serial_comm:
            self.log_message("❌ Not connected")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            return
        
        # Append newline if missing
        if not data.endswith(('\r\n', '\r', '\n')):
            data += '\r\n'
        
        if await self.serial_comm.send_string(data):
            self.log_message(f"📤 Sent: {data.strip()}")
            send_input.value = ""
            
            # Update statistics
            stats = self.query_one("#stats_panel", SerialStats)
            stats.update_stats("TX", len(data.encode()))
            
            # Add to data table
            self.add_to_data_table("TX", data.strip(), len(data.encode()))
        else:
            self.log_message("❌ Failed to send")
    
    def on_data_received(self, data: bytes, direction: str):
        """Handle received data"""
        self.call_later(self._handle_received_data, data, direction)
    
    def _handle_received_data(self, data: bytes, direction: str):
        """Process received data on the UI thread"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if direction == "RX":
                self.log_message(f"📥 Received: {data_str}")
                self.add_to_data_table("RX", data_str, len(data))
                
                stats = self.query_one("#stats_panel", SerialStats)
                stats.update_stats("RX", len(data))
                
                self.update_sparkline(len(data))
        except Exception as e:
            self.log_message(f"❌ Data handling error: {str(e)}")
    
    def add_to_data_table(self, direction: str, data: str, length: int):
        """Add a row to the data table"""
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
        """Update the sparkline widget"""
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
        """Clear displayed data"""
        table = self.query_one("#data_table", DataTable)
        table.clear()
        
        sparkline = self.query_one("#sparkline", Sparkline)
        self.sparkline_data.clear()
        sparkline.data = []
        
        self.data_buffer.clear()
        self.log_message("🗑️ Data cleared")
    
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
                writer.writerow(['timestamp', 'direction', 'data', 'length'])
                
                for entry in self.data_buffer:
                    writer.writerow([
                        entry['timestamp'].isoformat(),
                        entry['direction'],
                        entry['data'],
                        entry['length']
                    ])
            
            self.log_message(f"💾 Saved to {filename} ({len(self.data_buffer)} entries)")
        except Exception as e:
            self.log_message(f"❌ Save error: {str(e)}")
    
    async def action_quit(self) -> None:
        """Exit the application"""
        if self.serial_comm and self.connected:
            await self.serial_comm.disconnect()
        self.exit()


def main():
    """Main execution function"""
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = SimpleEnhancedDashboard()
    app.run()


if __name__ == "__main__":
    main()
