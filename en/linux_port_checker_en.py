#!/usr/bin/env python3
"""
Robust Linux serial port verification and diagnostics tool.
Enhanced error handling with guaranteed output.
"""

import os
import sys
import subprocess
import glob

def safe_print(message):
    """Safe print function"""
    try:
        print(message)
        sys.stdout.flush()
    except Exception as e:
        # Ensure error output even in worst case
        sys.stderr.write(f"Print error: {e}\n")
        sys.stderr.flush()

def check_python_environment():
    """Check Python environment"""
    safe_print("=== Checking Python environment ===")
    safe_print(f"Python version: {sys.version}")
    safe_print(f"Platform: {sys.platform}")
    safe_print(f"Executable: {sys.executable}")
    safe_print("")

def check_basic_system():
    """Basic system information"""
    safe_print("=== Basic system information ===")
    
    try:
        # User information
        import pwd
        current_user = pwd.getpwuid(os.getuid()).pw_name
        safe_print(f"Current user: {current_user}")
        safe_print(f"User ID: {os.getuid()}")
    except Exception as e:
        safe_print(f"User info error: {e}")
    
    try:
        # Group information
        import grp
        groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
        safe_print(f"Groups: {', '.join(groups)}")
        
        # dialout group check
        if 'dialout' in groups:
            safe_print("✅ dialout group: YES")
        else:
            safe_print("❌ dialout group: NO")
            safe_print("   Fix: sudo usermod -a -G dialout $USER && logout")
            
    except Exception as e:
        safe_print(f"Group info error: {e}")
    
    safe_print("")

def check_devices_manual():
    """Manually inspect device files"""
    safe_print("=== Checking device files ===")
    
    # List of devices to check
    devices_to_check = [
        '/dev/ttyS0', '/dev/ttyS1', '/dev/ttyS2',
        '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2',
        '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2'
    ]
    
    found_devices = []
    
    for device in devices_to_check:
        try:
            if os.path.exists(device):
                # Get detailed info
                stat_info = os.stat(device)
                permissions = oct(stat_info.st_mode)[-3:]
                
                # Access test
                readable = os.access(device, os.R_OK)
                writable = os.access(device, os.W_OK)
                
                status = "✅" if (readable and writable) else "❌"
                safe_print(f"{status} {device} - permissions: {permissions}, R:{readable}, W:{writable}")
                found_devices.append(device)
            else:
                safe_print(f"❌ {device} - not found")
        except Exception as e:
            safe_print(f"❌ {device} - error: {e}")
    
    if not found_devices:
        safe_print("❌ No serial devices found")
    else:
        safe_print(f"✅ Found {len(found_devices)} devices")
    
    safe_print("")

def check_with_glob():
    """Search devices with glob patterns"""
    safe_print("=== Glob pattern search ===")
    
    patterns = [
        '/dev/ttyS*',
        '/dev/ttyUSB*', 
        '/dev/ttyACM*',
        '/dev/ttyAMA*'
    ]
    
    all_devices = []
    
    for pattern in patterns:
        try:
            devices = glob.glob(pattern)
            if devices:
                safe_print(f"Pattern {pattern}: {devices}")
                all_devices.extend(devices)
            else:
                safe_print(f"Pattern {pattern}: no matches")
        except Exception as e:
            safe_print(f"Pattern {pattern}: error {e}")
    
    safe_print(f"Total devices found: {len(set(all_devices))}")
    safe_print("")

def check_pyserial():
    """Check pyserial installation"""
    safe_print("=== Checking pyserial ===")
    
    try:
        import serial
        safe_print(f"✅ pyserial version: {serial.VERSION}")
        
        try:
            import serial.tools.list_ports
            safe_print("✅ serial.tools.list_ports available")
            
            # Get list of ports
            ports = list(serial.tools.list_ports.comports())
            safe_print(f"Found {len(ports)} ports via pyserial")
            
            for i, port in enumerate(ports):
                safe_print(f"  Port {i+1}: {port.device}")
                safe_print(f"    Description: {port.description}")
                safe_print(f"    Hardware ID: {port.hwid}")
                
        except Exception as e:
            safe_print(f"❌ list_ports error: {e}")
            
    except ImportError:
        safe_print("❌ pyserial not installed")
        safe_print("   Install: pip3 install pyserial")
    except Exception as e:
        safe_print(f"❌ pyserial error: {e}")
    
    safe_print("")

def check_system_commands():
    """Verify system commands"""
    safe_print("=== Checking system commands ===")
    
    commands = [
        ['ls', '/dev/tty*'],
        ['lsusb'],
        ['dmesg', '|', 'grep', '-i', 'serial'],
        ['cat', '/proc/tty/driver/serial']
    ]
    
    for cmd in commands:
        try:
            safe_print(f"Running: {' '.join(cmd)}")
            
            if '|' in cmd:
                # Commands with pipes need shell=True
                result = subprocess.run(' '.join(cmd), shell=True, 
                                      capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    safe_print(f"  Output: {output[:200]}...")  # first 200 chars
                else:
                    safe_print("  Output: (empty)")
            else:
                safe_print(f"  Error: {result.stderr.strip()}")
                
        except subprocess.TimeoutExpired:
            safe_print(f"  Timeout")
        except FileNotFoundError:
            safe_print(f"  Command not found")
        except Exception as e:
            safe_print(f"  Exception: {e}")
    
    safe_print("")

def test_simple_access():
    """Simple access test"""
    safe_print("=== Simple access test ===")
    
    test_devices = ['/dev/ttyS0', '/dev/ttyUSB0', '/dev/ttyACM0']
    
    for device in test_devices:
        if os.path.exists(device):
            try:
                # Try opening read-only
                with open(device, 'rb') as f:
                    safe_print(f"✅ {device} - opened successfully (read)")
            except PermissionError:
                safe_print(f"❌ {device} - permission denied")
            except OSError as e:
                safe_print(f"❌ {device} - OS error: {e}")
            except Exception as e:
                safe_print(f"❌ {device} - error: {e}")
        else:
            safe_print(f"❌ {device} - does not exist")
    
    safe_print("")

def show_recommendations():
    """Display recommendations"""
    safe_print("=== Recommendations ===")
    safe_print("1. If you have permission issues:")
    safe_print("   sudo usermod -a -G dialout $USER")
    safe_print("   logout && login")
    safe_print("")
    safe_print("2. If /dev/ttyS0 cannot be found:")
    safe_print("   - Use a USB-to-serial adapter: /dev/ttyUSB0")
    safe_print("   - For Arduino etc.: /dev/ttyACM0")
    safe_print("")
    safe_print("3. If pyserial is not installed:")
    safe_print("   pip3 install pyserial")
    safe_print("")

def main():
    """Main execution"""
    safe_print("🔍 Linux Serial Port Diagnostics Tool")
    safe_print("=" * 60)
    
    try:
        check_python_environment()
        check_basic_system()
        check_devices_manual()
        check_with_glob()
        check_pyserial()
        check_system_commands()
        test_simple_access()
        show_recommendations()
        
        safe_print("=" * 60)
        safe_print("✅ Diagnostics completed!")
        
    except KeyboardInterrupt:
        safe_print("\n❌ Interrupted by user")
    except Exception as e:
        safe_print(f"\n❌ Unexpected error: {e}")
        import traceback
        safe_print(traceback.format_exc())

if __name__ == "__main__":
    # Ensure execution when run directly
    safe_print("🚀 Starting diagnostics...")
    main()
    safe_print("🏁 Script finished.")
