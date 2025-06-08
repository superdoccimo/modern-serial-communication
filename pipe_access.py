#!/usr/bin/env python3
"""
改良版VMware名前付きパイプ双方向通信
Windows側実装 - フリーズ対策版
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
        
        # 終了時のクリーンアップを登録
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """シグナルハンドラー（Ctrl+C対応）"""
        print(f"\n⚠️ 終了シグナル受信 (Signal: {signum})")
        print("安全にクリーンアップ中...")
        self.safe_shutdown()
        sys.exit(0)
    
    def safe_shutdown(self):
        """安全な終了処理"""
        print("🛑 安全終了処理開始")
        self.running = False
        
        # スレッド終了を少し待つ
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        self.cleanup()
        print("✅ 安全終了完了")
    
    def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.tx_pipe:
                win32file.CloseHandle(self.tx_pipe)
                self.tx_pipe = None
                print("📤 TX パイプクローズ")
        except:
            pass
        
        try:
            if self.rx_pipe:
                win32file.CloseHandle(self.rx_pipe)
                self.rx_pipe = None
                print("📥 RX パイプクローズ")
        except:
            pass
    
    def connect_to_pipe_safe(self, pipe_name, timeout=5000):
        """安全な名前付きパイプ接続"""
        print(f"🔌 パイプ接続試行: {pipe_name}")
        
        try:
            # パイプの存在確認
            if not self.wait_for_pipe(pipe_name, timeout):
                print(f"❌ パイプ待機タイムアウト: {pipe_name}")
                return None
            
            # 非ブロッキングモードでパイプ接続
            handle = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                win32file.FILE_FLAG_OVERLAPPED,  # 非同期I/O
                None
            )
            
            print(f"✅ パイプ接続成功: {pipe_name}")
            return handle
            
        except pywintypes.error as e:
            error_code, error_text, _ = e.args
            print(f"❌ パイプ接続エラー {pipe_name}: {error_text} (Code: {error_code})")
            return None
        except Exception as e:
            print(f"❌ 予期しないエラー {pipe_name}: {e}")
            return None
    
    def wait_for_pipe(self, pipe_name, timeout=5000):
        """パイプの準備完了を待機"""
        try:
            win32pipe.WaitNamedPipe(pipe_name, timeout)
            return True
        except:
            return False
    
    def bidirectional_communication(self):
        """双方向通信実行（改良版）"""
        print("=== VMware名前付きパイプ双方向通信（改良版） ===")
        print("💡 Ctrl+C で安全に終了できます")
        print("=" * 50)
        
        # パイプ接続
        print("🔄 パイプ接続中...")
        self.tx_pipe = self.connect_to_pipe_safe(r"\\.\pipe\vmware_tx")
        self.rx_pipe = self.connect_to_pipe_safe(r"\\.\pipe\vmware_rx")
        
        if not self.tx_pipe:
            print("❌ 送信パイプ接続失敗")
            print("💡 VMware設定を確認してください:")
            print("   - VM設定 → シリアルポート")
            print("   - パイプ名: \\\\\.\\pipe\\vmware_tx")
            return False
        
        if not self.rx_pipe:
            print("❌ 受信パイプ接続失敗")
            print("💡 VMware設定を確認してください:")
            print("   - VM設定 → シリアルポート")
            print("   - パイプ名: \\\\\.\\pipe\\vmware_rx")
            return False
        
        print("✅ 両方向パイプ接続成功")
        print("🚀 通信開始...")
        
        self.running = True
        
        # 受信スレッド開始
        rx_thread = threading.Thread(
            target=self.receive_data_safe, 
            args=(self.rx_pipe,),
            name="RX_Thread"
        )
        rx_thread.daemon = True
        rx_thread.start()
        self.threads.append(rx_thread)
        
        # 送信ループ
        self.send_data_safe(self.tx_pipe)
        
        return True
    
    def send_data_safe(self, pipe_handle):
        """安全なデータ送信"""
        counter = 1
        last_send_time = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                
                # 2秒間隔で送信
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
                        
                        # オーバーラップI/O用構造体
                        overlapped = pywintypes.OVERLAPPED()
                        overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
                        
                        # 非同期書き込み
                        win32file.WriteFile(pipe_handle, data, overlapped)
                        
                        # 完了待機（タイムアウト付き）
                        result = win32event.WaitForSingleObject(overlapped.hEvent, 1000)
                        
                        if result == win32event.WAIT_OBJECT_0:
                            print(f"[TX {counter:03d}] → Linux: {message['data']}")
                            counter += 1
                            last_send_time = current_time
                        elif result == win32event.WAIT_TIMEOUT:
                            print(f"⚠️ 送信タイムアウト: Message_{counter:03d}")
                        
                        # イベントハンドルクローズ
                        win32api.CloseHandle(overlapped.hEvent)
                        
                    except pywintypes.error as e:
                        error_code = e.args[0]
                        if error_code == 109:  # ERROR_BROKEN_PIPE
                            print("⚠️ パイプが切断されました")
                            break
                        else:
                            print(f"❌ 送信エラー: {e}")
                            break
                    except Exception as e:
                        print(f"❌ 予期しない送信エラー: {e}")
                        break
                
                # CPU使用率を下げるため少し待機
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("📤 送信ループ終了")
        finally:
            print("📤 送信スレッド終了")
    
    def receive_data_safe(self, pipe_handle):
        """安全なデータ受信"""
        buffer = b""
        
        try:
            while self.running:
                try:
                    # オーバーラップI/O用構造体
                    overlapped = pywintypes.OVERLAPPED()
                    overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
                    
                    # 非同期読み取り
                    try:
                        win32file.ReadFile(pipe_handle, 1024, overlapped)
                        
                        # 完了待機（短いタイムアウト）
                        result = win32event.WaitForSingleObject(overlapped.hEvent, 100)
                        
                        if result == win32event.WAIT_OBJECT_0:
                            # データ取得
                            bytes_read = win32file.GetOverlappedResult(pipe_handle, overlapped, False)
                            if bytes_read > 0:
                                data = win32file.GetOverlappedResult(pipe_handle, overlapped, True)
                                buffer += data
                                
                                # 行単位で処理
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
                        
                        # イベントハンドルクローズ
                        win32api.CloseHandle(overlapped.hEvent)
                        
                    except pywintypes.error as e:
                        error_code = e.args[0]
                        if error_code == 109:  # ERROR_BROKEN_PIPE
                            print("⚠️ 受信パイプが切断されました")
                            break
                        elif error_code == 232:  # ERROR_NO_DATA
                            # データなし（正常）
                            pass
                        else:
                            print(f"❌ 受信エラー: {e}")
                            break
                
                except Exception as e:
                    print(f"❌ 予期しない受信エラー: {e}")
                    break
                
                # CPU使用率調整
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("📥 受信ループ終了")
        finally:
            print("📥 受信スレッド終了")
    
    def test_pipe_connection(self):
        """パイプ接続テスト"""
        print("=== パイプ接続テスト ===")
        
        pipes_to_test = [
            r"\\.\pipe\vmware_tx",
            r"\\.\pipe\vmware_rx"
        ]
        
        for pipe_name in pipes_to_test:
            print(f"\n🔍 テスト中: {pipe_name}")
            
            if self.wait_for_pipe(pipe_name, 1000):
                print(f"✅ パイプ検出: {pipe_name}")
                
                # 接続テスト
                handle = self.connect_to_pipe_safe(pipe_name, 2000)
                if handle:
                    print(f"✅ 接続成功: {pipe_name}")
                    win32file.CloseHandle(handle)
                else:
                    print(f"❌ 接続失敗: {pipe_name}")
            else:
                print(f"❌ パイプ未検出: {pipe_name}")
                print("💡 VMware設定確認:")
                print("   1. VM設定 → シリアルポート追加")
                print("   2. 接続方法: 名前付きパイプを使用")
                print(f"   3. パイプ名: {pipe_name}")
                print("   4. パイプの端: サーバー")
                print("   5. I/Oモード: アプリケーション")

def main():
    """メイン実行"""
    comm = VMwarePipeComm()
    
    print("🔧 VMware名前付きパイプ通信ツール")
    print("=" * 40)
    print("1. パイプ接続テスト")
    print("2. 双方向通信開始")
    print("3. 終了")
    
    while True:
        try:
            choice = input("\n選択してください (1-3): ").strip()
            
            if choice == "1":
                comm.test_pipe_connection()
            
            elif choice == "2":
                if comm.bidirectional_communication():
                    print("✅ 通信セッション終了")
                else:
                    print("❌ 通信開始失敗")
            
            elif choice == "3":
                print("👋 終了します")
                break
            
            else:
                print("❌ 1-3を選択してください")
                
        except KeyboardInterrupt:
            print("\n\n👋 終了します")
            break
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    # 最終クリーンアップ
    comm.cleanup()

if __name__ == "__main__":
    main()