#!/usr/bin/env python3
"""
改良版Linux用シリアル通信ツール
VMwareデュアルパイプ対応・双方向通信
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
        """シリアルデバイス確認"""
        devices = {
            '/dev/ttyS0': 'Windows→Linux受信用',
            '/dev/ttyS1': 'Linux→Windows送信用'
        }
        
        print("🔍 シリアルデバイス確認:")
        status = {}
        
        for device, purpose in devices.items():
            if os.path.exists(device):
                readable = os.access(device, os.R_OK)
                writable = os.access(device, os.W_OK)
                status[device] = readable and writable
                
                status_icon = "✅" if status[device] else "❌"
                print(f"  {status_icon} {device}: {purpose}")
                print(f"      読み取り={readable}, 書き込み={writable}")
                
                if not status[device]:
                    print(f"      💡 権限修正: sudo chmod 666 {device}")
            else:
                status[device] = False
                print(f"  ❌ {device}: デバイスが存在しません")
                print(f"      💡 VMware設定を確認してください")
        
        all_ready = all(status.values())
        
        if not all_ready:
            print("\n⚠️ 権限修正方法:")
            print("  sudo usermod -a -G dialout $USER")
            print("  logout && login  # 再ログイン必要")
            print("または")
            print("  sudo chmod 666 /dev/ttyS*")
        
        return all_ready
    
    def send_to_windows(self, device='/dev/ttyS1', test_mode=True):
        """Linux→Windows送信"""
        description = f"Linux→Windows送信 ({device})"
        
        try:
            print(f"📤 {description}開始...")
            if test_mode:
                print("🧪 テストモード: Ctrl+Cで停止")
            
            with serial.Serial(device, 9600, timeout=1) as ser:
                counter = 1
                
                while self.running:
                    if test_mode:
                        # テストデータパターン
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
                        # 手動入力モード
                        message = input(f"[{counter:03d}] メッセージ: ").strip()
                        if message.lower() == 'quit':
                            break
                        message = f"MANUAL,{counter},{message},{datetime.now().strftime('%H:%M:%S')}\r\n"
                    
                    # 送信実行
                    ser.write(message.encode('utf-8'))
                    print(f"[TX {counter:03d}] Linux → Windows: {message.strip()}")
                    
                    counter += 1
                    
                    if test_mode:
                        time.sleep(random.uniform(1.5, 3.0))
                    
        except KeyboardInterrupt:
            print(f"\n✅ {description}を停止")
        except serial.SerialException as e:
            print(f"❌ シリアルエラー ({device}): {e}")
            print("💡 デバイス権限・VMware設定を確認してください")
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
        finally:
            self.running = False
    
    def receive_from_windows(self, device='/dev/ttyS0'):
        """Windows→Linux受信監視"""
        try:
            print(f"📥 Windows→Linux受信監視開始 ({device})")
            
            with serial.Serial(device, 9600, timeout=1) as ser:
                buffer = ""
                
                while self.running:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        buffer += data
                        
                        # 行単位処理
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            if line:
                                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                                print(f"[RX {timestamp}] Windows → Linux: {line}")
                    
                    time.sleep(0.01)
                    
        except serial.SerialException as e:
            print(f"❌ 受信エラー ({device}): {e}")
        except Exception as e:
            print(f"❌ 予期しない受信エラー: {e}")
        finally:
            print(f"📥 受信監視終了 ({device})")
    
    def bidirectional_test(self):
        """双方向通信テスト"""
        print("🔄 双方向通信テスト開始")
        print("📤 /dev/ttyS1 → Windows送信")
        print("📥 /dev/ttyS0 ← Windows受信")
        print("Ctrl+Cで停止")
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
        """手動通信モード"""
        print("💬 手動通信モード")
        print("📤 送信: /dev/ttyS1 → Windows")
        print("📥 受信: /dev/ttyS0 ← Windows")
        print("メッセージ入力で送信、'quit'で終了")
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
        """性能テスト"""
        print("⚡ 性能テスト開始")
        device = '/dev/ttyS1'
        duration = 30
        
        try:
            with serial.Serial(device, 9600, timeout=1) as ser:
                start_time = time.time()
                bytes_sent = 0
                packets_sent = 0
                
                print(f"📊 {duration}秒間の性能測定...")
                
                while time.time() - start_time < duration:
                    test_data = f"PERF_{packets_sent:06d}_" + "L" * 80 + "\r\n"
                    ser.write(test_data.encode('utf-8'))
                    
                    bytes_sent += len(test_data)
                    packets_sent += 1
                    
                    if packets_sent % 50 == 0:
                        elapsed = time.time() - start_time
                        bps = bytes_sent / elapsed if elapsed > 0 else 0
                        print(f"📈 進行: {packets_sent} packets, {bps:.1f} bytes/sec")
                    
                    time.sleep(0.02)  # 50Hz
                
                # 結果
                elapsed = time.time() - start_time
                print(f"\n📊 性能テスト結果:")
                print(f"  送信パケット: {packets_sent:,}")
                print(f"  送信バイト: {bytes_sent:,}")
                print(f"  実測時間: {elapsed:.2f}秒")
                print(f"  平均スループット: {bytes_sent/elapsed:.1f} bytes/sec")
                print(f"  理論値 (9600baud): {9600/10:.1f} bytes/sec")
                print(f"  効率: {(bytes_sent/elapsed)/(9600/10)*100:.1f}%")
                
        except Exception as e:
            print(f"❌ 性能テストエラー: {e}")
    
    def stop_all(self):
        """全通信停止"""
        self.running = False
        
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        print("✅ 全通信停止完了")

def main():
    """メイン実行"""
    comm = LinuxSerialComm()
    
    print("=== Linux Serial Communication Tool (Enhanced) ===")
    print("🐧 VMware Guest - デュアルパイプ対応")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    
    # 初期チェック
    if not comm.check_serial_devices():
        print("\n❌ シリアルデバイス準備未完了")
        print("上記の対処方法を実行してから再度お試しください")
        return
    
    try:
        while True:
            print("\n🎛️ メニュー:")
            print("1. デバイス状態確認")
            print("2. Linux→Windows送信テスト")
            print("3. Windows→Linux受信監視")
            print("4. 双方向通信テスト")
            print("5. 手動通信モード")
            print("6. 性能テスト")
            print("7. VMware設定ガイド")
            print("8. 終了")
            
            choice = input("\n選択してください (1-8): ").strip()
            
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
                print("\n=== VMware設定ガイド ===")
                print("【必要な設定】")
                print("シリアルポート1:")
                print("  パイプ名: \\\\.\\\pipe\\\\win_to_linux")
                print("  用途: Windows→Linux (/dev/ttyS0)")
                print()
                print("シリアルポート2:")
                print("  パイプ名: \\\\.\\\pipe\\\\linux_to_win")
                print("  用途: Linux→Windows (/dev/ttyS1)")
                print()
                print("【Linux側権限設定】")
                print("sudo usermod -a -G dialout $USER && logout")
                print("または")
                print("sudo chmod 666 /dev/ttyS*")
            
            elif choice == "8":
                print("👋 終了します")
                break
            
            else:
                print("❌ 1-8を選択してください")
                
    except KeyboardInterrupt:
        print("\n👋 終了します")
    finally:
        comm.stop_all()

if __name__ == "__main__":
    main()
