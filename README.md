# 📡 Modern Serial Communication

**A modern, open-source alternative to commercial serial monitoring tools**

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

Modern Serial Communication is a lightweight, Python-powered serial port monitoring and communication tool designed to replace expensive commercial solutions. Perfect for developers, engineers, and researchers working with legacy serial equipment.

## ✨ Features

### 🚀 Core Functionality
- **Real-time Serial Monitoring** - Live data visualization with timestamps
- **Multiple Connection Types** - Direct serial ports, TCP bridges, virtual ports
- **Async I/O** - Non-blocking communication for optimal performance
- **Cross-platform** - Works on Windows, Linux, and macOS

### 📊 Advanced Monitoring
- **Live Data Table** - Real-time packet display with filtering
- **Sparkline Graphs** - Visual data flow representation
- **Statistical Analysis** - Packet counts, throughput, and timing metrics
- **Structured Logging** - JSON Lines format for data analysis

### 🔧 Developer-Friendly
- **Terminal UI (TUI)** - Beautiful console interface with Textual
- **CSV Export** - Easy data analysis and reporting
- **Configurable Settings** - INI-based configuration management
- **Plugin Ready** - Extensible architecture for custom protocols

### 🌐 Enterprise Features
- **VM Support** - TCP bridging for virtual machine environments
- **MQTT Ready** - IoT dashboard integration (coming soon)
- **WebSocket Output** - Browser-based monitoring (coming soon)
- **REST API** - Programmatic access and automation

## 🎯 Why Choose This Over Commercial Tools?

| Feature | Commercial Tools | Modern Serial Comm |
|---------|------------------|-------------------|
| **Price** | $60-200+ | **Free & Open Source** |
| **Platform** | Windows Only | **Cross-Platform** |
| **Customization** | Limited | **Unlimited** |
| **Automation** | GUI Only | **API + Scripting** |
| **VM Support** | Complex Setup | **Built-in TCP Bridge** |
| **Data Export** | Proprietary | **Standard Formats** |

## 🚀 Quick Start

### Installation

#### Method 1: Package Installation (Recommended)
```bash
# Clone the repository
git clone https://github.com/superdoccimo/modern-serial-communication.git
cd modern-serial-communication

# Install as a package (development mode)
pip install -e .

# Use command line tools
serial-dashboard --help
serial-checker --help
```

#### Method 2: Direct Execution
```bash
# Clone the repository
git clone https://github.com/superdoccimo/modern-serial-communication.git
cd modern-serial-communication

# Install dependencies only
pip install -r requirements.txt

# Run cross-platform dashboard
python cross-platform/serial_dashboard_refactored.py
```

#### Method 3: Platform-Specific
```bash
# For Windows-specific features
python windows/dual_pipe_windows.py

# For Linux-specific features  
python linux/dual_pipe_linux.py
```

### Basic Usage

1. **Launch Dashboard**
   ```bash
   # If installed as package
   serial-dashboard
   
   # Or direct execution
   python cross-platform/simple_dashboard_refactored.py  # lightweight
   python cross-platform/serial_dashboard_refactored.py  # full features
   ```

2. **Connect to Serial Port**
   - Enter port name (e.g., `COM1`, `/dev/ttyUSB0`)
   - Click "Connect" button
   - Start monitoring data!

3. **For VM Environments**
   - Use TCP bridge: `socket://host:port`
   - Example: `socket://localhost:5000`

### Command Line Controls

- `q` - Quit application
- `c` - Clear all data
- `s` - Save data to CSV
- `r` - Toggle recording

## 📋 Requirements

- Python 3.8+
- pyserial
- pyserial-asyncio
- textual
- rich

## 🛠️ Development & Setup.py Usage

### Package Information
```bash
# Check version
python cross-platform/setup.py --version

# View package metadata
python cross-platform/setup.py --name
python cross-platform/setup.py --author
python cross-platform/setup.py --help

# List all available commands
python cross-platform/setup.py --help-commands
```

### Development Installation
```bash
# Install in development mode (recommended for contributors)
python cross-platform/setup.py develop
# or
pip install -e .

# Create distribution packages
python cross-platform/setup.py sdist bdist_wheel

# Install from source
python cross-platform/setup.py install
```

### Project Structure
```
modern-serial-communication/
├── common/           # Shared modules and utilities
├── cross-platform/   # Cross-platform applications
├── windows/          # Windows-specific features
├── linux/            # Linux-specific features
├── tests/            # Test suite
└── requirements.txt  # Dependencies
```

## 📚 Documentation & Tutorials

