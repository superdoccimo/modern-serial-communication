#!/usr/bin/env python3
"""
Enhanced VMware named pipe bidirectional communication
Windows implementation with freeze prevention
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

class VMwarePipeComm:
    def __init__(self):
        self.running = False
        self.tx_pipe = None
        self.rx_pipe = None
        self.threads = []
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Signal handler for Ctrl+C"""
        print(f"\n⚠️ Termination signal received (Signal: {signum})")
        print("Cleaning up safely...")
        self.safe_shutdown()
        sys.exit(0)
    
    def safe_shutdown(self):
        """Graceful shutdown"""
        print("🛑 Starting graceful shutdown")
        self.running = False
        
        # Wait briefly for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        self.cleanup()
        print("✅ Shutdown complete")
    
    def cleanup(self):
        """Resource cleanup"""
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
    
    def connect_to_pipe_safe(self, pipe_name, timeout=5000):
        """Safely connect to a named pipe"""
        print(f"🔌 Attempting pipe connection: {pipe_name}")
        
        try:
            # Check if the pipe exists
            if not self.wait_for_pipe(pipe_name, timeout):
                print(f"❌ Pipe wait timeout: {pipe_name}")
                return None
            
            # Connect in non-blocking mode
            handle = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                win32file.FILE_FLAG_OVERLAPPED,  # asynchronous I/O
                None
            )
            
            print(f"✅ Pipe connection succeeded: {pipe_name}")
            return handle
            
        except pywintypes.error as e:
            error_code, error_text, _ = e.args
            print(f"❌ Pipe connection error {pipe_name}: {error_text} (Code: {error_code})")
            return None
        except Exception as e:
            print(f"❌ Unexpected error {pipe_name}: {e}")
            return None
    
    def wait_for_pipe(self, pipe_name, timeout=5000):
        """Wait for the pipe to become ready"""
        try:
            win32pipe.WaitNamedPipe(pipe_name, timeout)
            return True
        except:
            return False
    
    def bidirectional_communication(self):
        """Run bidirectional communication (enhanced)"""
        print("=== VMware named pipe bidirectional communication (enhanced) ===")
        print("💡 Press Ctrl+C to exit safely")
        print("=" * 50)
        
        # Connect pipes
        print("🔄 Connecting to pipes...")
        self.tx_pipe = self.connect_to_pipe_safe(r"\\.\pipe\vmware_tx")
        self.rx_pipe = self.connect_to_pipe_safe(r"\\.\pipe\vmware_rx")
        
        if not self.tx_pipe:
            print("❌ Failed to connect TX pipe")
            print("💡 Check VMware settings:")
            print("   - VM settings -> Serial port")
            print("   - Pipe name: \\\\.\\pipe\\vmware_tx")
            return False
        
        if not self.rx_pipe:
            print("❌ Failed to connect RX pipe")
            print("💡 Check VMware settings:")
            print("   - VM settings -> Serial port")
            print("   - Pipe name: \\\\.\\pipe\\vmware_rx")
            return False
        
        print("✅ Both pipes connected")
        print("🚀 Starting communication...")
        
        self.running = True
        
        # Start RX thread
        rx_thread = threading.Thread(
            target=self.receive_data_safe, 
            args=(self.rx_pipe,),
            name="RX_Thread"
        )
        rx_thread.daemon = True
        rx_thread.start()
        self.threads.append(rx_thread)
        
        # Send loop
        self.send_data_safe(self.tx_pipe)
        
        return True
    
    def send_data_safe(self, pipe_handle):
        """Safely send data"""
        counter = 1
        last_send_time = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                
                # Send every 2 seconds
                if current_time - last_send_time >= 2.0:
                    message = {
                        "id": counter,
                        "timestamp": datetime.now().isoformat(),
                        "source": "Windows_Host",
                        "data": f"Message_{counter:03d}",
                        "sequence": counter
                    }
                    
                    try:
                        data = (json.dumps(message) + "\n").encode('utf-8')
                        
                        # Overlapped I/O structure
                        overlapped = pywintypes.OVERLAPPED()
                        overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
                        
                        # Asynchronous write
                        win32file.WriteFile(pipe_handle, data, overlapped)
                        
                        # Wait for completion (timeout)
                        result = win32event.WaitForSingleObject(overlapped.hEvent, 1000)
                        
                        if result == win32event.WAIT_OBJECT_0:
                            print(f"[TX {counter:03d}] → Linux: {message['data']}")
                            counter += 1
                            last_send_time = current_time
                        elif result == win32event.WAIT_TIMEOUT:
                            print(f"⚠️ Send timeout: Message_{counter:03d}")
                        
                        # Close event handle
                        win32api.CloseHandle(overlapped.hEvent)
                        
                    except pywintypes.error as e:
                        error_code = e.args[0]
                        if error_code == 109:  # ERROR_BROKEN_PIPE
                            print("⚠️ Pipe disconnected")
                            break
                        else:
                            print(f"❌ Send error: {e}")
                            break
                    except Exception as e:
                        print(f"❌ Unexpected send error: {e}")
                        break
                
                # Sleep briefly to reduce CPU usage
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("📤 Send loop ended")
        finally:
            print("📤 Send thread ended")
    
    def receive_data_safe(self, pipe_handle):
        """Safely receive data"""
        buffer = b""
        
        try:
            while self.running:
                try:
                    # Overlapped I/O structure
                    overlapped = pywintypes.OVERLAPPED()
                    overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
                    
                    # Asynchronous read
                    try:
                        win32file.ReadFile(pipe_handle, 1024, overlapped)
                        
                        # Wait for completion (short timeout)
                        result = win32event.WaitForSingleObject(overlapped.hEvent, 100)
                        
                        if result == win32event.WAIT_OBJECT_0:
                            # Retrieve data
                            bytes_read = win32file.GetOverlappedResult(pipe_handle, overlapped, False)
                            if bytes_read > 0:
                                data = win32file.GetOverlappedResult(pipe_handle, overlapped, True)
                                buffer += data
                                
                                # Process per line
                                while b"\n" in buffer:
                                    line, buffer = buffer.split(b"\n", 1)
                                    if line:
                                        try:
                                            msg = line.decode('utf-8', errors='ignore').strip()
                                            if msg:
                                                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                                                print(f"[RX {timestamp}] ← Linux: {msg}")
                                        except:
                                            pass
                        
                        # Close event handle
                        win32api.CloseHandle(overlapped.hEvent)
                        
                    except pywintypes.error as e:
                        error_code = e.args[0]
                        if error_code == 109:  # ERROR_BROKEN_PIPE
                            print("⚠️ RX pipe disconnected")
                            break
                        elif error_code == 232:  # ERROR_NO_DATA
                            # No data (normal)
                            pass
                        else:
                            print(f"❌ Receive error: {e}")
                            break
                
                except Exception as e:
                    print(f"❌ Unexpected receive error: {e}")
                    break
                
                # Adjust CPU usage
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("📥 Receive loop ended")
        finally:
            print("📥 Receive thread ended")
    
    def test_pipe_connection(self):
        """Test pipe connections"""
        print("=== Pipe connection test ===")
        
        pipes_to_test = [
            r"\\.\pipe\vmware_tx",
            r"\\.\pipe\vmware_rx"
        ]
        
        for pipe_name in pipes_to_test:
            print(f"\n🔍 Testing: {pipe_name}")
            
            if self.wait_for_pipe(pipe_name, 1000):
                print(f"✅ Pipe detected: {pipe_name}")
                
                # Connection test
                handle = self.connect_to_pipe_safe(pipe_name, 2000)
                if handle:
                    print(f"✅ Connection successful: {pipe_name}")
                    win32file.CloseHandle(handle)
                else:
                    print(f"❌ Connection failed: {pipe_name}")
            else:
                print(f"❌ Pipe not detected: {pipe_name}")
                print("💡 VMware configuration:")
                print("   1. Add a serial port in the VM settings")
                print("   2. Choose 'Use named pipe'")
                print(f"   3. Pipe name: {pipe_name}")
                print("   4. Endpoint: Server")
                print("   5. I/O mode: Application")

def main():
    """Main execution"""
    comm = VMwarePipeComm()
    
    print("🔧 VMware named pipe communication tool")
    print("=" * 40)
    print("1. Test pipe connection")
    print("2. Start bidirectional communication")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nSelect an option (1-3): ").strip()
            
            if choice == "1":
                comm.test_pipe_connection()
            
            elif choice == "2":
                if comm.bidirectional_communication():
                    print("✅ Communication session ended")
                else:
                    print("❌ Failed to start communication")
            
            elif choice == "3":
                print("👋 Exiting")
                break
            
            else:
                print("❌ Please select 1-3")
                
        except KeyboardInterrupt:
            print("\n\n👋 Exiting")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Final cleanup
    comm.cleanup()

if __name__ == "__main__":
    main()
