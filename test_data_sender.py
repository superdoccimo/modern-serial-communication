#!/usr/bin/env python3
"""
テストデータ送信スクリプト
COM2からCOM1へ定期的にデータを送信してダッシュボードの動作確認
"""

import serial
import time
import random
import json
from datetime import datetime

def send_test_data():
    """テストデータ送信"""
    try:
        print("COM2からテストデータを送信します...")
        print("Ctrl+Cで停止")
        
        with serial.Serial('COM2', 9600, timeout=1) as ser:
            counter = 1
            
            while True:
                # 様々なパターンのテストデータ
                test_patterns = [
                    f"SENSOR,{counter},{random.randint(20, 30)}.{random.randint(0, 99):02d},TEMP",
                    f"STATUS,{counter},OK,{datetime.now().strftime('%H:%M:%S')}",
                    f"DATA,{counter},{random.randint(0, 1023)},ADC_CH1",
                    f"HEARTBEAT,{counter},ALIVE",
                    f"ERROR,{counter},NONE,ALL_SYSTEMS_NORMAL",
                    json.dumps({
                        "id": counter,
                        "timestamp": datetime.now().isoformat(),
                        "sensors": {
                            "temperature": random.randint(20, 30),
                            "humidity": random.randint(40, 60),
                            "pressure": random.randint(1000, 1020)
                        }
                    })
                ]
                
                # ランダムにパターン選択
                message = random.choice(test_patterns) + "\r\n"
                
                # 送信
                ser.write(message.encode('utf-8'))
                print(f"[{counter:03d}] Sent: {message.strip()}")
                
                counter += 1
                
                # 1-3秒のランダム間隔
                time.sleep(random.uniform(1.0, 3.0))
                
    except KeyboardInterrupt:
        print("\n送信を停止しました")
    except serial.SerialException as e:
        print(f"シリアルポートエラー: {e}")
        print("COM2が利用できることを確認してください")
    except Exception as e:
        print(f"エラー: {e}")

def send_bulk_data():
    """大量データ送信テスト"""
    try:
        print("大量データ送信テスト開始...")
        
        with serial.Serial('COM2', 9600, timeout=1) as ser:
            for i in range(100):
                message = f"BULK_TEST,{i+1:03d},{'A' * random.randint(10, 50)}\r\n"
                ser.write(message.encode('utf-8'))
                print(f"Bulk [{i+1:03d}/100]: {len(message)} bytes")
                time.sleep(0.1)  # 高速送信
                
        print("大量データ送信完了")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    print("=== Serial Communication Test ===")
    print("1. 通常テスト（ランダムデータ）")
    print("2. 大量データテスト")
    print("3. 終了")
    
    while True:
        try:
            choice = input("\n選択してください (1-3): ").strip()
            
            if choice == "1":
                send_test_data()
            elif choice == "2":
                send_bulk_data()
            elif choice == "3":
                print("終了します")
                break
            else:
                print("1-3を選択してください")
                
        except KeyboardInterrupt:
            print("\n終了します")
            break