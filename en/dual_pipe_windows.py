#!/usr/bin/env python3
"""
VMware デュアルパイプ双方向通信 - Windows側
真の双方向通信を実現
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
        self.tx_pipe = None  # Windows→Linux（送信）
        self.rx_pipe = None  # Linux→Windows（受信）
        self.threads = []
        
        # 安全終了設定
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """安全終了処理"""
        print(f"\n⚠️ 終了シグナル受信")
        self.safe_shutdown()
        sys.exit(0)
    
    def safe_shutdown(self):
        """安全な終了"""
        print("🛑 安全終了処理...")
        self.running = False
        
        # スレッド終了待ち
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        self.cleanup()
        print("✅ 終了完了")
    
    def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.tx_pipe:
                win32file.CloseHandle(self.tx_pipe)
                self.tx_pipe = None
                print("📤 送信パイプクローズ")
        except:
            pass
        
        try:
            if self.rx_pipe:
                win32file.CloseHandle(self.rx_pipe)
                self.rx_pipe = None
                print("📥 受信パイプクローズ")
        except:
            pass
    
    def connect_pipe_safe(self, pipe_name, timeout=5000):
        """安全なパイプ接続"""
        print(f"🔌 接続試行: {pipe_name}")
        
        try:
            # パイプ待機
            win32pipe.WaitNamedPipe(pipe_name, timeout)
            
            # 非同期モードで接続
            handle = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                win32file.FILE_FLAG_OVERLAPPED,
                None
            )
            
            print(f"✅ 接続成功: {pipe_name}")
            return handle
            
        except Exception as e:
            print(f"❌ 接続失敗 {pipe_name}: {e}")
            return None
    
    def dual_pipe_communication(self):
        """デュアルパイプ双方向通信"""
        print("=== VMware デュアルパイプ双方向通信 ===")
        print("📤 送信用: \\\\.\\\pipe\\\\win_to_linux")
        print("📥 受信用: \\\\.\\\pipe\\\\linux_to_win")
        print("💡 Ctrl+Cで安全終了")
        print("=" * 50)
        
        # パイプ接続
        self.tx_pipe = self.connect_pipe_safe(r"\\.\pipe\win_to_linux")
        self.rx_pipe = self.connect_pipe_safe(r"\\.\pipe\linux_to_win")
        
        if not self.tx_pipe:
            print("❌ 送信パイプ接続失敗")
            print("💡 VMware設定確認:")
            print("   シリアルポート1: \\\\.\\\pipe\\\\win_to_linux")
            return False
        
        if not self.rx_pipe:
            print("❌ 受信パイプ接続失敗") 
            print("💡 VMware設定確認:")
            print("   シリアルポート2: \\\\.\\\pipe\\\\linux_to_win")
            return False
        
        print("✅ デュアルパイプ接続成功")
        print("🚀 双方向通信開始...")
        
        self.running = True
        
        # 受信スレッド起動
        rx_thread = threading.Thread(
            target=self.receive_from_linux,
            name="Linux_RX_Thread"
        )
        rx_thread.daemon = True
        rx_thread.start()
        self.threads.append(rx_thread)
        
        # 送信メインループ
        self.send_to_linux()
        
        return True
    
    def send_to_linux(self):
        """Windows→Linux送信"""
        counter = 1
        last_send = time.time()
        
        print("📤 Windows→Linux送信開始")
        
        try:
            while self.running:
                current_time = time.time()
                
                # 2秒間隔で送信
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
                        
                        # 非同期送信
                        overlapped = pywintypes.OVERLAPPED()
                        overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
                        
                        win32file.WriteFile(self.tx_pipe, data, overlapped)
                        result = win32event.WaitForSingleObject(overlapped.hEvent, 1000)
                        
                        if result == win32event.WAIT_OBJECT_0:
                            print(f"[TX {counter:03d}] Windows → Linux: {message['data']}")
                            counter += 1
                            last_send = current_time
                        else:
                            print(f"⚠️ 送信タイムアウト: {counter}")
                        
                        win32api.CloseHandle(overlapped.hEvent)
                        
                    except Exception as e:
                        print(f"❌ 送信エラー: {e}")
                        break
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            pass
        finally:
            print("📤 Windows送信終了")
    
    def receive_from_linux(self):
        """Linux→Windows受信"""
        buffer = b""
        
        print("📥 Linux→Windows受信待機")
        
        try:
            while self.running:
                try:
                    overlapped = pywintypes.OVERLAPPED()
                    overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
                    
                    # 非同期読み取り
                    win32file.ReadFile(self.rx_pipe, 1024, overlapped)
                    result = win32event.WaitForSingleObject(overlapped.hEvent, 100)
                    
                    if result == win32event.WAIT_OBJECT_0:
                        bytes_read = win32file.GetOverlappedResult(self.rx_pipe, overlapped, False)
                        if bytes_read > 0:
                            # データ取得（実際の読み取り）
                            try:
                                # overlappedから実際のデータを取得
                                _, data = win32file.ReadFile(self.rx_pipe, bytes_read)
                                buffer += data
                                
                                # 行単位処理
                                while b"\n" in buffer:
                                    line, buffer = buffer.split(b"\n", 1)
                                    if line:
                                        msg = line.decode('utf-8', errors='ignore').strip()
                                        if msg:
                                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                                            print(f"[RX {timestamp}] Linux → Windows: {msg}")
                            except:
                                # ReadFileが重複する場合の対処
                                pass
                    
                    win32api.CloseHandle(overlapped.hEvent)
                    
                except pywintypes.error as e:
                    if e.args[0] == 109:  # ERROR_BROKEN_PIPE
                        print("⚠️ Linux側パイプ切断")
                        break
                    elif e.args[0] == 232:  # ERROR_NO_DATA
                        pass  # データなし（正常）
                
                time.sleep(0.01)
                
        except Exception as e:
            print(f"❌ 受信エラー: {e}")
        finally:
            print("📥 Linux受信終了")
    
    def test_pipes(self):
        """パイプ接続テスト"""
        print("=== デュアルパイプ接続テスト ===")
        
        pipes = [
            (r"\\.\pipe\win_to_linux", "Windows→Linux"),
            (r"\\.\pipe\linux_to_win", "Linux→Windows")
        ]
        
        for pipe_name, description in pipes:
            print(f"\n🔍 テスト: {description}")
            print(f"   パイプ: {pipe_name}")
            
            try:
                win32pipe.WaitNamedPipe(pipe_name, 1000)
                print(f"   ✅ パイプ検出成功")
                
                handle = self.connect_pipe_safe(pipe_name, 2000)
                if handle:
                    print(f"   ✅ 接続テスト成功")
                    win32file.CloseHandle(handle)
                else:
                    print(f"   ❌ 接続テスト失敗")
                    
            except Exception as e:
                print(f"   ❌ パイプ未検出: {e}")
                print(f"   💡 VMware設定確認が必要")

def main():
    """メイン実行"""
    comm = DualPipeComm()
    
    print("🔧 VMware デュアルパイプ通信ツール")
    print("=" * 40)
    print("1. パイプ接続テスト")
    print("2. 双方向通信開始")  
    print("3. VMware設定ガイド")
    print("4. 終了")
    
    while True:
        try:
            choice = input("\n選択してください (1-4): ").strip()
            
            if choice == "1":
                comm.test_pipes()
            
            elif choice == "2":
                if comm.dual_pipe_communication():
                    print("✅ 通信セッション終了")
                else:
                    print("❌ 通信開始失敗")
            
            elif choice == "3":
                print("\n=== VMware設定ガイド ===")
                print("【シリアルポート1設定】")
                print("  接続方法: 名前付きパイプを使用")
                print("  パイプ名: \\\\.\\\pipe\\\\win_to_linux")
                print("  パイプの端: サーバー")
                print("  I/Oモード: アプリケーション")
                print()
                print("【シリアルポート2設定】")
                print("  接続方法: 名前付きパイプを使用")
                print("  パイプ名: \\\\.\\\pipe\\\\linux_to_win")
                print("  パイプの端: サーバー")
                print("  I/Oモード: アプリケーション")
                print()
                print("【Linux側対応】")
                print("  /dev/ttyS0 ← Windows送信を受信")
                print("  /dev/ttyS1 → Windowsへ送信")
            
            elif choice == "4":
                print("👋 終了します")
                break
            
            else:
                print("❌ 1-4を選択してください")
                
        except KeyboardInterrupt:
            print("\n👋 終了します")
            break
    
    comm.cleanup()

if __name__ == "__main__":
    main()
