#!/usr/bin/env python3
"""
Enhanced Linux serial communication tool
Supports VMware dual-pipe bidirectional mode
"""

import serial
import time
import random
import json
import os
import sys
import threading
from datetime import datetime

class LinuxSerialComm:
    def __init__(self):
        self.running = False
        self.threads = []
    
    def check_serial_devices(self):
        """Check available serial devices"""
        devices = {
            '/dev/ttyS0': 'receive Windows -> Linux',
            '/dev/ttyS1': 'send Linux -> Windows'
        }
        
        print("🔍 Checking serial devices:")
        status = {}
        
        for device, purpose in devices.items():
            if os.path.exists(device):
                readable = os.access(device, os.R_OK)
                writable = os.access(device, os.W_OK)
                status[device] = readable and writable
                
                status_icon = "✅" if status[device] else "❌"
                print(f"  {status_icon} {device}: {purpose}")
                print(f"      read={readable}, write={writable}")
                
                if not status[device]:
                    print(f"      💡 Fix permissions: sudo chmod 666 {device}")
            else:
                status[device] = False
                print(f"  ❌ {device}: device not found")
                print(f"      💡 Check VMware settings")
        
        all_ready = all(status.values())
        
        if not all_ready:
            print("\n⚠️ How to adjust permissions:")
            print("  sudo usermod -a -G dialout $USER")
            print("  logout && login  # re-login required")
            print("or")
            print("  sudo chmod 666 /dev/ttyS*")
        
        return all_ready
    
    def send_to_windows(self, device='/dev/ttyS1', test_mode=True):
        """Send data from Linux to Windows"""
        description = f"Linux->Windows send ({device})"
        
        try:
            print(f"📤 Starting {description}...")
            if test_mode:
                print("🧪 Test mode: Ctrl+C to stop")
            
            with serial.Serial(device, 9600, timeout=1) as ser:
                counter = 1
                
                while self.running:
                    if test_mode:
                        # Test data patterns
                        test_patterns = [
                            f"LINUX_TO_WIN,{counter},{random.randint(20, 30)}.{random.randint(0, 99):02d},CPU_TEMP",
                            f"UBUNTU_STATUS,{counter},RUNNING,{datetime.now().strftime('%H:%M:%S')}",
                            f"SYSTEM_DATA,{counter},{random.randint(0, 100)},MEMORY_USAGE_PERCENT",
                            f"LINUX_HEARTBEAT,{counter},ALIVE_FROM_LINUX",
                            f"PROCESS_COUNT,{counter},{random.randint(100, 300)},TOTAL_PROCESSES",
                            f"NETWORK_STAT,{counter},{random.randint(1000, 9999)},PACKETS_PER_SEC",
                            json.dumps({
                                "id": counter,
                                "timestamp": datetime.now().isoformat(),
                                "source": "Linux_Guest",
                                "direction": "Linux_to_Windows",
                                "system": {
                                    "hostname": "ubuntu-vm",
                                    "uptime": random.randint(3600, 86400),
                                    "load_avg": round(random.uniform(0.1, 2.0), 2),
                                    "free_memory": random.randint(1000, 4000)
                                },
                                "sensors": {
                                    "cpu_temp": random.randint(40, 70),
                                    "fan_speed": random.randint(1000, 3000),
                                    "voltage": round(random.uniform(11.8, 12.2), 1)
                                }
                            })
                        ]
                        
                        message = random.choice(test_patterns) + "\r\n"
                    else:
                        # Manual input mode
                        message = input(f"[{counter:03d}] Message: ").strip()
                        if message.lower() == 'quit':
                            break
                        message = f"MANUAL,{counter},{message},{datetime.now().strftime('%H:%M:%S')}\r\n"
                    
                    # Perform send
                    ser.write(message.encode('utf-8'))
                    print(f"[TX {counter:03d}] Linux -> Windows: {message.strip()}")
                    
                    counter += 1
                    
                    if test_mode:
                        time.sleep(random.uniform(1.5, 3.0))
                    
        except KeyboardInterrupt:
            print(f"\n✅ Stopped {description}")
        except serial.SerialException as e:
            print(f"❌ Serial error ({device}): {e}")
            print("💡 Check device permissions or VMware settings")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            self.running = False
    
    def receive_from_windows(self, device='/dev/ttyS0'):
        """Monitor data from Windows"""
        try:
            print(f"📥 Start monitoring Windows -> Linux ({device})")
            
            with serial.Serial(device, 9600, timeout=1) as ser:
                buffer = ""
                
                while self.running:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        buffer += data
                        
                        # Process by line
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            if line:
                                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                                print(f"[RX {timestamp}] Windows -> Linux: {line}")
                    
                    time.sleep(0.01)
                    
        except serial.SerialException as e:
            print(f"❌ Receive error ({device}): {e}")
        except Exception as e:
            print(f"❌ Unexpected receive error: {e}")
        finally:
            print(f"📥 Monitoring stopped ({device})")
    
    def bidirectional_test(self):
        """Bidirectional communication test"""
        print("🔄 Starting bidirectional test")
        print("📤 /dev/ttyS1 -> Windows")
        print("📥 /dev/ttyS0 <- Windows")
        print("Ctrl+C to stop")
        print("=" * 40)
        
        self.running = True
        
        # 受信スレッド開始
        rx_thread = threading.Thread(
            target=self.receive_from_windows,
            args=('/dev/ttyS0',),
            name="Windows_RX"
        )
        rx_thread.daemon = True
        rx_thread.start()
        self.threads.append(rx_thread)
        
        # 送信開始（メインスレッド）
        self.send_to_windows('/dev/ttyS1', test_mode=True)
    
    def manual_communication(self):
        """Manual communication mode"""
        print("💬 Manual communication mode")
        print("📤 Send: /dev/ttyS1 -> Windows")
        print("📥 Receive: /dev/ttyS0 <- Windows")
        print("Type messages to send, 'quit' to exit")
        print("=" * 40)
        
        self.running = True
        
        # 受信スレッド開始
        rx_thread = threading.Thread(
            target=self.receive_from_windows,
            args=('/dev/ttyS0',),
            name="Manual_RX"
        )
        rx_thread.daemon = True
        rx_thread.start()
        self.threads.append(rx_thread)
        
        # 手動送信開始
        self.send_to_windows('/dev/ttyS1', test_mode=False)
    
    def performance_test(self):
        """Performance test"""
        print("⚡ Starting performance test")
        device = '/dev/ttyS1'
        duration = 30
        
        try:
            with serial.Serial(device, 9600, timeout=1) as ser:
                start_time = time.time()
                bytes_sent = 0
                packets_sent = 0
                
                print(f"📊 Measuring for {duration} seconds...")
                
                while time.time() - start_time < duration:
                    test_data = f"PERF_{packets_sent:06d}_" + "L" * 80 + "\r\n"
                    ser.write(test_data.encode('utf-8'))
                    
                    bytes_sent += len(test_data)
                    packets_sent += 1
                    
                    if packets_sent % 50 == 0:
                        elapsed = time.time() - start_time
                        bps = bytes_sent / elapsed if elapsed > 0 else 0
                        print(f"📈 Progress: {packets_sent} packets, {bps:.1f} bytes/sec")
                    
                    time.sleep(0.02)  # 50Hz
                
                # 結果
                elapsed = time.time() - start_time
                print(f"\n📊 Performance result:")
                print(f"  Packets sent: {packets_sent:,}")
                print(f"  Bytes sent: {bytes_sent:,}")
                print(f"  Elapsed: {elapsed:.2f}s")
                print(f"  Avg throughput: {bytes_sent/elapsed:.1f} bytes/sec")
                print(f"  Theoretical (9600baud): {9600/10:.1f} bytes/sec")
                print(f"  Efficiency: {(bytes_sent/elapsed)/(9600/10)*100:.1f}%")
                
        except Exception as e:
            print(f"❌ Performance test error: {e}")
    
    def stop_all(self):
        """Stop all communication"""
        self.running = False
        
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        print("✅ All communication stopped")

