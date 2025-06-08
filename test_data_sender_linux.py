#!/usr/bin/env python3
"""
Linux用テストデータ送信スクリプト
/dev/ttyS0から/dev/ttyS1へ定期的にデータを送信してダッシュボードの動作確認
"""

import serial
import time
import random
import json
import os
import sys
from datetime import datetime

def check_permissions():
    """権限確認"""
    devices = ['/dev/ttyS0', '/dev/ttyS1']
    
    print("🔍 デバイス権限確認:")
    for device in devices:
        if os.path.exists(device):
            readable = os.access(device, os.R_OK)
            writable = os.access(device, os.W_OK)
            print(f"  {device}: 読み取り={readable}, 書き込み={writable}")
            
            if not (readable and writable):
                print(f"  ⚠️ {device} にアクセス権限がありません")
                print("  解決方法: sudo usermod -a -G dialout $USER && logout")
                return False
        else:
            print(f"  ❌ {device} が存在しません")
            return False
    
    print("  ✅ 全デバイスにアクセス可能")
    return True

def send_test_data(sender_port='/dev/ttyS0', description="ttyS0から送信"):
    """テストデータ送信"""
    try:
        print(f"📡 {description}...")
        print("Ctrl+Cで停止")
        
        with serial.Serial(sender_port, 9600, timeout=1) as ser:
            counter = 1
            
            while True:
                # 様々なパターンのテストデータ
                test_patterns = [
                    f"LINUX_SENSOR,{counter},{random.randint(20, 30)}.{random.randint(0, 99):02d},TEMP_C",
                    f"LINUX_STATUS,{counter},OK,{datetime.now().strftime('%H:%M:%S')}",
                    f"LINUX_DATA,{counter},{random.randint(0, 1023)},GPIO_PIN_{random.randint(1, 8)}",
                    f"LINUX_HEARTBEAT,{counter},ALIVE,{sender_port}",
                    f"SYSTEM_INFO,{counter},NONE,UBUNTU_RUNNING",
                    f"CPU_TEMP,{counter},{random.randint(45, 65)}.{random.randint(0, 99):02d},CELSIUS",
                    f"MEMORY_USAGE,{counter},{random.randint(30, 80)},PERCENT",
                    f"DISK_USAGE,{counter},{random.randint(20, 90)},PERCENT",
                    json.dumps({
                        "id": counter,
                        "timestamp": datetime.now().isoformat(),
                        "host": "linux_guest",
                        "sensors": {
                            "cpu_temp": random.randint(45, 65),
                            "memory_usage": random.randint(30, 80),
                            "disk_usage": random.randint(20, 90),
                            "load_avg": round(random.uniform(0.1, 2.0), 2)
                        },
                        "network": {
                            "interface": "ens33",
                            "rx_bytes": random.randint(1000000, 9999999),
                            "tx_bytes": random.randint(500000, 5000000)
                        }
                    })
                ]
                
                # ランダムにパターン選択
                message = random.choice(test_patterns) + "\r\n"
                
                # 送信
                ser.write(message.encode('utf-8'))
                print(f"[{counter:03d}] 📤 Sent via {sender_port}: {message.strip()}")
                
                counter += 1
                
                # 1-3秒のランダム間隔
                time.sleep(random.uniform(1.0, 3.0))
                
    except KeyboardInterrupt:
        print(f"\n✅ {sender_port}からの送信を停止しました")
    except serial.SerialException as e:
        print(f"❌ シリアルポートエラー: {e}")
        print(f"💡 {sender_port}が利用できることを確認してください")
        print("💡 権限エラーの場合: sudo usermod -a -G dialout $USER && logout")
    except Exception as e:
        print(f"❌ エラー: {e}")

