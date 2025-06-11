#!/usr/bin/env python3
"""
Enhanced Serial Communication Dashboard
with automatic port detection and selection
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

# Import the library created earlier
try:
    from modern_serial_comm import ModernSerialComm, SerialConfig
except ImportError:
    print("Error: modern_serial_comm.py not found")
    print("Place it in the same directory")
    sys.exit(1)


def detect_available_ports() -> List[tuple]:
    """Detect available serial ports"""
    ports = []
    
    try:
        import serial.tools.list_ports
        for port in serial.tools.list_ports.comports():
            description = f"{port.device} - {port.description}"
            ports.append((port.device, description))
    except ImportError:
        # Manual detection when pyserial.tools.list_ports is unavailable
        if sys.platform == "win32":
            # Windows COM ports
            for i in range(1, 21):
                port_name = f"COM{i}"
                ports.append((port_name, f"COM Port {i}"))
        else:
            # Linux/Unix serial ports
            patterns = ['/dev/ttyS*', '/dev/ttyUSB*', '/dev/ttyACM*', '/dev/ttyAMA*']
            for pattern in patterns:
                for device in glob.glob(pattern):
                    if os.path.exists(device):
                        ports.append((device, f"Serial Device {os.path.basename(device)}"))
    
    # Add loopback for testing
    ports.append(("loop://", "Loop back (test)"))
    
    return ports


class PortSelector(Container):
    """Widget for selecting a serial port"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.available_ports = detect_available_ports()
    
    def compose(self) -> ComposeResult:
        yield Label("🔌 Select Port", classes="panel-title")
        
        # Build list of available ports as (label, value)
        port_options = [(f"{port} - {desc}", port) for port, desc in self.available_ports]
        
        if port_options:
            # Default selection depending on platform
            default_port = "/dev/ttyS0" if sys.platform != "win32" else "COM2"
            
            # Check if the default port exists in the available list
            default_value = None
            for port, desc in self.available_ports:
                if port == default_port:
                    default_value = port  # set value part
                    break
            
            # Use first port when default is not found
            if not default_value and self.available_ports:
                default_value = self.available_ports[0][0]
            
            yield Select(
                port_options,
                value=default_value,
                id="port_select"
            )
        else:
            yield Label("❌ No available ports found")
        
        yield Label("Or enter manually:", classes="small-label")
        yield Input(placeholder="Enter port name manually...", id="manual_port_input")


class ConnectionPanel(Container):
    """Panel for managing connections"""
    
    def compose(self) -> ComposeResult:
        yield PortSelector(id="port_selector")
        with Horizontal(classes="button-row"):
            yield Button("Connect", id="connect_btn", variant="success")
            yield Button("Disconnect", id="disconnect_btn", variant="error", disabled=True)
            yield Button("Refresh Ports", id="refresh_ports_btn", variant="default")


class EnhancedSerialDashboard(App):
    """Enhanced serial dashboard"""
    
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
        """Build the user interface"""
        yield Header()
        
        with Horizontal():
            # Left panel
            with Vertical(id="left_panel"):
                yield ConnectionPanel(id="connection_panel")
                yield SendPanel(id="send_panel")
                yield SerialStats(id="stats_panel")
            
            # Right main area
            with Vertical(id="main_area"):
                # Data table
                yield DataTable(id="data_table")
                
                # Sparkline
                yield Sparkline(
                    id="sparkline",
                    data=[],
                    summary_function=max
                )
                
                # Log view
                yield RichLog(id="log_view", highlight=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize when the app starts"""
        # Set up columns for the data table
        table = self.query_one("#data_table", DataTable)
        table.add_columns("Time", "Dir", "Data", "Length")
        table.cursor_type = "row"
        
        # Initialize log
        log = self.query_one("#log_view", RichLog)
        log.write("📡 Enhanced Serial Dashboard started\n")
        log.write("🔍 Automatically detected available ports\n")
        log.write("💡 Press 'q' to quit, 'c' to clear data, 's' to save CSV, 'r' to refresh ports\n")
        
        # Show detected ports
        ports = detect_available_ports()
        log.write(f"🔌 Detected ports: {len(ports)}\n")
        for port, desc in ports[:5]:  # show first five
            log.write(f"   • {port} - {desc}\n")
        
        # Initialize sparkline
        sparkline = self.query_one("#sparkline", Sparkline)
        sparkline.data = []
    
    def get_selected_port(self) -> str:
        """Return the selected port"""
        try:
            # Port selected via the Select widget
            port_select = self.query_one("#port_select", Select)
            selected_port = port_select.value
            
            # Check manual input
            manual_input = self.query_one("#manual_port_input", Input)
            manual_port = manual_input.value.strip()
            
            if manual_port:
                return manual_port
            elif selected_port:
                return selected_port
            else:
                return ""
                
        except Exception as e:
            self.log_message(f"❌ Failed to get port: {e}")
            return ""
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button click"""
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
        """Update the list of serial ports"""
        self.log_message("🔄 Refreshing port list...")
        
        # Get the updated port list
        ports = detect_available_ports()
        
        # Update the Select widget
        try:
            port_select = self.query_one("#port_select", Select)
            port_options = [(desc, port) for port, desc in ports]
            
            # Keep current selection
            current_value = port_select.value
            
            # Update options (may require creating a new Select due to Textual limitations)
            self.log_message(f"🔌 Detected {len(ports)} ports")
            
        except Exception as e:
            self.log_message(f"❌ Error refreshing ports: {e}")
    
    def action_refresh_ports(self) -> None:
        """Action to refresh ports"""
        asyncio.create_task(self.refresh_ports())
    
    async def connect_serial(self):
        """Establish a serial connection"""
        port = self.get_selected_port()
        
        if not port:
            self.log_message("❌ Please select a port")
            return
        
        try:
            # Select config file based on platform
            if sys.platform == "win32":
                config_file = "serial_config_windows.ini"
            else:
                config_file = "serial_config_linux.ini"
            
            # Create serial communication object
            self.serial_comm = ModernSerialComm(config_file)
            
            # Set the selected port
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
    
    # The remaining methods are the same as in the original SerialDashboard
    # send_data, on_data_received, _handle_received_data,
    # add_to_data_table, update_sparkline, log_message,
    # action_clear_data, action_save_data, action_quit
    
    async def send_data(self):
        """Send data through the serial connection"""
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


# SendPanel and SerialStats are the same as in the original code
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
        """Update statistics"""
        if direction == "RX":
            self.rx_count += 1
            self.rx_bytes += byte_count
        elif direction == "TX":
            self.tx_count += 1
            self.tx_bytes += byte_count
        
        self.update_display()
    
    def update_display(self):
        """Refresh the displayed stats"""
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


def main():
    """Main execution function"""
    import sys
    
    # Windows event loop policy
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the application
    app = EnhancedSerialDashboard()
    app.run()


if __name__ == "__main__":
    main()
