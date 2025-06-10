#!/usr/bin/env python3
"""
VMware環境用 TCP-シリアルブリッジ
WindowsホストとLinuxゲスト間でのシリアルデータ転送
仮想シリアルポートの代替案
"""

import socket
import serial
import threading
import time
import json
from datetime import datetime
import platform

class VMwareTCPSerialBridge:
    def __init__(self):
        self.running = False
        self.connections = []
    
    def windows_serial_to_tcp_server(self, serial_port="COM1", baudrate=9600, tcp_port=9999):
        """Windows側: シリアルポート → TCP サーバー"""
        print(f"=== Windows側 シリアル→TCP サーバー ===")
        print(f"シリアルポート: {serial_port} ({baudrate} baud)")
        print(f"TCPサーバーポート: {tcp_port}")
        print("Linux側からの接続を待機...")
        
        # TCPサーバー起動
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', tcp_port))
        server_socket.listen(5)
        
        self.running = True
        
        try:
            # シリアルポート開封
            with serial.Serial(serial_port, baudrate, timeout=1) as ser:
                print(f"シリアルポート {serial_port} 開封成功")
                
                while self.running:
                    try:
                        # 新しい接続を受け入れ
                        client_socket, addr = server_socket.accept()
                        print(f"Linux側接続: {addr}")
                        self.connections.append(client_socket)
                        
                        # 専用スレッドで処理
                        thread = threading.Thread(
                            target=self.handle_tcp_client,
                            args=(ser, client_socket, addr)
                        )
                        thread.daemon = True
                        thread.start()
                        
                    except socket.timeout:
                        continue
                    except OSError as e:
                        print(f"接続エラー: {e}")
                        
        except serial.SerialException as e:
            print(f"シリアルポートエラー: {e}")
        except OSError as e:
            print(f"エラー: {e}")
        finally:
            server_socket.close()
            print("サーバー終了")
    
    def handle_tcp_client(self, serial_port, client_socket, addr):
        """TCP クライアント処理"""
        try:
            while self.running:
                # シリアルからデータ読み取り
                if serial_port.in_waiting > 0:
                    data = serial_port.read(serial_port.in_waiting)
                    try:
                        client_socket.send(data)
                        print(f"転送 → {addr}: {len(data)} bytes")
                    except OSError:
                        break
                
                # TCPからデータ受信（双方向通信）
                client_socket.settimeout(0.1)
                try:
                    tcp_data = client_socket.recv(1024)
                    if tcp_data:
                        serial_port.write(tcp_data)
                        print(f"受信 ← {addr}: {len(tcp_data)} bytes")
                except socket.timeout:
                    pass
                except OSError:
                    break
                
                time.sleep(0.01)
                
        except (serial.SerialException, OSError) as e:
            print(f"クライアント処理エラー {addr}: {e}")
        finally:
            client_socket.close()
            if client_socket in self.connections:
                self.connections.remove(client_socket)
            print(f"クライアント切断: {addr}")
    
    def linux_tcp_to_serial_client(self, windows_ip, tcp_port=9999, serial_device="/dev/ttyS0", baudrate=9600):
        """Linux側: TCP クライアント → シリアルポート"""
        print(f"=== Linux側 TCP→シリアル クライアント ===")
        print(f"Windows接続先: {windows_ip}:{tcp_port}")
        print(f"シリアルデバイス: {serial_device} ({baudrate} baud)")
        
        try:
            # Windowsサーバーに接続
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((windows_ip, tcp_port))
            print("Windows側に接続成功")
            
            # シリアルポート開封
            with serial.Serial(serial_device, baudrate, timeout=1) as ser:
                print(f"シリアルデバイス {serial_device} 開封成功")
                
                self.running = True
                
                while self.running:
                    # TCPからデータ受信
                    tcp_socket.settimeout(0.1)
                    try:
                        tcp_data = tcp_socket.recv(1024)
                        if tcp_data:
                            ser.write(tcp_data)
                            print(f"TCP→シリアル: {len(tcp_data)} bytes")
                            print(f"データ: {tcp_data.decode('utf-8', errors='ignore').strip()}")
                        elif not tcp_data:
                            print("接続が閉じられました")
                            break
                    except socket.timeout:
                        pass
                    
                    # シリアルからデータ読み取り（双方向通信）
                    if ser.in_waiting > 0:
                        serial_data = ser.read(ser.in_waiting)
                        tcp_socket.send(serial_data)
                        print(f"シリアル→TCP: {len(serial_data)} bytes")
                    
                    time.sleep(0.01)
                    
        except ConnectionRefusedError:
            print(f"接続拒否: {windows_ip}:{tcp_port}")
            print("Windows側でサーバーが起動しているか確認してください")
        except serial.SerialException as e:
            print(f"シリアルデバイスエラー: {e}")
            print("デバイスの権限を確認してください: sudo chmod 666 /dev/ttyS0")
        except OSError as e:
            print(f"エラー: {e}")
        finally:
            tcp_socket.close()
            print("クライアント終了")
    
    def send_test_data_windows(self, serial_port="COM1", baudrate=9600):
        """Windows側: テストデータ送信"""
        print(f"=== Windows テストデータ送信 ===")
        print(f"シリアルポート: {serial_port}")
        
        try:
            with serial.Serial(serial_port, baudrate, timeout=1) as ser:
                counter = 1
                while True:
                    # テストメッセージ作成
                    test_data = {
                        "id": counter,
                        "timestamp": datetime.now().isoformat(),
                        "source": "Windows_Host",
                        "message": f"Test_Message_{counter:03d}"
                    }
                    
                    message = json.dumps(test_data) + "\r\n"
                    ser.write(message.encode('utf-8'))
                    
                    print(f"[{counter:03d}] 送信: {message.strip()}")
                    counter += 1
                    
                    time.sleep(2)
                    
        except KeyboardInterrupt:
            print("送信停止")
        except serial.SerialException as e:
            print(f"エラー: {e}")
    
    def monitor_serial_linux(self, serial_device="/dev/ttyS0", baudrate=9600):
        """Linux側: シリアルポート監視"""
        print(f"=== Linux シリアル監視 ===")
        print(f"デバイス: {serial_device}")
        
        try:
            with serial.Serial(serial_device, baudrate, timeout=1) as ser:
                print("データ監視開始... (Ctrl+Cで停止)")
                
                while True:
                    if ser.in_waiting > 0:
                        data = ser.readline().decode('utf-8', errors='ignore').strip()
                        if data:
                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            print(f"[{timestamp}] 受信: {data}")
                    
                    time.sleep(0.01)
                    
        except KeyboardInterrupt:
            print("監視停止")
        except serial.SerialException as e:
            print(f"エラー: {e}")
    
    def get_ip_info(self):
        """IP情報取得"""
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except OSError:
            return "取得失敗"

