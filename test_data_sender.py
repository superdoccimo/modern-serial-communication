#!/usr/bin/env python3
"""
クロスプラットフォーム対応シリアル通信テストツール
Windows/Linux/macOS対応、ポート選択可能
"""

import serial
import serial.tools.list_ports
import time
import random
import json
import platform
import threading
from datetime import datetime

class SerialTester:
    def __init__(self):
        self.is_running = False
        self.send_thread = None
        
    def list_available_ports(self):
        """利用可能なシリアルポートを一覧表示"""
        ports = serial.tools.list_ports.comports()
        
        print("\n=== 利用可能なシリアルポート ===")
        if not ports:
            print("シリアルポートが見つかりません")
            return []
        
        for i, port in enumerate(ports, 1):
            print(f"{i}. {port.device}")
            print(f"   説明: {port.description}")
            print(f"   ハードウェアID: {port.hwid}")
            print()
        
        return ports
    
    def select_port(self, ports, prompt="ポートを選択してください"):
        """ポート選択UI"""
        while True:
            try:
                choice = input(f"{prompt} (1-{len(ports)}, 0で戻る): ").strip()
                
                if choice == "0":
                    return None
                
                port_index = int(choice) - 1
                if 0 <= port_index < len(ports):
                    return ports[port_index].device
                else:
                    print(f"1-{len(ports)}の範囲で選択してください")
                    
            except ValueError:
                print("数字を入力してください")
            except KeyboardInterrupt:
                return None
    
    def get_baudrate(self):
        """ボーレート選択"""
        common_rates = [9600, 19200, 38400, 57600, 115200]
        
        print("\n=== ボーレート選択 ===")
        for i, rate in enumerate(common_rates, 1):
            print(f"{i}. {rate}")
        print("6. カスタム")
        
        while True:
            try:
                choice = input("選択してください (1-6): ").strip()
                
                if choice in ['1', '2', '3', '4', '5']:
                    return common_rates[int(choice) - 1]
                elif choice == '6':
                    custom_rate = int(input("ボーレートを入力: "))
                    return custom_rate
                else:
                    print("1-6を選択してください")
                    
            except ValueError:
                print("有効な数字を入力してください")
            except KeyboardInterrupt:
                return 9600
    
    def send_test_data(self, port, baudrate):
        """テストデータ送信"""
        self.is_running = True
        counter = 1
        
        try:
            print(f"\n{port}からテストデータを送信開始...")
            print("Ctrl+Cで停止")
            
            with serial.Serial(port, baudrate, timeout=1) as ser:
                while self.is_running:
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
                    
        except serial.SerialException as e:
            print(f"シリアルポートエラー: {e}")
        except Exception as e:
            print(f"エラー: {e}")
        finally:
            self.is_running = False
    
    def receive_data(self, port, baudrate):
        """データ受信モニター"""
        try:
            print(f"\n{port}でデータ受信開始...")
            print("Ctrl+Cで停止")
            
            with serial.Serial(port, baudrate, timeout=1) as ser:
                while True:
                    if ser.in_waiting > 0:
                        data = ser.readline().decode('utf-8', errors='ignore').strip()
                        if data:
                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            print(f"[{timestamp}] Received: {data}")
                    time.sleep(0.01)
                    
        except KeyboardInterrupt:
            print("\n受信を停止しました")
        except serial.SerialException as e:
            print(f"シリアルポートエラー: {e}")
        except Exception as e:
            print(f"エラー: {e}")
    
    def send_bulk_data(self, port, baudrate):
        """大量データ送信テスト"""
        try:
            print(f"\n{port}で大量データ送信テスト開始...")
            
            with serial.Serial(port, baudrate, timeout=1) as ser:
                for i in range(100):
                    message = f"BULK_TEST,{i+1:03d},{'A' * random.randint(10, 50)}\r\n"
                    ser.write(message.encode('utf-8'))
                    print(f"Bulk [{i+1:03d}/100]: {len(message)} bytes")
                    time.sleep(0.1)  # 高速送信
                    
            print("大量データ送信完了")
            
        except Exception as e:
            print(f"エラー: {e}")
    
    def bidirectional_test(self, send_port, receive_port, baudrate):
        """送受信同時テスト"""
        print(f"\n双方向テスト開始:")
        print(f"送信: {send_port}")
        print(f"受信: {receive_port}")
        print("Ctrl+Cで停止")
        
        # 受信スレッド開始
        receive_thread = threading.Thread(
            target=self.receive_data, 
            args=(receive_port, baudrate)
        )
        receive_thread.daemon = True
        receive_thread.start()
        
        # 少し待ってから送信開始
        time.sleep(1)
        self.send_test_data(send_port, baudrate)
    
    def create_virtual_ports(self):
        """仮想ポート作成ガイド"""
        system = platform.system()
        
        print("\n=== 仮想ポート作成方法 ===")
        
        if system == "Windows":
            print("Windows用:")
            print("1. com0com (無料)")
            print("   - https://sourceforge.net/projects/com0com/")
            print("   - COM1-COM2のペアを作成可能")
            print("2. Virtual Serial Port Driver (有料)")
            print("   - Eltima Software製")
            print("\n使用例:")
            print("   COM1 → COM2 に送信")
            
        elif system == "Linux":
            print("Linux用:")
            print("1. socat コマンド:")
            print("   sudo socat -d -d pty,raw,echo=0 pty,raw,echo=0")
            print("2. 出力例:")
            print("   2024/06/08 10:30:00 socat[1234] N PTY is /dev/pts/2")
            print("   2024/06/08 10:30:00 socat[1234] N PTY is /dev/pts/3")
            print("3. 別ターミナルで以下実行:")
            print("   sudo chmod 666 /dev/pts/2 /dev/pts/3")
            print("\n使用例:")
            print("   /dev/pts/2 → /dev/pts/3 に送信")
            print("\n実際のシリアルデバイス例:")
            print("   /dev/ttyUSB0 → /dev/ttyUSB1")
            print("   /dev/ttyACM0 → /dev/ttyACM1")
            
        elif system == "Darwin":  # macOS
            print("macOS用:")
            print("1. socat コマンド (Homebrewでインストール):")
            print("   brew install socat")
            print("   socat -d -d pty,raw,echo=0 pty,raw,echo=0")
            print("2. 出力されたデバイス名を使用")
            print("\n使用例:")
            print("   /dev/ttys002 → /dev/ttys003 に送信")
            
        print("\n=== ネットワーク経由での送信 ===")
        print("Linuxマシンへの送信:")
        print("1. 受信側Linux: nc -l -p 12345 > received_data.txt")
        print("2. 送信側: このツールで TCP/Serial変換")
        print("3. または直接 netcat/socat でポート転送")
        
        print("\n仮想ポートを作成後、このプログラムで送受信テストができます")
    
    def run(self):
        """メインメニュー"""
        while True:
            print(f"\n=== シリアル通信テストツール ===")
            print(f"OS: {platform.system()}")
            print("1. 利用可能ポート一覧")
            print("2. データ送信テスト")
            print("3. データ受信テスト")
            print("4. 大量データ送信テスト")
            print("5. 双方向テスト（送信+受信）")
            print("6. 仮想ポート作成ガイド")
            print("7. 終了")
            
            try:
                choice = input("\n選択してください (1-7): ").strip()
                
                if choice == "1":
                    self.list_available_ports()
                
                elif choice == "2":
                    ports = self.list_available_ports()
                    if ports:
                        send_port = self.select_port(ports, "送信ポートを選択")
                        if send_port:
                            baudrate = self.get_baudrate()
                            self.send_test_data(send_port, baudrate)
                
                elif choice == "3":
                    ports = self.list_available_ports()
                    if ports:
                        receive_port = self.select_port(ports, "受信ポートを選択")
                        if receive_port:
                            baudrate = self.get_baudrate()
                            self.receive_data(receive_port, baudrate)
                
                elif choice == "4":
                    ports = self.list_available_ports()
                    if ports:
                        send_port = self.select_port(ports, "送信ポートを選択")
                        if send_port:
                            baudrate = self.get_baudrate()
                            self.send_bulk_data(send_port, baudrate)
                
                elif choice == "5":
                    ports = self.list_available_ports()
                    if ports and len(ports) >= 2:
                        print("\n2つのポートを選択してください")
                        send_port = self.select_port(ports, "送信ポートを選択")
                        if send_port:
                            receive_port = self.select_port(ports, "受信ポートを選択")
                            if receive_port and receive_port != send_port:
                                baudrate = self.get_baudrate()
                                self.bidirectional_test(send_port, receive_port, baudrate)
                            else:
                                print("異なるポートを選択してください")
                    else:
                        print("双方向テストには2つ以上のポートが必要です")
                
                elif choice == "6":
                    self.create_virtual_ports()
                
                elif choice == "7":
                    print("終了します")
                    break
                
                else:
                    print("1-7を選択してください")
                    
            except KeyboardInterrupt:
                print("\n\n終了します")
                self.is_running = False
                break

if __name__ == "__main__":
    tester = SerialTester()
    tester.run()