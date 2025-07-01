#!/usr/bin/env python3
"""
Final Working Dual Port Serial Communication Dashboard
Uses the operation method confirmed during debugging
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

# Import libraries
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
    """Final working dual port dashboard"""
    
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
        
        # Header area (connection control)
        with Container(id="header_area"):
            # Row 1: Receive port (always shown)
            with Horizontal(classes="input-row"):
                yield Label("📥RX:", classes="port-label-short")
                yield Input(
                    value="COM1" if sys.platform == "win32" else "/dev/ttyS0", 
                    id="rx_port_input", 
                    classes="port-input"
                )
            
            # Row 2: Transmit port (always shown, disabled initially)
            with Horizontal(classes="input-row", id="tx_port_row"):
                yield Label("📤TX:", classes="port-label-short")
                yield Input(
                    value="COM2" if sys.platform == "win32" else "/dev/ttyS1", 
                    id="tx_port_input", 
                    classes="port-input",
                    disabled=True  # Disabled initially
                )
            
            # Row 3: Checkbox
            yield Checkbox("Separate RX/TX", id="separate_ports_checkbox", classes="compact-checkbox")
            
            # Row 4: Connection buttons (always shown)
            with Horizontal(classes="button-row"):
                yield Button("Connect", id="connect_btn", variant="success", classes="compact-btn")
                yield Button("Disconnect", id="disconnect_btn", variant="error", disabled=True, classes="compact-btn")
                yield Button("Detect", id="detect_ports_btn", variant="default", classes="compact-btn")
            
            # Row 5: Send area
            with Horizontal(classes="send-row"):
                yield Input(placeholder="Data to send...", id="send_input", classes="send-input")
                yield Button("Send", id="send_btn", variant="primary", classes="send-btn")
        
        # Main area
        with Horizontal(id="main_area"):
            # Left: control panel
            with Vertical(id="control_panel"):
                yield Label("🎛️ Control")
                yield Button("Clear", id="clear_data_btn", variant="default")
                yield Button("Save", id="save_data_btn", variant="default")
                yield Label("💡 VMware Example:")
                yield Label("Win: COM1↔COM2")
                yield Label("Lin: /dev/ttyS0↔/dev/ttyS1")
                yield Label("")
                yield Label("🎮 Controls:")
                yield Label("q: Quit")
                yield Label("c: Clear")
                yield Label("d: Detect Ports")
                yield Label("t: Toggle Split")
            
            # Right: data area
            with Vertical(id="data_area"):
                yield DataTable(id="data_table")
                yield RichLog(id="log_view", highlight=True)
        
        # Status bar
        yield Static("🔴 Disconnected | 📥0 📤0", id="status_bar")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize when the app starts"""
        # Initialize data table
        table = self.query_one("#data_table", DataTable)
        table.add_columns("Time", "Dir", "Data", "Port")
        table.cursor_type = "row"
        
        # Initialize log
        log = self.query_one("#log_view", RichLog)
        log.write("📡 Final Working Dashboard started\n")
        log.write("🎉 Operation verified during debugging\n")
        log.write("💡 Supports bidirectional communication in VMware\n")
        
        # Show VMware configuration example
        if sys.platform == "win32":
            log.write("🖥️ Recommended settings on Windows host:\n")
            log.write("   RX: COM1 (incoming from Linux)\n")
            log.write("   TX: COM2 (outgoing to Linux)\n")
        else:
            log.write("🐧 Recommended settings on Linux guest:\n")
            log.write("   RX: /dev/ttyS0 (incoming from Windows)\n")
            log.write("   TX: /dev/ttyS1 (outgoing to Windows)\n")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes"""
        if event.checkbox.id == "separate_ports_checkbox":
            self.dual_port_mode = event.value
            self.update_tx_port_state(event.value)
            self.log_message(f"🔄 Separate RX/TX: {'enabled' if event.value else 'disabled'}")
    
    def update_tx_port_state(self, enable_tx_port: bool):
        """Enable or disable the transmit port"""
        tx_input = self.query_one("#tx_port_input", Input)
        tx_input.disabled = not enable_tx_port
        
        if enable_tx_port:
            tx_input.styles.opacity = 1.0
        else:
            tx_input.styles.opacity = 0.5
    
    def action_toggle_dual_port(self) -> None:
        """Toggle dual port mode"""
        checkbox = self.query_one("#separate_ports_checkbox", Checkbox)
        checkbox.value = not checkbox.value
        self.dual_port_mode = checkbox.value
        self.update_tx_port_state(checkbox.value)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
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
        """Action to detect available ports"""
        self.log_message("🔍 Detecting ports...")
        ports = detect_available_ports()
        self.log_message(f"🔌 Detected {len(ports)} ports")
        
        for port, desc in ports[:8]:
            self.log_message(f"  • {port} - {desc}")
    
    async def connect_serial(self):
        """Serial connection using the debug-verified method"""
        rx_port = self.query_one("#rx_port_input", Input).value.strip()
        
        if not rx_port:
            self.log_message("❌ Please enter a receive port")
            return
        
        self.log_message(f"🔌 Starting connection: {rx_port}")
        
        try:
            # Use method confirmed in debugging
            config_file = "serial_config_windows.ini" if sys.platform == "win32" else "serial_config_linux.ini"
            
            # Same approach as simple_dashboard.py
            if not os.path.exists(config_file):
                self.log_message(f"⚠️ {config_file} not found. Using manual settings")
                config = SerialConfig()
                config.config.set('SERIAL', 'port', rx_port)
                config.config.set('SERIAL', 'baudrate', '9600')
                
                self.rx_serial_comm = ModernSerialComm()
                self.rx_serial_comm.config_manager = config
                self.rx_serial_comm._load_settings_from_config()
            else:
                self.log_message(f"📋 Using {config_file}")
                self.rx_serial_comm = ModernSerialComm(config_file)
                self.rx_serial_comm.config_manager.config.set('SERIAL', 'port', rx_port)
                self.rx_serial_comm._load_settings_from_config()
            
            # Set receive callback
            self.rx_serial_comm.set_receive_callback(self.on_data_received)
            
            # Attempt connection
            if not await self.rx_serial_comm.connect():
                self.log_message(f"❌ Failed to connect RX port {rx_port}")
                return
            
            self.log_message(f"✅ RX port {rx_port} connected")
            
            # When in dual port mode
            if self.dual_port_mode:
                tx_port = self.query_one("#tx_port_input", Input).value.strip()
                
                if not tx_port:
                    self.log_message("❌ Please enter a transmit port")
                    await self.rx_serial_comm.disconnect()
                    return
                
                if tx_port != rx_port:
                    self.log_message(f"🔌 Connecting TX port: {tx_port}")
                    
                    # Connection for transmission (same method)
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
                        self.log_message(f"✅ TX port {tx_port} connected")
                    else:
                        self.log_message(f"❌ Failed to connect TX port {tx_port}")
                        await self.rx_serial_comm.disconnect()
                        return
                else:
                    self.tx_serial_comm = self.rx_serial_comm
                    self.log_message(f"📍 Using same port {tx_port} for RX and TX")
            else:
                self.tx_serial_comm = self.rx_serial_comm
                tx_port = rx_port
            
            self.connected = True
            
            # Update button states
            self.query_one("#connect_btn", Button).disabled = True
            self.query_one("#disconnect_btn", Button).disabled = False
            
            # Update status
            self.update_status()
            
            self.log_message("🎉 Connection established! Ready to send/receive")
            self.log_message("💬 Enter a message in the send area to test communication")
            
        except Exception as e:
            self.log_message(f"❌ Connection error: {str(e)}")
    
    async def disconnect_serial(self):
        """Disconnect from the serial port"""
        if self.connected:
            self.log_message("🔌 Starting disconnect...")
            
            if self.rx_serial_comm:
                await self.rx_serial_comm.disconnect()
                self.log_message("🔌 RX port disconnected")
            
            if self.tx_serial_comm and self.tx_serial_comm != self.rx_serial_comm:
                await self.tx_serial_comm.disconnect()
                self.log_message("🔌 TX port disconnected")
            
            self.rx_serial_comm = None
            self.tx_serial_comm = None
            self.connected = False
            
            # Update button states
            self.query_one("#connect_btn", Button).disabled = False
            self.query_one("#disconnect_btn", Button).disabled = True
            
            self.update_status()
            self.log_message("✅ All ports disconnected")
    
    async def send_data(self):
        """Send data"""
        if not self.connected or not self.tx_serial_comm:
            self.log_message("❌ Transmit port not connected")
            return
        
        send_input = self.query_one("#send_input", Input)
        data = send_input.value.strip()
        
        if not data:
            self.log_message("❌ Please enter data to send")
            return
        
        if not data.endswith(('\r\n', '\r', '\n')):
            data += '\r\n'
        
        try:
            if await self.tx_serial_comm.send_string(data):
                tx_port = self.tx_serial_comm.port
                self.log_message(f"📤 Sent successfully({tx_port}): {data.strip()}")
                send_input.value = ""
                self.tx_count += 1
                self.add_to_data_table("TX", data.strip(), tx_port)
                self.update_status()
            else:
                self.log_message("❌ Send failed")
        except Exception as e:
            self.log_message(f"❌ Send error: {str(e)}")
    
    def on_data_received(self, data: bytes, direction: str):
        """Process received data"""
        self.call_later(self._handle_received_data, data, direction)
    
    def _handle_received_data(self, data: bytes, direction: str):
        """Process received data on the UI thread"""
        try:
            data_str = data.decode('utf-8', errors='replace').strip()
            
            if direction == "RX":
                rx_port = self.rx_serial_comm.port if self.rx_serial_comm else "unknown"
                self.log_message(f"📥 Received({rx_port}): {data_str}")
                self.add_to_data_table("RX", data_str, rx_port)
                self.rx_count += 1
                self.update_status()
        except Exception as e:
            self.log_message(f"❌ Data processing error: {str(e)}")
    
    def add_to_data_table(self, direction: str, data: str, port: str):
        """Add a row to the data table"""
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
        """Update the status bar"""
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
            status_text = f"🔴 Disconnected | 📥{self.rx_count} 📤{self.tx_count}"
        
        status.update(status_text)
    
    def log_message(self, message: str):
        """Output a log message"""
        log = self.query_one("#log_view", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")
    
    def action_clear_data(self) -> None:
        """Clear received and sent data"""
        table = self.query_one("#data_table", DataTable)
        table.clear()
        self.data_buffer.clear()
        self.rx_count = 0
        self.tx_count = 0
        self.update_status()
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
                writer.writerow(['timestamp', 'direction', 'data', 'port'])
                
                for entry in self.data_buffer:
                    writer.writerow([
                        entry['timestamp'].isoformat(),
                        entry['direction'],
                        entry['data'],
                        entry['port']
                    ])
            
            self.log_message(f"💾 {filename} saved ({len(self.data_buffer)} entries)")
        except Exception as e:
            self.log_message(f"❌ Save error: {str(e)}")
    
    async def action_quit(self) -> None:
        """Exit the application"""
        if self.connected:
            await self.disconnect_serial()
        self.exit()


def main():
    """Main execution function"""
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = FinalWorkingDashboard()
    app.run()


if __name__ == "__main__":
    main()
