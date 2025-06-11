#!/usr/bin/env python3
"""
TCP-serial bridge for VMware environments.
Transfers serial data between a Windows host and a Linux guest.
Provides an alternative to VMware virtual serial ports.
"""

import socket
import serial
import threading
import time
import json
from datetime import datetime
import platform

class VMwareTCPSerialBridge:
    def __init__(self):
        self.running = False
        self.connections = []
    
    def windows_serial_to_tcp_server(self, serial_port="COM1", baudrate=9600, tcp_port=9999):
        """Windows side: Serial port to TCP server"""
        print(f"=== Windows Serial→TCP server ===")
        print(f"Serial port: {serial_port} ({baudrate} baud)")
        print(f"TCP server port: {tcp_port}")
        print("Waiting for connection from Linux...")
        
        # Start the TCP server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', tcp_port))
        server_socket.listen(5)
        
        self.running = True
        
        try:
            # Open the serial port
            with serial.Serial(serial_port, baudrate, timeout=1) as ser:
                print(f"Serial port {serial_port} opened")
                
                while self.running:
                    try:
                        # Accept a new connection
                        client_socket, addr = server_socket.accept()
                        print(f"Linux connection: {addr}")
                        self.connections.append(client_socket)
                        
                        # Handle on a dedicated thread
                        thread = threading.Thread(
                            target=self.handle_tcp_client,
                            args=(ser, client_socket, addr)
                        )
                        thread.daemon = True
                        thread.start()
                        
                    except socket.timeout:
                        continue
                    except OSError as e:
                        print(f"Connection error: {e}")
                        
        except serial.SerialException as e:
            print(f"Serial port error: {e}")
        except OSError as e:
            print(f"Error: {e}")
        finally:
            server_socket.close()
            print("Server stopped")
    
    def handle_tcp_client(self, serial_port, client_socket, addr):
        """Handle a TCP client connection"""
        try:
            while self.running:
                # Read data from serial
                if serial_port.in_waiting > 0:
                    data = serial_port.read(serial_port.in_waiting)
                    try:
                        client_socket.send(data)
                        print(f"Forward → {addr}: {len(data)} bytes")
                    except OSError:
                        break
                
                # Receive data from TCP (bidirectional)
                client_socket.settimeout(0.1)
                try:
                    tcp_data = client_socket.recv(1024)
                    if tcp_data:
                        serial_port.write(tcp_data)
                        print(f"Recv ← {addr}: {len(tcp_data)} bytes")
                except socket.timeout:
                    pass
                except OSError:
                    break
                
                time.sleep(0.01)
                
        except (serial.SerialException, OSError) as e:
            print(f"Client handler error {addr}: {e}")
        finally:
            client_socket.close()
            if client_socket in self.connections:
                self.connections.remove(client_socket)
            print(f"Client disconnected: {addr}")
    
    def linux_tcp_to_serial_client(self, windows_ip, tcp_port=9999, serial_device="/dev/ttyS0", baudrate=9600):
        """Linux side: TCP client to serial port"""
        print(f"=== Linux TCP→Serial client ===")
        print(f"Windows target: {windows_ip}:{tcp_port}")
        print(f"Serial device: {serial_device} ({baudrate} baud)")
        
        try:
            # Connect to the Windows server
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((windows_ip, tcp_port))
            print("Connected to Windows host")
            
            # Open the serial port
            with serial.Serial(serial_device, baudrate, timeout=1) as ser:
                print(f"Serial device {serial_device} opened")
                
                self.running = True
                
                while self.running:
                    # Receive data from TCP
                    tcp_socket.settimeout(0.1)
                    try:
                        tcp_data = tcp_socket.recv(1024)
                        if tcp_data:
                            ser.write(tcp_data)
                            print(f"TCP→Serial: {len(tcp_data)} bytes")
                            print(f"Data: {tcp_data.decode('utf-8', errors='ignore').strip()}")
                        elif not tcp_data:
                            print("Connection closed")
                            break
                    except socket.timeout:
                        pass
                    
                    # Read from serial (bidirectional)
                    if ser.in_waiting > 0:
                        serial_data = ser.read(ser.in_waiting)
                        tcp_socket.send(serial_data)
                        print(f"Serial→TCP: {len(serial_data)} bytes")
                    
                    time.sleep(0.01)
                    
        except ConnectionRefusedError:
            print(f"Connection refused: {windows_ip}:{tcp_port}")
            print("Verify the server is running on Windows")
        except serial.SerialException as e:
            print(f"Serial device error: {e}")
            print("Check permissions: sudo chmod 666 /dev/ttyS0")
        except OSError as e:
            print(f"Error: {e}")
        finally:
            tcp_socket.close()
            print("Client stopped")
    
    def send_test_data_windows(self, serial_port="COM1", baudrate=9600):
        """Send test data on Windows"""
        print(f"=== Windows send test data ===")
        print(f"Serial port: {serial_port}")
        
        try:
            with serial.Serial(serial_port, baudrate, timeout=1) as ser:
                counter = 1
                while True:
                    # Build test message
                    test_data = {
                        "id": counter,
                        "timestamp": datetime.now().isoformat(),
                        "source": "Windows_Host",
                        "message": f"Test_Message_{counter:03d}"
                    }
                    
                    message = json.dumps(test_data) + "\r\n"
                    ser.write(message.encode('utf-8'))
                    
                    print(f"[{counter:03d}] Sent: {message.strip()}")
                    counter += 1
                    
                    time.sleep(2)
                    
        except KeyboardInterrupt:
            print("Transmission stopped")
        except serial.SerialException as e:
            print(f"Error: {e}")
    
    def monitor_serial_linux(self, serial_device="/dev/ttyS0", baudrate=9600):
        """Monitor a serial port on Linux"""
        print(f"=== Linux serial monitor ===")
        print(f"Device: {serial_device}")
        
        try:
            with serial.Serial(serial_device, baudrate, timeout=1) as ser:
                print("Start monitoring... (Ctrl+C to stop)")
                
                while True:
                    if ser.in_waiting > 0:
                        data = ser.readline().decode('utf-8', errors='ignore').strip()
                        if data:
                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            print(f"[{timestamp}] Received: {data}")
                    
                    time.sleep(0.01)
                    
        except KeyboardInterrupt:
            print("Monitoring stopped")
        except serial.SerialException as e:
            print(f"Error: {e}")
    
    def get_ip_info(self):
        """Get IP information"""
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except OSError:
            return "Failed"

