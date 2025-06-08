#!/usr/bin/env python3
"""
非同期シリアル接続デバッグツール
ModernSerialCommの問題を特定
"""

import asyncio
import sys
import os

def test_sync_serial():
    """同期シリアル接続テスト"""
    print("=== 同期シリアル接続テスト ===")
    
    try:
        import serial
        print(f"✅ pyserial version: {serial.VERSION}")
        
        with serial.Serial('/dev/ttyS0', 9600, timeout=1) as ser:
            print("✅ 同期接続成功")
            ser.write(b'sync test\n')
            print("✅ 同期送信成功")
            return True
            
    except Exception as e:
        print(f"❌ 同期接続失敗: {e}")
        return False

async def test_async_serial():
    """非同期シリアル接続テスト"""
    print("\n=== 非同期シリアル接続テスト ===")
    
    try:
        import serial_asyncio
        print("✅ serial_asyncio imported")
        
        # 基本的な非同期接続
        print("非同期接続試行中...")
        reader, writer = await serial_asyncio.open_serial_connection(
            url='/dev/ttyS0',
            baudrate=9600,
            timeout=1.0
        )
        print("✅ 非同期接続成功")
        
        # 送信テスト
        writer.write(b'async test\n')
        await writer.drain()
        print("✅ 非同期送信成功")
        
        # クリーンアップ
        writer.close()
        if hasattr(writer, 'wait_closed'):
            await writer.wait_closed()
        print("✅ 非同期切断成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 非同期接続失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_modern_serial_comm():
    """ModernSerialCommテスト"""
    print("\n=== ModernSerialComm テスト ===")
    
    try:
        # パスを調整
        sys.path.append('.')
        from modern_serial_comm import ModernSerialComm, SerialConfig
        print("✅ ModernSerialComm imported")
        
        # 設定作成
        config = SerialConfig()
        config.config.set('SERIAL', 'port', '/dev/ttyS0')
        config.config.set('SERIAL', 'baudrate', '9600')
        print("✅ Config created")
        
        # インスタンス作成
        comm = ModernSerialComm()
        comm.config = config  # 直接設定
        print("✅ ModernSerialComm instance created")
        
        # 接続試行
        print("ModernSerialComm接続試行中...")
        result = await comm.connect()
        
        if result:
            print("✅ ModernSerialComm接続成功")
            await comm.send_string("ModernSerialComm test\n")
            print("✅ ModernSerialComm送信成功")
            await comm.disconnect()
            print("✅ ModernSerialComm切断成功")
            return True
        else:
            print("❌ ModernSerialComm接続失敗")
            return False
            
    except Exception as e:
        print(f"❌ ModernSerialComm例外: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_config_file():
    """設定ファイル確認"""
    print("\n=== 設定ファイル確認 ===")
    
    config_files = [
        'serial_config_linux.ini',
        'serial_config.ini'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file} 存在")
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                print(f"内容:\n{content}")
            except Exception as e:
                print(f"❌ 読み取りエラー: {e}")
        else:
            print(f"❌ {config_file} 存在しない")

def check_permissions():
    """権限確認"""
    print("\n=== 権限確認 ===")
    
    device = '/dev/ttyS0'
    try:
        # 読み取り権限
        readable = os.access(device, os.R_OK)
        writable = os.access(device, os.W_OK)
        print(f"読み取り権限: {readable}")
        print(f"書き込み権限: {writable}")
        
        # ファイル状態
        stat_info = os.stat(device)
        print(f"ファイルモード: {oct(stat_info.st_mode)}")
        
    except Exception as e:
        print(f"❌ 権限確認エラー: {e}")

async def main():
    """メイン実行"""
    print("🔍 非同期シリアル接続デバッグ開始")
    print("=" * 50)
    
    # Windows用のイベントループ設定
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    check_permissions()
    check_config_file()
    
    # テスト実行
    sync_ok = test_sync_serial()
    async_ok = await test_async_serial()
    modern_ok = await test_modern_serial_comm()
    
    print("\n" + "=" * 50)
    print("📊 テスト結果まとめ")
    print(f"同期シリアル: {'✅ 成功' if sync_ok else '❌ 失敗'}")
    print(f"非同期シリアル: {'✅ 成功' if async_ok else '❌ 失敗'}")
    print(f"ModernSerialComm: {'✅ 成功' if modern_ok else '❌ 失敗'}")
    
    if sync_ok and not async_ok:
        print("\n💡 診断: 非同期ライブラリに問題があります")
        print("   解決策: pyserial-asyncioのバージョン確認またはダウングレード")
    elif sync_ok and async_ok and not modern_ok:
        print("\n💡 診断: ModernSerialCommの設定に問題があります")
        print("   解決策: 設定ファイルまたはコード修正")
    elif not sync_ok:
        print("\n💡 診断: 基本的なシリアル接続に問題があります")
        print("   解決策: 権限・デバイス確認")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ ユーザーによって中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()