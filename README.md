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

```bash
# Clone the repository
git clone https://github.com/superdoccimo/modern-serial-communication.git
cd modern-serial-communication

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python serial_dashboard.py
```

### Basic Usage

1. **Launch Dashboard**
   ```bash
   python serial_dashboard.py
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

## 🔧 Configuration

The tool uses `serial_config.ini` for configuration:

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

## 📦 Project Structure

```
modern-serial-communication/
├── serial_dashboard.py      # Main TUI application
├── modern_serial_comm.py    # Core library
├── port_checker.py          # Port discovery tool
├── test_data_sender.py      # Testing utilities
├── requirements.txt         # Dependencies
├── serial_config.ini        # Configuration
└── README.md               # This file
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