def main():
    bridge = VMwareTCPSerialBridge()
    system = platform.system()
    
    print(f"Current OS: {system}")
    print(f"IP address: {bridge.get_ip_info()}")
    
    while True:
        print(f"\n=== VMware TCP-Serial Bridge ({system}) ===")
        
        if system == "Windows":
            print("[Windows Menu]")
            print("1. Start Serial→TCP server")
            print("2. Send test data (serial)")
            print("3. Show IP information")
        else:
            print("[Linux Menu]")
            print("1. Start TCP→Serial client")
            print("2. Monitor serial")
            print("3. Permission guide")
        
        print("9. Setup guide")
        print("0. Exit")
        
        choice = input("\nSelect an option: ").strip()
        
        if choice == "1":
            if system == "Windows":
                port = input("Serial port (COM1): ").strip() or "COM1"
                baudrate = int(input("Baud rate (9600): ").strip() or "9600")
                tcp_port = int(input("TCP port (9999): ").strip() or "9999")
                
                try:
                    bridge.windows_serial_to_tcp_server(port, baudrate, tcp_port)
                except KeyboardInterrupt:
                    bridge.running = False
                    print("Server stopped")
            else:
                windows_ip = input("Windows IP: ").strip()
                tcp_port = int(input("TCP port (9999): ").strip() or "9999")
                device = input("Serial device (/dev/ttyS0): ").strip() or "/dev/ttyS0"
                baudrate = int(input("Baud rate (9600): ").strip() or "9600")
                
                try:
                    bridge.linux_tcp_to_serial_client(windows_ip, tcp_port, device, baudrate)
                except KeyboardInterrupt:
                    bridge.running = False
                    print("Client stopped")
        
        elif choice == "2":
            if system == "Windows":
                port = input("Serial port (COM1): ").strip() or "COM1"
                baudrate = int(input("Baud rate (9600): ").strip() or "9600")
                bridge.send_test_data_windows(port, baudrate)
            else:
                device = input("Serial device (/dev/ttyS0): ").strip() or "/dev/ttyS0"
                baudrate = int(input("Baud rate (9600): ").strip() or "9600")
                bridge.monitor_serial_linux(device, baudrate)
        
        elif choice == "3":
            if system == "Windows":
                print(f"IP address: {bridge.get_ip_info()}")
                print("Use this IP on the Linux side")
            else:
                print("=== Linux permission setup ===")
                print("sudo chmod 666 /dev/ttyS0")
                print("or")
                print("sudo usermod -a -G dialout $USER")
                print("(re-login required)")
        
        elif choice == "9":
            print("\n=== Setup guide ===")
            print("1. VMware settings:")
            print("   Add a serial port in VM settings")
            print("   Recognized as /dev/ttyS0 on Linux")
            print()
            print("2. Usage:")
            print("   1) Windows: start server from menu 1")
            print("   2) Linux: start client from menu 1")
            print("   3) Windows: send test data from menu 2")
            print("   4) Linux: verify received data")
            print()
            print("3. Troubleshooting:")
            print("   - Check firewall")
            print("   - Install VMware Tools")
            print("   - Serial device permissions")
        
        elif choice == "0":
            bridge.running = False
            break

if __name__ == "__main__":
    main()
