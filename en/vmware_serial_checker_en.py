#!/usr/bin/env python3
"""
VMware virtual serial port diagnostic and configuration tool.
Verifies serial communication between a Windows host and a Linux guest.
"""

import serial
import serial.tools.list_ports
import subprocess
import platform
import time
import os
import socket
from datetime import datetime

class VMwareSerialDiagnostic:
    def __init__(self):
        self.system = platform.system()
    
    def check_system_info(self):
        """Check system information"""
        print("=== System information ===")
        print(f"OS: {platform.system()} {platform.release()}")
        print(f"Architecture: {platform.machine()}")
        
        if self.system == "Linux":
            # Check VMware Tools
            try:
                result = subprocess.run(['vmware-toolbox-cmd', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"VMware Tools: {result.stdout.strip()}")
                else:
                    print("VMware Tools: not installed")
            except FileNotFoundError:
                print("VMware Tools: not installed")
            
            # Check kernel modules
            try:
                with open('/proc/modules', 'r') as f:
                    modules = f.read()
                    if 'vmw_' in modules:
                        print("VMware kernel module: detected")
                    else:
                        print("VMware kernel module: not found")
            except:
                pass
        
        print()
    
    def list_serial_devices(self):
        """List serial devices"""
        print("=== Serial device list ===")
        
        if self.system == "Linux":
            # Check /dev/ttyS*
            serial_devices = []
            for i in range(10):
                device = f"/dev/ttyS{i}"
                if os.path.exists(device):
                    serial_devices.append(device)
            
            print("Standard serial devices:")
            for device in serial_devices:
                try:
                    stat = os.stat(device)
                    print(f"  {device} (permissions: {oct(stat.st_mode)[-3:]})")
                except:
                    print(f"  {device} (not accessible)")
            
            # Check /dev/ttyUSB* and /dev/ttyACM*
            usb_devices = []
            for prefix in ['/dev/ttyUSB', '/dev/ttyACM']:
                for i in range(10):
                    device = f"{prefix}{i}"
                    if os.path.exists(device):
                        usb_devices.append(device)
            
            if usb_devices:
                print("USB serial devices:")
                for device in usb_devices:
                    print(f"  {device}")
            else:
                print("USB serial devices: none")
        
        # Detection via pyserial
        print("\nDevices detected by pyserial:")
        ports = serial.tools.list_ports.comports()
        if ports:
            for port in ports:
                print(f"  {port.device}: {port.description}")
        else:
            print("  None detected")
        
        print()
    
    def test_serial_access(self, device_path):
        """Serial device access test"""
        print(f"=== {device_path} access test ===")
        
        try:
            # Basic open/close test
            with serial.Serial(device_path, 9600, timeout=1) as ser:
                print(f"✓ Successfully opened device")
                print(f"  Port: {ser.port}")
                print(f"  Baud rate: {ser.baudrate}")
                print(f"  Timeout: {ser.timeout}")
                
                # Simple read/write test
                try:
                    ser.write(b"TEST\r\n")
                    print("✓ Write test successful")
                    
                    # Wait a bit then attempt to read
                    time.sleep(0.1)
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting)
                        print(f"✓ Received data: {data}")
                    else:
                        print("- No data received (expected)")
                        
                except Exception as e:
                    print(f"✗ Read/write error: {e}")
                    
        except serial.SerialException as e:
            print(f"✗ Serial port error: {e}")
        except PermissionError:
            print(f"✗ Permission error: no access to {device_path}")
            if self.system == "Linux":
                print(f"  Solution: sudo chmod 666 {device_path}")
                print(f"  or: sudo usermod -a -G dialout $USER")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
        
        print()
    
    def check_vmware_config(self):
        """VMware configuration guide"""
        print("=== VMware virtual serial port setup guide ===")
        
        if self.system == "Windows":
            print("Windows host settings:")
            print("1. VMware Workstation/Player configuration")
            print("   - VM settings → Add Hardware → Serial Port")
            print("   - Use named pipe as connection")
            print(r"   - Pipe name: \\.\pipe\com_1 (example)")
            print("   - Pipe endpoint: server")
            print("   - I/O mode: application")
            print()
            print("2. Create Windows virtual COM port")
            print("   - Create a virtual port pair with com0com, etc.")
            print("   - Example: COM1 ↔ COM2")
            print()
            
        elif self.system == "Linux":
            print("Linux guest checks:")
            print("1. Verify VMware settings")
            print("   - Is a serial port added?")
            print("   - Typically recognized as /dev/ttyS0")
            print()
            print("2. Permission settings")
            print("   sudo chmod 666 /dev/ttyS0")
            print("   or")
            print("   sudo usermod -a -G dialout $USER")
            print("   (re-login required)")
            print()
            print("3. Check VMware Tools")
            print("   - Ensure VMware Tools is installed")
            print("   - Some drivers may be required")
            print()
        
        print("=== Alternatives ===")
        print("1. TCP/IP socket communication")
        print("   - More reliable and easier to configure")
        print("   - Transfer data over the network")
        print()
        print("2. Shared folders")
        print("   - Exchange data via files")
        print("   - Less real-time but reliable")
        print()
        print("3. SSH/SCP")
        print("   - Secure communication")
        print("   - Standard Linux functionality")
        print()
    
    def network_alternative_test(self):
        """Network alternative test"""
        print("=== Network communication test ===")
        
        if self.system == "Linux":
            print("Start a test server on Linux:")
            print("1. Python3 server:")
            print("   python3 -c \"")
            print("import socket, datetime")
            print("s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)")
            print("s.bind(('0.0.0.0', 12345))")
            print("s.listen(1)")
            print("print('waiting...')")
            print("c, a = s.accept()")
            print("while True:")
            print("    data = c.recv(1024)")
            print("    if not data: break")
            print("    print(f'{datetime.datetime.now()}: {data.decode()}')\"")
            print()
            print("2. Using netcat:")
            print("   nc -l -p 12345")
            print()
            
        elif self.system == "Windows":
            print("Send test data from Windows:")
            print("PowerShell example:")
            print('$client = New-Object System.Net.Sockets.TcpClient')
            print('$client.Connect("192.168.xxx.xxx", 12345)')
            print('$stream = $client.GetStream()')
            print('$data = [System.Text.Encoding]::UTF8.GetBytes("Test message\\n")')
            print('$stream.Write($data, 0, $data.Length)')
            print('$client.Close()')
            print()
        
        # IP check
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            print(f"Current IP address: {ip}")
        except:
            print("Failed to obtain IP address")
    
    def run_diagnosis(self):
        """Run full diagnosis"""
        print("Starting VMware virtual serial port diagnosis\n")
        
        self.check_system_info()
        self.list_serial_devices()
        
        # On Linux, test main devices
        if self.system == "Linux":
            test_devices = ["/dev/ttyS0", "/dev/ttyS1"]
            for device in test_devices:
                if os.path.exists(device):
                    self.test_serial_access(device)
        
        self.check_vmware_config()
        self.network_alternative_test()

def main():
    diagnostic = VMwareSerialDiagnostic()
    
    while True:
        print("\n=== VMware Serial Port Diagnostic Tool ===")
        print("1. Run full diagnosis")
        print("2. Show system information")
        print("3. List serial devices")
        print("4. Device test (manual)")
        print("5. VMware configuration guide")
        print("6. Network alternatives")
        print("7. Exit")
        
        choice = input("\nSelect an option (1-7): ").strip()
        
        if choice == "1":
            diagnostic.run_diagnosis()
        
        elif choice == "2":
            diagnostic.check_system_info()
        
        elif choice == "3":
            diagnostic.list_serial_devices()
        
        elif choice == "4":
            device = input("Device path to test: ").strip()
            if device:
                diagnostic.test_serial_access(device)
        
        elif choice == "5":
            diagnostic.check_vmware_config()
        
        elif choice == "6":
            diagnostic.network_alternative_test()
        
        elif choice == "7":
            break
        
        else:
            print("Please choose between 1 and 7")

if __name__ == "__main__":
    main()
