#!/usr/bin/env python3
"""
Serial port checker
Displays a list of available serial ports
"""

import serial.tools.list_ports
import sys


def list_serial_ports():
    """List available serial ports"""
    print("=== Available Serial Ports ===")
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("No serial ports found.")
        print("\nTest configuration:")
        print("- loop://  : loopback (for testing)")
        print("- spy://COM1 : monitor an existing port")
        return []
    
    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device}")
        print(f"   Description: {port.description}")
        print(f"   HW ID: {port.hwid}")
        if hasattr(port, 'manufacturer') and port.manufacturer:
            print(f"   Manufacturer: {port.manufacturer}")
        print()
    
    return [port.device for port in ports]


def test_port_connection(port_name: str):
    """Connection test for the specified port"""
    try:
        import serial
        print(f"\n=== Testing connection to {port_name} ===")
        
        # Basic connection test
        with serial.Serial(port_name, 9600, timeout=1) as ser:
            print(f"✅ Connected to {port_name}")
            print(f"   Baudrate: {ser.baudrate}")
            print(f"   Data bits: {ser.bytesize}")
            print(f"   Stop bits: {ser.stopbits}")
            print(f"   Parity: {ser.parity}")
            return True
            
    except serial.SerialException as e:
        print(f"❌ Failed to connect to {port_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def create_test_config(port_name: str = None):
    """Create configuration file for testing"""
    import configparser
    
    config = configparser.ConfigParser()
    
    # Get available ports
    available_ports = list_serial_ports()
    
    if port_name:
        selected_port = port_name
    elif available_ports:
        selected_port = available_ports[0]
        print(f"\nUsing the first port found: {selected_port}")
    else:
        selected_port = 'loop://'
        print("\nNo real ports found, using loopback for testing")
    
    config['SERIAL'] = {
        'port': selected_port,
        'baudrate': '9600',
        'bytesize': '8',
        'parity': 'N',
        'stopbits': '1',
        'timeout': '1.0'
    }
    
    config['NETWORK'] = {
        'tcp_host': 'localhost',
        'tcp_port': '5000',
        'use_tcp': 'false'
    }
    
    config['LOGGING'] = {
        'level': 'INFO',
        'format': 'json_lines',
        'output_file': 'serial_log.jsonl'
    }
    
    # Save configuration file
    config_path = 'serial_config.ini'
    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print(f"\nCreated config file '{config_path}'")
    print(f"Port: {selected_port}")
    
    return config_path


if __name__ == "__main__":
    print("Python Serial Communication - Port Checker")
    print("=" * 50)
    
    # List available ports
    available_ports = list_serial_ports()
    
    # Interactive port selection
    if available_ports:
        print(f"\n{len(available_ports)} ports found.")
        print("Enter the number of the port to test (press Enter to skip):")
        
        try:
            choice = input("> ").strip()
            if choice.isdigit():
                port_index = int(choice) - 1
                if 0 <= port_index < len(available_ports):
                    selected_port = available_ports[port_index]
                    test_port_connection(selected_port)
                    create_test_config(selected_port)
                else:
                    print("Invalid number. Creating default configuration.")
                    create_test_config()
            else:
                print("Creating default configuration.")
                create_test_config()
        except KeyboardInterrupt:
            print("\nInterrupted.")
            sys.exit(1)
    else:
        create_test_config()
    
    print("\nRun the main program with the following command:")
    print("python modern_serial_comm.py")