def main():
    """Main execution"""
    comm = LinuxSerialComm()
    
    print("=== Linux Serial Communication Tool (Enhanced) ===")
    print("🐧 VMware Guest - dual-pipe ready")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    
    # Initial check
    if not comm.check_serial_devices():
        print("\n❌ Serial devices not ready")
        print("Please resolve the issues above and try again")
        return
    
    try:
        while True:
            print("\n🎛️ Menu:")
            print("1. Check devices")
            print("2. Send test Linux->Windows")
            print("3. Monitor Windows->Linux")
            print("4. Bidirectional test")
            print("5. Manual communication")
            print("6. Performance test")
            print("7. VMware setup guide")
            print("8. Exit")
            
            choice = input("\nSelect an option (1-8): ").strip()
            
            if choice == "1":
                comm.check_serial_devices()
            
            elif choice == "2":
                comm.running = True
                comm.send_to_windows('/dev/ttyS1', test_mode=True)
            
            elif choice == "3":
                comm.running = True
                comm.receive_from_windows('/dev/ttyS0')
            
            elif choice == "4":
                comm.bidirectional_test()
            
            elif choice == "5":
                comm.manual_communication()
            
            elif choice == "6":
                comm.performance_test()
            
            elif choice == "7":
                print("\n=== VMware setup guide ===")
                print("[Required settings]")
                print("Serial port 1:")
                print("  Pipe name: \\\\.\\\pipe\\\\win_to_linux")
                print("  Purpose: Windows->Linux (/dev/ttyS0)")
                print()
                print("Serial port 2:")
                print("  Pipe name: \\\\.\\\pipe\\\\linux_to_win")
                print("  Purpose: Linux->Windows (/dev/ttyS1)")
                print()
                print("[Linux permissions]")
                print("sudo usermod -a -G dialout $USER && logout")
                print("or")
                print("sudo chmod 666 /dev/ttyS*")
            
            elif choice == "8":
                print("👋 Exiting")
                break
            
            else:
                print("❌ Please choose 1-8")
                
    except KeyboardInterrupt:
        print("\n👋 Exiting")
    finally:
        comm.stop_all()

if __name__ == "__main__":
    main()