### Blog Posts & Guides
- **English:**
  - [Python Serial Communication Guide](https://betelgeuse.work/serial-python/)
  - [Linux Serial Communication Tutorial](https://betelgeuse.work/linux-serial/)

- **Japanese (日本語):**
  - [シリアル通信の基礎とPython実装](https://minokamo.tokyo/2025/06/03/9050/)
  - [Linuxでのシリアル通信プログラミング](https://minokamo.tokyo/2025/06/05/9063/)

- **Hindi (हिंदी):**
  - [Python Serial Communication Tutorial](https://minokamo.in/python-serial/)
  - [Linux Serial Communication Guide](https://minokamo.in/linux-serial/)

### Video Tutorials
- **English:** [Modern Serial Communication Tutorial](https://youtu.be/ZyGcM10ewxY)
- **Japanese:** [モダンシリアル通信チュートリアル](https://youtu.be/IJkWY9RMJFo)

## 🔧 Configuration

Use the OS-specific `.ini` file for configuration:
`serial_config_windows.ini` on Windows or `serial_config_linux.ini` on Linux.

```ini
[SERIAL]
port = COM1
baudrate = 9600
bytesize = 8
parity = N
stopbits = 1
timeout = 1.0

[NETWORK]
tcp_host = localhost
tcp_port = 5000
use_tcp = false

[LOGGING]
level = INFO
format = json_lines
output_file = serial_log.jsonl
```

## 🏭 Use Cases

### Manufacturing & Industrial
- Legacy equipment monitoring
- Production line data collection
- Quality control systems
- Sensor data acquisition

### Development & Testing
- Embedded system debugging
- Protocol analysis
- Device testing
- IoT development

### Research & Education
- Data logging for experiments
- Student projects
- Protocol learning
- System integration

## 🌐 VM and Remote Access

Perfect for modern development environments:

### Docker/VM Setup
```bash
# Host: Bridge COM port to TCP
ncat -l -p 5000 --sh-exec "plink -serial COM7 -sercfg 9600,8n1"

# Guest: Connect via TCP
python serial_dashboard.py
# Use: socket://host:5000
```

### SSH/Remote Development
- Terminal-based UI works over SSH
- No GUI dependencies
- Lightweight and responsive

### Hybrid Network Dashboard & Remote Client
Run `hybrid_network_dashboard.py` on the machine with the serial hardware and
connect from another PC using `remote_client_dashboard.py`. This pair allows
you to operate the serial port remotely over TCP.

## 📦 Project Structure

```
modern-serial-communication/
├── simple_dashboard.py         # Simplified dashboard
├── serial_dashboard.py         # Full-featured dashboard
├── modern_serial_comm.py       # Core library
├── async_serial_debug.py       # Diagnostic tool
├── linux_port_checker.py       # Linux port checker
├── port_checker.py             # Port discovery tool
├── hybrid_network_dashboard.py  # Serial+TCP dashboard server
├── remote_client_dashboard.py   # Connects to the hybrid dashboard
├── test_data_sender.py         # Example sender (Windows)
├── test_data_sender_linux.py   # Example sender (Linux)
├── serial_config_windows.ini   # Windows config
├── serial_config_linux.ini     # Linux config
├── requirements.txt            # Dependencies
└── README.md                   # Documentation
```

## 🚧 Roadmap

### Near Term
- [ ] WebSocket output for browser UIs
- [ ] MQTT integration for IoT dashboards
- [ ] Plugin system for custom protocols
- [ ] Advanced filtering and search

### Long Term
- [ ] Web-based GUI option
- [ ] Database integration
- [ ] Multi-port monitoring
- [ ] Protocol decoders (Modbus, etc.)

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch
3. **Commit** your changes
4. **Push** to the branch
5. **Open** a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/superdoccimo/modern-serial-communication.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Coming soon

# Run tests
python -m pytest  # Coming soon
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual) for the beautiful TUI
- Inspired by the need for accessible, open-source serial communication tools
- Thanks to the Python serial communication community

## 💡 Why We Built This

Many developers and engineers still work with legacy serial equipment, but commercial monitoring tools are expensive, Windows-only, and inflexible. We believe powerful tools should be:

- **Accessible** - Free and open source
- **Modern** - Built with current best practices
- **Flexible** - Easily customizable and extendable
- **Cross-platform** - Works everywhere Python does

Join us in making serial communication accessible to everyone!

---

**[⭐ Star this repo](https://github.com/superdoccimo/modern-serial-communication.git)** if you find it useful!

**[📧 Get in touch](mailto:github@minokamo.xyz)** for enterprise support or custom development.
