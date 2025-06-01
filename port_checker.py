#!/usr/bin/env python3
"""
シリアルポート確認ツール
利用可能なシリアルポートを一覧表示
"""

import serial.tools.list_ports
import sys


def list_serial_ports():
    """利用可能なシリアルポートを一覧表示"""
    print("=== 利用可能なシリアルポート ===")
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("利用可能なシリアルポートが見つかりません。")
        print("\nテスト用の設定:")
        print("- loop://  : ループバック（テスト用）")
        print("- spy://COM1 : 既存ポートの監視")
        return []
    
    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device}")
        print(f"   説明: {port.description}")
        print(f"   ハードウェアID: {port.hwid}")
        if hasattr(port, 'manufacturer') and port.manufacturer:
            print(f"   製造元: {port.manufacturer}")
        print()
    
    return [port.device for port in ports]


def test_port_connection(port_name: str):
    """指定ポートへの接続テスト"""
    try:
        import serial
        print(f"\n=== {port_name} 接続テスト ===")
        
        # 基本的な接続テスト
        with serial.Serial(port_name, 9600, timeout=1) as ser:
            print(f"✅ {port_name} への接続に成功しました")
            print(f"   ボーレート: {ser.baudrate}")
            print(f"   データビット: {ser.bytesize}")
            print(f"   ストップビット: {ser.stopbits}")
            print(f"   パリティ: {ser.parity}")
            return True
            
    except serial.SerialException as e:
        print(f"❌ {port_name} への接続に失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False


def create_test_config(port_name: str = None):
    """テスト用設定ファイル作成"""
    import configparser
    
    config = configparser.ConfigParser()
    
    # 利用可能なポートを取得
    available_ports = list_serial_ports()
    
    if port_name:
        selected_port = port_name
    elif available_ports:
        selected_port = available_ports[0]
        print(f"\n最初に見つかったポート {selected_port} を使用します")
    else:
        selected_port = 'loop://'
        print("\n実際のポートが見つからないため、テスト用ループバックを使用します")
    
    config['SERIAL'] = {
        'port': selected_port,
        'baudrate': '9600',
        'bytesize': '8',
        'parity': 'N',
        'stopbits': '1',
        'timeout': '1.0'
    }
    
    config['NETWORK'] = {
        'tcp_host': 'localhost',
        'tcp_port': '5000',
        'use_tcp': 'false'
    }
    
    config['LOGGING'] = {
        'level': 'INFO',
        'format': 'json_lines',
        'output_file': 'serial_log.jsonl'
    }
    
    # 設定ファイル保存
    config_path = 'serial_config.ini'
    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print(f"\n設定ファイル '{config_path}' を作成しました")
    print(f"使用ポート: {selected_port}")
    
    return config_path


if __name__ == "__main__":
    print("Python Serial Communication - ポート確認ツール")
    print("=" * 50)
    
    # 利用可能ポート一覧
    available_ports = list_serial_ports()
    
    # 対話的にポート選択
    if available_ports:
        print(f"\n{len(available_ports)}個のポートが見つかりました。")
        print("テストしたいポート番号を入力してください（Enterでスキップ）:")
        
        try:
            choice = input("> ").strip()
            if choice.isdigit():
                port_index = int(choice) - 1
                if 0 <= port_index < len(available_ports):
                    selected_port = available_ports[port_index]
                    test_port_connection(selected_port)
                    create_test_config(selected_port)
                else:
                    print("無効な番号です。デフォルト設定を作成します。")
                    create_test_config()
            else:
                print("デフォルト設定を作成します。")
                create_test_config()
        except KeyboardInterrupt:
            print("\n中断されました。")
            sys.exit(1)
    else:
        create_test_config()
    
    print("\n次のコマンドでメインプログラムを実行してください:")
    print("python modern_serial_comm.py")