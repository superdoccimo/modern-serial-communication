#!/usr/bin/env python3
"""
VMware仮想シリアルポート診断・設定ツール
WindowsホストからLinuxゲスト間のシリアル通信確認
"""

import serial
import serial.tools.list_ports
import subprocess
import platform
import time
import os
import socket
from datetime import datetime

class VMwareSerialDiagnostic:
    def __init__(self):
        self.system = platform.system()
    
    def check_system_info(self):
        """システム情報確認"""
        print("=== システム情報 ===")
        print(f"OS: {platform.system()} {platform.release()}")
        print(f"アーキテクチャ: {platform.machine()}")
        
        if self.system == "Linux":
            # VMware Toolsチェック
            try:
                result = subprocess.run(['vmware-toolbox-cmd', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"VMware Tools: {result.stdout.strip()}")
                else:
                    print("VMware Tools: インストールされていません")
            except FileNotFoundError:
                print("VMware Tools: インストールされていません")
            
            # カーネルモジュール確認
            try:
                with open('/proc/modules', 'r') as f:
                    modules = f.read()
                    if 'vmw_' in modules:
                        print("VMware カーネルモジュール: 検出済み")
                    else:
                        print("VMware カーネルモジュール: 未検出")
            except:
                pass
        
        print()
    
    def list_serial_devices(self):
        """シリアルデバイス一覧"""
        print("=== シリアルデバイス一覧 ===")
        
        if self.system == "Linux":
            # /dev/ttyS* の確認
            serial_devices = []
            for i in range(10):
                device = f"/dev/ttyS{i}"
                if os.path.exists(device):
                    serial_devices.append(device)
            
            print("標準シリアルデバイス:")
            for device in serial_devices:
                try:
                    stat = os.stat(device)
                    print(f"  {device} (権限: {oct(stat.st_mode)[-3:]})")
                except:
                    print(f"  {device} (アクセス不可)")
            
            # /dev/ttyUSB*, /dev/ttyACM* の確認
            usb_devices = []
            for prefix in ['/dev/ttyUSB', '/dev/ttyACM']:
                for i in range(10):
                    device = f"{prefix}{i}"
                    if os.path.exists(device):
                        usb_devices.append(device)
            
            if usb_devices:
                print("USBシリアルデバイス:")
                for device in usb_devices:
                    print(f"  {device}")
            else:
                print("USBシリアルデバイス: なし")
        
        # pyserialでの検出
        print("\npyserial検出デバイス:")
        ports = serial.tools.list_ports.comports()
        if ports:
            for port in ports:
                print(f"  {port.device}: {port.description}")
        else:
            print("  検出されませんでした")
        
        print()
    
    def test_serial_access(self, device_path):
        """シリアルデバイスアクセステスト"""
        print(f"=== {device_path} アクセステスト ===")
        
        try:
            # 基本的な開閉テスト
            with serial.Serial(device_path, 9600, timeout=1) as ser:
                print(f"✓ デバイス開封成功")
                print(f"  ポート: {ser.port}")
                print(f"  ボーレート: {ser.baudrate}")
                print(f"  タイムアウト: {ser.timeout}")
                
                # 簡単な読み書きテスト
                try:
                    ser.write(b"TEST\r\n")
                    print("✓ 書き込みテスト成功")
                    
                    # 少し待って読み取り試行
                    time.sleep(0.1)
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting)
                        print(f"✓ データ受信: {data}")
                    else:
                        print("- データ受信なし（正常）")
                        
                except Exception as e:
                    print(f"✗ 読み書きエラー: {e}")
                    
        except serial.SerialException as e:
            print(f"✗ シリアルポートエラー: {e}")
        except PermissionError:
            print(f"✗ 権限エラー: {device_path}にアクセス権限がありません")
            if self.system == "Linux":
                print(f"  解決方法: sudo chmod 666 {device_path}")
                print(f"  または: sudo usermod -a -G dialout $USER")
        except Exception as e:
            print(f"✗ 予期しないエラー: {e}")
        
        print()
    
    def check_vmware_config(self):
        """VMware設定確認ガイド"""
        print("=== VMware仮想シリアルポート設定ガイド ===")
        
        if self.system == "Windows":
            print("Windowsホスト側設定:")
            print("1. VMware Workstation/Player設定")
            print("   - VM設定 → ハードウェア追加 → シリアルポート")
            print("   - 接続先: 名前付きパイプを使用")
            print("   - パイプ名: \\.\pipe\com_1 (例)")
            print("   - パイプの端: サーバー")
            print("   - I/O モード: アプリケーション")
            print()
            print("2. Windows仮想COMポート作成")
            print("   - com0com等で仮想ポートペア作成")
            print("   - 例: COM1 ↔ COM2")
            print()
            
        elif self.system == "Linux":
            print("Linuxゲスト側確認:")
            print("1. VMware設定確認")
            print("   - シリアルポートが追加されているか")
            print("   - 通常 /dev/ttyS0 として認識される")
            print()
            print("2. 権限設定")
            print("   sudo chmod 666 /dev/ttyS0")
            print("   または")
            print("   sudo usermod -a -G dialout $USER")
            print("   (再ログインが必要)")
            print()
            print("3. VMware Tools確認")
            print("   - VMware Toolsがインストール済みか確認")
            print("   - 一部のドライバーが必要な場合があります")
            print()
        
        print("=== 代替案 ===")
        print("1. TCP/IPソケット通信")
        print("   - より確実で設定が簡単")
        print("   - ネットワーク経由でのデータ転送")
        print()
        print("2. 共有フォルダー経由")
        print("   - ファイルベースでのデータ交換")
        print("   - リアルタイム性は劣るが確実")
        print()
        print("3. SSH/SCP")
        print("   - セキュアな通信")
        print("   - 標準的なLinux機能")
        print()
    
    def network_alternative_test(self):
        """ネットワーク代替案テスト"""
        print("=== ネットワーク通信テスト ===")
        
        if self.system == "Linux":
            print("Linux側でのテストサーバー起動:")
            print("1. Python3サーバー:")
            print("   python3 -c \"")
            print("import socket, datetime")
            print("s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)")
            print("s.bind(('0.0.0.0', 12345))")
            print("s.listen(1)")
            print("print('待機中...')")
            print("c, a = s.accept()")
            print("while True:")
            print("    data = c.recv(1024)")
            print("    if not data: break")
            print("    print(f'{datetime.datetime.now()}: {data.decode()}')\"")
            print()
            print("2. netcat使用:")
            print("   nc -l -p 12345")
            print()
            
        elif self.system == "Windows":
            print("Windows側からのテスト送信:")
            print("PowerShellコマンド例:")
            print('$client = New-Object System.Net.Sockets.TcpClient')
            print('$client.Connect("192.168.xxx.xxx", 12345)')
            print('$stream = $client.GetStream()')
            print('$data = [System.Text.Encoding]::UTF8.GetBytes("Test message\\n")')
            print('$stream.Write($data, 0, $data.Length)')
            print('$client.Close()')
            print()
        
        # IP確認
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            print(f"現在のIPアドレス: {ip}")
        except:
            print("IPアドレス取得失敗")
    
    def run_diagnosis(self):
        """総合診断実行"""
        print("VMware仮想シリアルポート診断開始\n")
        
        self.check_system_info()
        self.list_serial_devices()
        
        # Linuxの場合、主要なデバイスをテスト
        if self.system == "Linux":
            test_devices = ["/dev/ttyS0", "/dev/ttyS1"]
            for device in test_devices:
                if os.path.exists(device):
                    self.test_serial_access(device)
        
        self.check_vmware_config()
        self.network_alternative_test()

def main():
    diagnostic = VMwareSerialDiagnostic()
    
    while True:
        print("\n=== VMware シリアルポート診断ツール ===")
        print("1. 総合診断実行")
        print("2. システム情報確認")
        print("3. シリアルデバイス一覧")
        print("4. デバイステスト（手動指定）")
        print("5. VMware設定ガイド")
        print("6. ネットワーク代替案")
        print("7. 終了")
        
        choice = input("\n選択してください (1-7): ").strip()
        
        if choice == "1":
            diagnostic.run_diagnosis()
        
        elif choice == "2":
            diagnostic.check_system_info()
        
        elif choice == "3":
            diagnostic.list_serial_devices()
        
        elif choice == "4":
            device = input("テストするデバイスパス: ").strip()
            if device:
                diagnostic.test_serial_access(device)
        
        elif choice == "5":
            diagnostic.check_vmware_config()
        
        elif choice == "6":
            diagnostic.network_alternative_test()
        
        elif choice == "7":
            break
        
        else:
            print("1-7を選択してください")

if __name__ == "__main__":
    main()