#!/usr/bin/env python3
"""
VMware dual-pipe communication - Windows side
Provides true bidirectional transfer
"""

import win32pipe
import win32file
import win32event
import win32api
import threading
import time
import json
import signal
import sys
import atexit
from datetime import datetime
import pywintypes

class DualPipeComm:
    def __init__(self):
        self.running = False
        self.tx_pipe = None  # Windows->Linux (TX)
        self.rx_pipe = None  # Linux->Windows (RX)
        self.threads = []
        
        # Graceful shutdown setup
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signal"""
        print(f"\n⚠️ Received termination signal")
        self.safe_shutdown()
        sys.exit(0)
    
    def safe_shutdown(self):
        """Graceful shutdown"""
        print("🛑 Performing graceful shutdown...")
        self.running = False
        
        # Wait for threads
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        self.cleanup()
        print("✅ Shutdown complete")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.tx_pipe:
                win32file.CloseHandle(self.tx_pipe)
                self.tx_pipe = None
                print("📤 TX pipe closed")
        except:
            pass
        
        try:
            if self.rx_pipe:
                win32file.CloseHandle(self.rx_pipe)
                self.rx_pipe = None
                print("📥 RX pipe closed")
        except:
            pass
    
    def connect_pipe_safe(self, pipe_name, timeout=5000):
        """Safely connect to a named pipe"""
        print(f"🔌 Connecting: {pipe_name}")
        
        try:
            # Wait for pipe
            win32pipe.WaitNamedPipe(pipe_name, timeout)
            
            # Connect in overlapped mode
            handle = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                win32file.FILE_FLAG_OVERLAPPED,
                None
            )
            
            print(f"✅ Connected: {pipe_name}")
            return handle
            
        except Exception as e:
            print(f"❌ Connection failed {pipe_name}: {e}")
            return None
    
    def dual_pipe_communication(self):
        """Bidirectional communication using two pipes"""
        print("=== VMware dual-pipe communication ===")
        print("📤 TX: \\\\.\\\pipe\\\\win_to_linux")
        print("📥 RX: \\\\.\\\pipe\\\\linux_to_win")
        print("💡 Press Ctrl+C to exit")
        print("=" * 50)
        
        # Connect pipes
        self.tx_pipe = self.connect_pipe_safe(r"\\.\pipe\win_to_linux")
        self.rx_pipe = self.connect_pipe_safe(r"\\.\pipe\linux_to_win")
        
        if not self.tx_pipe:
            print("❌ Failed to connect TX pipe")
            print("💡 Check VMware settings:")
            print("   Serial port 1: \\\\.\\\pipe\\\\win_to_linux")
            return False
        
        if not self.rx_pipe:
            print("❌ Failed to connect RX pipe")
            print("💡 Check VMware settings:")
            print("   Serial port 2: \\\\.\\\pipe\\\\linux_to_win")
            return False
        
        print("✅ Dual pipe connected")
        print("🚀 Starting bidirectional transfer...")
        
        self.running = True
        
        # Start RX thread
        rx_thread = threading.Thread(
            target=self.receive_from_linux,
            name="Linux_RX_Thread"
        )
        rx_thread.daemon = True
        rx_thread.start()
        self.threads.append(rx_thread)
        
        # Start sending loop
        self.send_to_linux()
        
        return True
    
    def send_to_linux(self):
        """Send data from Windows to Linux"""
        counter = 1
        last_send = time.time()
        
        print("📤 Windows -> Linux TX start")
        
        try:
            while self.running:
                current_time = time.time()
                
                # Send every 2 seconds
                if current_time - last_send >= 2.0:
                    message = {
                        "id": counter,
                        "timestamp": datetime.now().isoformat(),
                        "source": "Windows_Host",
                        "direction": "Win_to_Linux",
                        "data": f"Windows_Message_{counter:03d}",
                        "system_info": {
                            "platform": "Windows",
                            "counter": counter
                        }
                    }
                    
                    try:
                        data = (json.dumps(message) + "\n").encode('utf-8')
                        
                        # Asynchronous send
                        overlapped = pywintypes.OVERLAPPED()
                        overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
                        
                        win32file.WriteFile(self.tx_pipe, data, overlapped)
                        result = win32event.WaitForSingleObject(overlapped.hEvent, 1000)
                        
                        if result == win32event.WAIT_OBJECT_0:
                            print(f"[TX {counter:03d}] Windows -> Linux: {message['data']}")
                            counter += 1
                            last_send = current_time
                        else:
                            print(f"⚠️ Send timeout: {counter}")
                        
                        win32api.CloseHandle(overlapped.hEvent)
                        
                    except Exception as e:
                        print(f"❌ Send error: {e}")
                        break
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            pass
        finally:
            print("📤 Windows TX ended")
    
    def receive_from_linux(self):
        """Receive data from Linux"""
        buffer = b""
        
        print("📥 Waiting for Linux -> Windows")
        
        try:
            while self.running:
                try:
                    overlapped = pywintypes.OVERLAPPED()
                    overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
                    
                    # Asynchronous read
                    win32file.ReadFile(self.rx_pipe, 1024, overlapped)
                    result = win32event.WaitForSingleObject(overlapped.hEvent, 100)
                    
                    if result == win32event.WAIT_OBJECT_0:
                        bytes_read = win32file.GetOverlappedResult(self.rx_pipe, overlapped, False)
                        if bytes_read > 0:
                            # Get actual data
                            try:
                                # Retrieve data from overlapped
                                _, data = win32file.ReadFile(self.rx_pipe, bytes_read)
                                buffer += data
                                
                                # Process per line
                                while b"\n" in buffer:
                                    line, buffer = buffer.split(b"\n", 1)
                                    if line:
                                        msg = line.decode('utf-8', errors='ignore').strip()
                                        if msg:
                                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                                            print(f"[RX {timestamp}] Linux -> Windows: {msg}")
                            except:
                                # Handle overlapping ReadFile
                                pass
                    
                    win32api.CloseHandle(overlapped.hEvent)
                    
                except pywintypes.error as e:
                    if e.args[0] == 109:  # ERROR_BROKEN_PIPE
                        print("⚠️ Linux side pipe closed")
                        break
                    elif e.args[0] == 232:  # ERROR_NO_DATA
                        pass  # No data (normal)
                
                time.sleep(0.01)
                
        except Exception as e:
            print(f"❌ Receive error: {e}")
        finally:
            print("📥 Linux RX ended")
    
    def test_pipes(self):
        """Test pipe connections"""
        print("=== Dual pipe connection test ===")
        
        pipes = [
            (r"\\.\pipe\win_to_linux", "Windows->Linux"),
            (r"\\.\pipe\linux_to_win", "Linux->Windows")
        ]
        
        for pipe_name, description in pipes:
            print(f"\n🔍 Test: {description}")
            print(f"   Pipe: {pipe_name}")
            
            try:
                win32pipe.WaitNamedPipe(pipe_name, 1000)
                print(f"   ✅ Pipe detected")
                
                handle = self.connect_pipe_safe(pipe_name, 2000)
                if handle:
                    print(f"   ✅ Connection test passed")
                    win32file.CloseHandle(handle)
                else:
                    print(f"   ❌ Connection test failed")
                    
            except Exception as e:
                print(f"   ❌ Pipe not found: {e}")
                print(f"   💡 Check VMware settings")

def main():
    """Main execution"""
    comm = DualPipeComm()
    
    print("🔧 VMware dual-pipe communication tool")
    print("=" * 40)
    print("1. Test pipe connections")
    print("2. Start communication")
    print("3. VMware configuration guide")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nSelect an option (1-4): ").strip()
            
            if choice == "1":
                comm.test_pipes()
            
            elif choice == "2":
                if comm.dual_pipe_communication():
                    print("✅ Communication session ended")
                else:
                    print("❌ Failed to start communication")
            
            elif choice == "3":
                print("\n=== VMware configuration guide ===")
                print("[Serial Port 1]")
                print("  Connection: Named pipe")
                print("  Pipe name: \\\\.\\\pipe\\\\win_to_linux")
                print("  End: Server")
                print("  I/O mode: Application")
                print()
                print("[Serial Port 2]")
                print("  Connection: Named pipe")
                print("  Pipe name: \\\\.\\\pipe\\\\linux_to_win")
                print("  End: Server")
                print("  I/O mode: Application")
                print()
                print("[Linux mapping]")
                print("  /dev/ttyS0 : receive from Windows")
                print("  /dev/ttyS1 : send to Windows")
            
            elif choice == "4":
                print("👋 Exiting")
                break
            
            else:
                print("❌ Please choose 1-4")
                
        except KeyboardInterrupt:
            print("\n👋 Exiting")
            break
    
    comm.cleanup()

if __name__ == "__main__":
    main()
