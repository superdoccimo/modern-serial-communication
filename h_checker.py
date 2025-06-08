#!/usr/bin/env python3
"""
汎用シリアル通信テストツール
実機同士、VirtualBox、VMware（名前付きパイプ）対応
"""

import serial
import serial.tools.list_ports
import platform
import time
import json
import threading
import os
from datetime import datetime

class UniversalSerialTester:
    def __init__(self):
        self.system = platform.system()
        self.running = False
        
    def detect_environment(self):
        """実行環境の自動検出"""
        env_info = {
            "system": self.system,
            "virtual": False,
            "vm_type": None,
            "recommended_method": None
        }
        
        if self.system == "Linux":
            # 仮想環境検出
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()
                    
                if 'vmware' in cpuinfo:
                    env_info["virtual"] = True
                    env_info["vm_type"] = "VMware"
                    env_info["recommended_method"] = "名前付きパイプ または TCP/IP"
                elif 'virtualbox' in cpuinfo:
                    env_info["virtual"] = True  
                    env_info["vm_type"] = "VirtualBox"
                    env_info["recommended_method"] = "仮想シリアルポート"
                else:
                    env_info["recommended_method"] = "物理シリアルポート"
                    
            except:
                pass
                
        elif self.system == "Windows":
            # Windows環境チェック
            try:
                import subprocess
                result = subprocess.run(['systeminfo'], capture_output=True, text=True)
                if 'VMware' in result.stdout:
                    env_info["virtual"] = True
                    env_info["vm_type"] = "VMware Host"
                    env_info["recommended_method"] = "名前付きパイプ"
                elif 'VirtualBox' in result.stdout:
                    env_info["virtual"] = True
                    env_info["vm_type"] = "VirtualBox Host"
                    env_info["recommended_method"] = "COM-COMブリッジ"
                else:
                    env_info["recommended_method"] = "物理シリアルポート"
            except:
                pass
        
        return env_info
    
    def show_environment_guide(self):
        """環境別設定ガイド表示"""
        env = self.detect_environment()
        
        print("=== 実行環境情報 ===")
        print(f"OS: {env['system']}")
        print(f"仮想環境: {'Yes' if env['virtual'] else 'No'}")
        if env['vm_type']:
            print(f"VM種類: {env['vm_type']}")
        print(f"推奨方法: {env['recommended_method']}")
        print()
        
        # 環境別詳細ガイド
        if env['vm_type'] == "VMware":
            print("🔧 VMware設定ガイド:")
            print("1. VM設定 → シリアルポート追加")
            print("2. 接続方法: 名前付きパイプを使用")
            print("3. パイプ名: \\\\.\\pipe\\vmware_serial")
            print("4. パイプの端: サーバー")
            print("5. I/Oモード: アプリケーション")
            
        elif env['vm_type'] == "VirtualBox":
            print("🔧 VirtualBox設定ガイド:")
            print("1. VM設定 → シリアルポート")
            print("2. ポート1有効化")
            print("3. ポートモード: ホストパイプ")
            print("4. パス/アドレス: \\\\.\\pipe\\vbox_serial")
            
        elif not env['virtual']:
            print("🔧 物理環境設定ガイド:")
            print("1. USBシリアル変換器を使用")
            print("2. または RS232C ケーブル接続")
            print("3. 両端のボーレート設定を統一")
            
        print()
    
    def smart_port_detection(self):
        """インテリジェントポート検出"""
        ports = serial.tools.list_ports.comports()
        
        categorized_ports = {
            "physical": [],
            "virtual": [],
            "usb": [],
            "unknown": []
        }
        
        for port in ports:
            desc = port.description.lower()
            hwid = port.hwid.lower()
            
            if 'usb' in desc or 'usb' in hwid:
                categorized_ports["usb"].append(port)
            elif 'com0com' in desc or 'virtual' in desc:
                categorized_ports["virtual"].append(port)
            elif 'communications port' in desc:
                categorized_ports["physical"].append(port)
            else:
                categorized_ports["unknown"].append(port)
        
        print("=== インテリジェントポート検出結果 ===")
        
        for category, port_list in categorized_ports.items():
            if port_list:
                category_names = {
                    "physical": "物理シリアルポート",
                    "virtual": "仮想シリアルポート", 
                    "usb": "USBシリアル変換器",
                    "unknown": "その他"
                }
                
                print(f"\n📌 {category_names[category]}:")
                for i, port in enumerate(port_list, 1):
                    print(f"  {i}. {port.device}")
                    print(f"     説明: {port.description}")
                    if hasattr(port, 'manufacturer') and port.manufacturer:
                        print(f"     製造者: {port.manufacturer}")
        
        return categorized_ports
    
    def bidirectional_test_wizard(self):
        """双方向テストウィザード"""
        print("=== 双方向通信テストウィザード ===")
        
        categorized = self.smart_port_detection()
        all_ports = []
        for port_list in categorized.values():
            all_ports.extend(port_list)
        
        if len(all_ports) < 2:
            print("⚠️ 双方向テストには2つ以上のポートが必要です")
            print("💡 解決策:")
            print("1. com0com等で仮想ポートペア作成")
            print("2. USBシリアル変換器を2つ接続") 
            print("3. TCP/IPブリッジを使用")
            return
        
        print(f"\n利用可能ポート: {len(all_ports)}個")
        for i, port in enumerate(all_ports, 1):
            print(f"{i}. {port.device} - {port.description}")
        
        try:
            # 送信ポート選択
            tx_choice = int(input("\n送信ポート選択 (1-{}): ".format(len(all_ports)))) - 1
            tx_port = all_ports[tx_choice].device
            
            # 受信ポート選択
            rx_choice = int(input("受信ポート選択 (1-{}): ".format(len(all_ports)))) - 1
            rx_port = all_ports[rx_choice].device
            
            if tx_port == rx_port:
                print("❌ 異なるポートを選択してください")
                return
            
            # ボーレート設定
            baudrate = int(input("ボーレート (9600): ") or "9600")
            
            print(f"\n🔄 双方向テスト開始")
            print(f"送信: {tx_port}")
            print(f"受信: {rx_port}")
            print(f"ボーレート: {baudrate}")
            print("Ctrl+Cで停止")
            
            self.run_bidirectional_test(tx_port, rx_port, baudrate)
            
        except (ValueError, IndexError):
            print("❌ 無効な選択です")
        except KeyboardInterrupt:
            print("\n✅ テスト終了")
    
    def run_bidirectional_test(self, tx_port, rx_port, baudrate):
        """双方向テスト実行"""
        self.running = True
        
        # 受信スレッド開始
        rx_thread = threading.Thread(
            target=self.receive_monitor,
            args=(rx_port, baudrate)
        )
        rx_thread.daemon = True
        rx_thread.start()
        
        # 送信開始
        try:
            with serial.Serial(tx_port, baudrate, timeout=1) as ser:
                counter = 1
                while self.running:
                    # テストデータ作成
                    test_data = {
                        "id": counter,
                        "timestamp": datetime.now().isoformat(),
                        "tx_port": tx_port,
                        "message": f"Test_{counter:03d}"
                    }
                    
                    message = json.dumps(test_data) + "\r\n"
                    ser.write(message.encode('utf-8'))
                    
                    print(f"[TX {counter:03d}] {tx_port} → {rx_port}: {test_data['message']}")
                    counter += 1
                    
                    time.sleep(2)
                    
        except serial.SerialException as e:
            print(f"❌ 送信エラー: {e}")
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
    
    def receive_monitor(self, port, baudrate):
        """受信監視"""
        try:
            with serial.Serial(port, baudrate, timeout=1) as ser:
                buffer = ""
                while self.running:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        buffer += data
                        
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            if line:
                                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                                print(f"[RX {timestamp}] {port} ← {line}")
                    
                    time.sleep(0.01)
                    
        except serial.SerialException as e:
            print(f"❌ 受信エラー: {e}")
    
    def performance_test(self, port, baudrate=9600, duration=30):
        """性能テスト"""
        print(f"=== 性能テスト開始 ===")
        print(f"ポート: {port}")
        print(f"ボーレート: {baudrate}")
        print(f"テスト時間: {duration}秒")
        
        try:
            with serial.Serial(port, baudrate, timeout=1) as ser:
                start_time = time.time()
                bytes_sent = 0
                packets_sent = 0
                
                while time.time() - start_time < duration:
                    # 100バイトのテストデータ
                    test_data = f"PERF_TEST_{packets_sent:06d}_" + "X" * 80 + "\r\n"
                    ser.write(test_data.encode('utf-8'))
                    
                    bytes_sent += len(test_data)
                    packets_sent += 1
                    
                    if packets_sent % 100 == 0:
                        elapsed = time.time() - start_time
                        bps = bytes_sent / elapsed
                        print(f"進行状況: {packets_sent} packets, {bps:.1f} bytes/sec")
                    
                    time.sleep(0.01)  # 100Hz
                
                # 結果表示
                elapsed = time.time() - start_time
                print(f"\n=== 性能テスト結果 ===")
                print(f"送信パケット: {packets_sent}")
                print(f"送信バイト: {bytes_sent:,}")
                print(f"実測時間: {elapsed:.2f}秒")
                print(f"スループット: {bytes_sent/elapsed:.1f} bytes/sec")
                print(f"理論値: {baudrate/10:.1f} bytes/sec")
                print(f"効率: {(bytes_sent/elapsed)/(baudrate/10)*100:.1f}%")
                
        except Exception as e:
            print(f"❌ 性能テストエラー: {e}")
    
    def run(self):
        """メインメニュー"""
        while True:
            print("\n" + "="*50)
            print("🔧 汎用シリアル通信テストツール")
            print("="*50)
            
            print("1. 環境情報・設定ガイド")
            print("2. インテリジェントポート検出")  
            print("3. 双方向通信テストウィザード")
            print("4. 単方向送信テスト")
            print("5. 受信監視")
            print("6. 性能テスト")
            print("7. 終了")
            
            try:
                choice = input("\n選択してください (1-7): ").strip()
                
                if choice == "1":
                    self.show_environment_guide()
                
                elif choice == "2":
                    self.smart_port_detection()
                
                elif choice == "3":
                    self.bidirectional_test_wizard()
                
                elif choice == "4":
                    ports = list(serial.tools.list_ports.comports())
                    if ports:
                        print("\n利用可能ポート:")
                        for i, port in enumerate(ports, 1):
                            print(f"{i}. {port.device}")
                        
                        try:
                            port_choice = int(input("ポート選択: ")) - 1
                            if 0 <= port_choice < len(ports):
                                port = ports[port_choice].device
                                baudrate = int(input("ボーレート (9600): ") or "9600")
                                
                                # 単方向送信テスト
                                self.running = True
                                self.run_bidirectional_test(port, port, baudrate)
                        except:
                            print("❌ 無効な選択")
                
                elif choice == "5":
                    ports = list(serial.tools.list_ports.comports())
                    if ports:
                        print("\n利用可能ポート:")
                        for i, port in enumerate(ports, 1):
                            print(f"{i}. {port.device}")
                        
                        try:
                            port_choice = int(input("ポート選択: ")) - 1
                            if 0 <= port_choice < len(ports):
                                port = ports[port_choice].device
                                baudrate = int(input("ボーレート (9600): ") or "9600")
                                
                                print(f"受信監視開始: {port}")
                                print("Ctrl+Cで停止")
                                
                                self.running = True
                                self.receive_monitor(port, baudrate)
                        except KeyboardInterrupt:
                            self.running = False
                            print("\n受信監視停止")
                        except:
                            print("❌ 無効な選択")
                
                elif choice == "6":
                    ports = list(serial.tools.list_ports.comports())
                    if ports:
                        print("\n利用可能ポート:")
                        for i, port in enumerate(ports, 1):
                            print(f"{i}. {port.device}")
                        
                        try:
                            port_choice = int(input("ポート選択: ")) - 1
                            if 0 <= port_choice < len(ports):
                                port = ports[port_choice].device
                                baudrate = int(input("ボーレート (9600): ") or "9600")
                                duration = int(input("テスト時間[秒] (30): ") or "30")
                                
                                self.performance_test(port, baudrate, duration)
                        except:
                            print("❌ 無効な選択")
                
                elif choice == "7":
                    print("終了します")
                    break
                
                else:
                    print("❌ 1-7を選択してください")
                    
            except KeyboardInterrupt:
                print("\n\n終了します")
                self.running = False
                break

if __name__ == "__main__":
    tester = UniversalSerialTester()
    tester.run()