def send_bulk_data(sender_port='/dev/ttyS0'):
    """大量データ送信テスト"""
    try:
        print(f"📦 大量データ送信テスト開始 ({sender_port})...")
        
        with serial.Serial(sender_port, 9600, timeout=1) as ser:
            for i in range(100):
                message = f"LINUX_BULK_TEST,{i+1:03d},{'L' * random.randint(10, 50)},{sender_port}\r\n"
                ser.write(message.encode('utf-8'))
                print(f"Bulk [{i+1:03d}/100]: {len(message)} bytes via {sender_port}")
                time.sleep(0.1)  # 高速送信
                
        print("✅ 大量データ送信完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def send_bidirectional_test():
    """双方向通信テスト"""
    print("🔄 双方向通信テスト開始...")
    print("両方のポートから交互にデータを送信します")
    
    try:
        with serial.Serial('/dev/ttyS0', 9600, timeout=1) as ser0, \
             serial.Serial('/dev/ttyS1', 9600, timeout=1) as ser1:
            
            for i in range(20):
                # ttyS0からの送信
                msg0 = f"FROM_TTYS0,{i+1:02d},Hello_from_ttyS0,{datetime.now().strftime('%H:%M:%S')}\r\n"
                ser0.write(msg0.encode('utf-8'))
                print(f"📤 ttyS0 → Windows: {msg0.strip()}")
                time.sleep(1)
                
                # ttyS1からの送信
                msg1 = f"FROM_TTYS1,{i+1:02d},Hello_from_ttyS1,{datetime.now().strftime('%H:%M:%S')}\r\n"
                ser1.write(msg1.encode('utf-8'))
                print(f"📤 ttyS1 → Windows: {msg1.strip()}")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n✅ 双方向テストを停止しました")
    except Exception as e:
        print(f"❌ 双方向テストエラー: {e}")

def interactive_sender():
    """対話的送信モード"""
    print("💬 対話的送信モード")
    print("メッセージを入力してEnter（'quit'で終了）")
    
    port = input("送信ポート (/dev/ttyS0 または /dev/ttyS1): ").strip() or '/dev/ttyS0'
    
    try:
        with serial.Serial(port, 9600, timeout=1) as ser:
            counter = 1
            while True:
                message = input(f"[{counter:03d}] メッセージ: ").strip()
                
                if message.lower() == 'quit':
                    break
                
                if message:
                    full_message = f"MANUAL,{counter:03d},{message},{datetime.now().strftime('%H:%M:%S')}\r\n"
                    ser.write(full_message.encode('utf-8'))
                    print(f"✅ 送信完了 via {port}: {full_message.strip()}")
                    counter += 1
                
    except KeyboardInterrupt:
        print("\n✅ 対話的送信を終了しました")
    except Exception as e:
        print(f"❌ エラー: {e}")

def main():
    """メイン関数"""
    print("=== Linux Serial Communication Test ===")
    print("🐧 Ubuntu VMware Guest Environment")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 権限確認
    if not check_permissions():
        print("\n❌ デバイスアクセス権限が不足しています")
        print("以下のコマンドを実行してから再度お試しください:")
        print("sudo usermod -a -G dialout $USER")
        print("logout")
        return
    
    # デバイス情報表示
    print("\n📋 利用可能デバイス:")
    for device in ['/dev/ttyS0', '/dev/ttyS1']:
        if os.path.exists(device):
            try:
                stat_info = os.stat(device)
                print(f"  {device}: 権限={oct(stat_info.st_mode)[-3:]}")
            except Exception as e:
                print(f"  {device}: エラー={e}")
    
    while True:
        print("\n🎛️ テストメニュー:")
        print("1. ttyS0からテストデータ送信（Windows側で受信）")
        print("2. ttyS1からテストデータ送信（Windows側で受信）")
        print("3. 大量データテスト (ttyS0)")
        print("4. 大量データテスト (ttyS1)")
        print("5. 双方向通信テスト")
        print("6. 対話的送信モード")
        print("7. デバイス再確認")
        print("8. 終了")
        
        try:
            choice = input("\n選択してください (1-8): ").strip()
            
            if choice == "1":
                send_test_data('/dev/ttyS0', "ttyS0からWindows側へデータ送信")
            elif choice == "2":
                send_test_data('/dev/ttyS1', "ttyS1からWindows側へデータ送信")
            elif choice == "3":
                send_bulk_data('/dev/ttyS0')
            elif choice == "4":
                send_bulk_data('/dev/ttyS1')
            elif choice == "5":
                send_bidirectional_test()
            elif choice == "6":
                interactive_sender()
            elif choice == "7":
                check_permissions()
            elif choice == "8":
                print("👋 終了します")
                break
            else:
                print("❌ 1-8を選択してください")
                
        except KeyboardInterrupt:
            print("\n👋 終了します")
            break
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")

if __name__ == "__main__":
    main()