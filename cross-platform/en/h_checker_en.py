#!/usr/bin/env python3
"""
Universal serial communication test tool.
Supports real devices, VirtualBox, and VMware (named pipes).
"""

import serial
import serial.tools.list_ports
import platform
import time
import json
import threading
import os
from datetime import datetime

class UniversalSerialTester:
    def __init__(self):
        self.system = platform.system()
        self.running = False
        
    def detect_environment(self):
        """Automatically detect the execution environment"""
        env_info = {
            "system": self.system,
            "virtual": False,
            "vm_type": None,
            "recommended_method": None
        }
        
        if self.system == "Linux":
            # Detect virtualization
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()
                    
                if 'vmware' in cpuinfo:
                    env_info["virtual"] = True
                    env_info["vm_type"] = "VMware"
                    env_info["recommended_method"] = "Named pipe or TCP/IP"
                elif 'virtualbox' in cpuinfo:
                    env_info["virtual"] = True  
                    env_info["vm_type"] = "VirtualBox"
                    env_info["recommended_method"] = "Virtual serial port"
                else:
                    env_info["recommended_method"] = "Physical serial port"
                    
            except:
                pass
                
        elif self.system == "Windows":
            # Windows environment check
            try:
                import subprocess
                result = subprocess.run(['systeminfo'], capture_output=True, text=True)
                if 'VMware' in result.stdout:
                    env_info["virtual"] = True
                    env_info["vm_type"] = "VMware Host"
                    env_info["recommended_method"] = "Named pipe"
                elif 'VirtualBox' in result.stdout:
                    env_info["virtual"] = True
                    env_info["vm_type"] = "VirtualBox Host"
                    env_info["recommended_method"] = "COM-COM bridge"
                else:
                    env_info["recommended_method"] = "Physical serial port"
            except:
                pass
        
        return env_info
    
    def show_environment_guide(self):
        """Show configuration guide for each environment"""
        env = self.detect_environment()
        
        print("=== Environment Information ===")
        print(f"OS: {env['system']}")
        print(f"Virtualized: {'Yes' if env['virtual'] else 'No'}")
        if env['vm_type']:
            print(f"VM Type: {env['vm_type']}")
        print(f"Recommended method: {env['recommended_method']}")
        print()
        
        # Detailed guide per environment
        if env['vm_type'] == "VMware":
            print("🔧 VMware setup guide:")
            print("1. VM settings → Add serial port")
            print("2. Connection type: Use named pipe")
            print("3. Pipe name: \\.\pipe\vmware_serial")
            print("4. Pipe endpoint: Server")
            print("5. I/O mode: Application")
            
        elif env['vm_type'] == "VirtualBox":
            print("🔧 VirtualBox setup guide:")
            print("1. VM settings → Serial Ports")
            print("2. Enable Port 1")
            print("3. Port Mode: Host Pipe")
            print("4. Path/Address: \\.\pipe\vbox_serial")
            
        elif not env['virtual']:
            print("🔧 Physical environment guide:")
            print("1. Use a USB serial adapter")
            print("2. Or connect via RS232C cable")
            print("3. Match baud rate on both ends")
            
        print()
    
    def smart_port_detection(self):
        """Intelligent port detection"""
        ports = serial.tools.list_ports.comports()
        
        categorized_ports = {
            "physical": [],
            "virtual": [],
            "usb": [],
            "unknown": []
        }
        
        for port in ports:
            desc = port.description.lower()
            hwid = port.hwid.lower()
            
            if 'usb' in desc or 'usb' in hwid:
                categorized_ports["usb"].append(port)
            elif 'com0com' in desc or 'virtual' in desc:
                categorized_ports["virtual"].append(port)
            elif 'communications port' in desc:
                categorized_ports["physical"].append(port)
            else:
                categorized_ports["unknown"].append(port)
        
        print("=== Intelligent port detection results ===")
        
        for category, port_list in categorized_ports.items():
            if port_list:
                category_names = {
                    "physical": "Physical serial ports",
                    "virtual": "Virtual serial ports",
                    "usb": "USB serial adapters",
                    "unknown": "Other"
                }
                
                print(f"\n📌 {category_names[category]}:")
                for i, port in enumerate(port_list, 1):
                    print(f"  {i}. {port.device}")
                    print(f"     Description: {port.description}")
                    if hasattr(port, 'manufacturer') and port.manufacturer:
                        print(f"     Manufacturer: {port.manufacturer}")
        
        return categorized_ports
    
    def bidirectional_test_wizard(self):
        """Bidirectional test wizard"""
        print("=== Bidirectional communication test wizard ===")
        
        categorized = self.smart_port_detection()
        all_ports = []
        for port_list in categorized.values():
            all_ports.extend(port_list)
        
        if len(all_ports) < 2:
            print("⚠️ At least two ports are required for the test")
            print("💡 Suggestions:")
            print("1. Create a virtual port pair with com0com, etc.")
            print("2. Connect two USB serial adapters")
            print("3. Use a TCP/IP bridge")
            return
        
        print(f"\nAvailable ports: {len(all_ports)}")
        for i, port in enumerate(all_ports, 1):
            print(f"{i}. {port.device} - {port.description}")
        
        try:
            # Select transmit port
            tx_choice = int(input("\nSelect transmit port (1-{}): ".format(len(all_ports)))) - 1
            tx_port = all_ports[tx_choice].device
            
            # Select receive port
            rx_choice = int(input("Select receive port (1-{}): ".format(len(all_ports)))) - 1
            rx_port = all_ports[rx_choice].device
            
            if tx_port == rx_port:
                print("❌ Please choose different ports")
                return
            
            # Baud rate setting
            baudrate = int(input("Baud rate (9600): ") or "9600")
            
            print(f"\n🔄 Starting bidirectional test")
            print(f"Transmit: {tx_port}")
            print(f"Receive: {rx_port}")
            print(f"Baud rate: {baudrate}")
            print("Press Ctrl+C to stop")
            
            self.run_bidirectional_test(tx_port, rx_port, baudrate)
            
        except (ValueError, IndexError):
            print("❌ Invalid selection")
        except KeyboardInterrupt:
            print("\n✅ Test finished")
    
    def run_bidirectional_test(self, tx_port, rx_port, baudrate):
        """Execute the bidirectional test"""
        self.running = True
        
        # Start receive thread
        rx_thread = threading.Thread(
            target=self.receive_monitor,
            args=(rx_port, baudrate)
        )
        rx_thread.daemon = True
        rx_thread.start()
        
        # Begin transmitting
        try:
            with serial.Serial(tx_port, baudrate, timeout=1) as ser:
                counter = 1
                while self.running:
                    # Create test data
                    test_data = {
                        "id": counter,
                        "timestamp": datetime.now().isoformat(),
                        "tx_port": tx_port,
                        "message": f"Test_{counter:03d}"
                    }
                    
                    message = json.dumps(test_data) + "\r\n"
                    ser.write(message.encode('utf-8'))
                    
                    print(f"[TX {counter:03d}] {tx_port} → {rx_port}: {test_data['message']}")
                    counter += 1
                    
                    time.sleep(2)
                    
        except serial.SerialException as e:
            print(f"❌ Send error: {e}")
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
    
    def receive_monitor(self, port, baudrate):
        """Receive monitor"""
        try:
            with serial.Serial(port, baudrate, timeout=1) as ser:
                buffer = ""
                while self.running:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        buffer += data
                        
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            if line:
                                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                                print(f"[RX {timestamp}] {port} ← {line}")
                    
                    time.sleep(0.01)
                    
        except serial.SerialException as e:
            print(f"❌ Receive error: {e}")
    
    def performance_test(self, port, baudrate=9600, duration=30):
        """Performance test"""
        print(f"=== Starting performance test ===")
        print(f"Port: {port}")
        print(f"Baud rate: {baudrate}")
        print(f"Duration: {duration} seconds")
        
        try:
            with serial.Serial(port, baudrate, timeout=1) as ser:
                start_time = time.time()
                bytes_sent = 0
                packets_sent = 0
                
                while time.time() - start_time < duration:
                    # 100-byte test data
                    test_data = f"PERF_TEST_{packets_sent:06d}_" + "X" * 80 + "\r\n"
                    ser.write(test_data.encode('utf-8'))
                    
                    bytes_sent += len(test_data)
                    packets_sent += 1
                    
                    if packets_sent % 100 == 0:
                        elapsed = time.time() - start_time
                        bps = bytes_sent / elapsed
                        print(f"Progress: {packets_sent} packets, {bps:.1f} bytes/sec")
                    
                    time.sleep(0.01)  # 100Hz
                
                # Show results
                elapsed = time.time() - start_time
                print(f"\n=== Performance test results ===")
                print(f"Packets sent: {packets_sent}")
                print(f"Bytes sent: {bytes_sent:,}")
                print(f"Elapsed time: {elapsed:.2f} sec")
                print(f"Throughput: {bytes_sent/elapsed:.1f} bytes/sec")
                print(f"Theoretical: {baudrate/10:.1f} bytes/sec")
                print(f"Efficiency: {(bytes_sent/elapsed)/(baudrate/10)*100:.1f}%")
                
        except Exception as e:
            print(f"❌ Performance test error: {e}")
    
    def run(self):
        """Main menu"""
        while True:
            print("\n" + "="*50)
            print("🔧 Universal Serial Communication Tester")
            print("="*50)
            
            print("1. Environment info & setup guide")
            print("2. Intelligent port detection")
            print("3. Bidirectional test wizard")
            print("4. One-way send test")
            print("5. Receive monitor")
            print("6. Performance test")
            print("7. Exit")
            
            try:
                choice = input("\nSelect an option (1-7): ").strip()
                
                if choice == "1":
                    self.show_environment_guide()
                
                elif choice == "2":
                    self.smart_port_detection()
                
                elif choice == "3":
                    self.bidirectional_test_wizard()
                
                elif choice == "4":
                    ports = list(serial.tools.list_ports.comports())
                    if ports:
                        print("\nAvailable ports:")
                        for i, port in enumerate(ports, 1):
                            print(f"{i}. {port.device}")
                        
                        try:
                            port_choice = int(input("Select port: ")) - 1
                            if 0 <= port_choice < len(ports):
                                port = ports[port_choice].device
                                baudrate = int(input("Baud rate (9600): ") or "9600")
                                
                                # One-way send test
                                self.running = True
                                self.run_bidirectional_test(port, port, baudrate)
                        except:
                            print("❌ Invalid selection")
                
                elif choice == "5":
                    ports = list(serial.tools.list_ports.comports())
                    if ports:
                        print("\nAvailable ports:")
                        for i, port in enumerate(ports, 1):
                            print(f"{i}. {port.device}")
                        
                        try:
                            port_choice = int(input("Select port: ")) - 1
                            if 0 <= port_choice < len(ports):
                                port = ports[port_choice].device
                                baudrate = int(input("Baud rate (9600): ") or "9600")
                                
                                print(f"Starting receive monitor: {port}")
                                print("Press Ctrl+C to stop")
                                
                                self.running = True
                                self.receive_monitor(port, baudrate)
                        except KeyboardInterrupt:
                            self.running = False
                            print("\nReceive monitoring stopped")
                        except:
                            print("❌ Invalid selection")
                
                elif choice == "6":
                    ports = list(serial.tools.list_ports.comports())
                    if ports:
                        print("\nAvailable ports:")
                        for i, port in enumerate(ports, 1):
                            print(f"{i}. {port.device}")
                        
                        try:
                            port_choice = int(input("Select port: ")) - 1
                            if 0 <= port_choice < len(ports):
                                port = ports[port_choice].device
                                baudrate = int(input("Baud rate (9600): ") or "9600")
                                duration = int(input("Test duration[s] (30): ") or "30")
                                
                                self.performance_test(port, baudrate, duration)
                        except:
                            print("❌ Invalid selection")
                
                elif choice == "7":
                    print("Exiting")
                    break
                
                else:
                    print("❌ Please select 1-7")
                    
            except KeyboardInterrupt:
                print("\n\nExiting")
                self.running = False
                break

if __name__ == "__main__":
    tester = UniversalSerialTester()
    tester.run()