def main():
    bridge = VMwareTCPSerialBridge()
    system = platform.system()
    
    print(f"現在のOS: {system}")
    print(f"IPアドレス: {bridge.get_ip_info()}")
    
    while True:
        print(f"\n=== VMware TCP-シリアルブリッジ ({system}) ===")
        
        if system == "Windows":
            print("【Windows側メニュー】")
            print("1. シリアル→TCPサーバー起動")
            print("2. テストデータ送信（シリアル）")
            print("3. IP情報表示")
        else:
            print("【Linux側メニュー】")
            print("1. TCP→シリアルクライアント起動")
            print("2. シリアル監視")
            print("3. 権限設定ガイド")
        
        print("9. 設定ガイド")
        print("0. 終了")
        
        choice = input("\n選択してください: ").strip()
        
        if choice == "1":
            if system == "Windows":
                port = input("シリアルポート (COM1): ").strip() or "COM1"
                baudrate = int(input("ボーレート (9600): ").strip() or "9600")
                tcp_port = int(input("TCPポート (9999): ").strip() or "9999")
                
                try:
                    bridge.windows_serial_to_tcp_server(port, baudrate, tcp_port)
                except KeyboardInterrupt:
                    bridge.running = False
                    print("サーバー停止")
            else:
                windows_ip = input("Windows IP: ").strip()
                tcp_port = int(input("TCPポート (9999): ").strip() or "9999")
                device = input("シリアルデバイス (/dev/ttyS0): ").strip() or "/dev/ttyS0"
                baudrate = int(input("ボーレート (9600): ").strip() or "9600")
                
                try:
                    bridge.linux_tcp_to_serial_client(windows_ip, tcp_port, device, baudrate)
                except KeyboardInterrupt:
                    bridge.running = False
                    print("クライアント停止")
        
        elif choice == "2":
            if system == "Windows":
                port = input("シリアルポート (COM1): ").strip() or "COM1"
                baudrate = int(input("ボーレート (9600): ").strip() or "9600")
                bridge.send_test_data_windows(port, baudrate)
            else:
                device = input("シリアルデバイス (/dev/ttyS0): ").strip() or "/dev/ttyS0"
                baudrate = int(input("ボーレート (9600): ").strip() or "9600")
                bridge.monitor_serial_linux(device, baudrate)
        
        elif choice == "3":
            if system == "Windows":
                print(f"IPアドレス: {bridge.get_ip_info()}")
                print("このIPをLinux側で使用してください")
            else:
                print("=== Linux権限設定 ===")
                print("sudo chmod 666 /dev/ttyS0")
                print("または")
                print("sudo usermod -a -G dialout $USER")
                print("(再ログイン必要)")
        
        elif choice == "9":
            print("\n=== 設定ガイド ===")
            print("1. VMware設定:")
            print("   VM設定 → シリアルポート追加")
            print("   Linuxで /dev/ttyS0 として認識")
            print()
            print("2. 使用手順:")
            print("   ① Windows側: メニュー1でサーバー起動")
            print("   ② Linux側: メニュー1でクライアント起動")
            print("   ③ Windows側: メニュー2でテストデータ送信")
            print("   ④ Linux側: データ受信確認")
            print()
            print("3. トラブルシューティング:")
            print("   - ファイアウォール確認")
            print("   - VMware Tools インストール")
            print("   - シリアルデバイス権限")
        
        elif choice == "0":
            bridge.running = False
            break

if __name__ == "__main__":
    main()
