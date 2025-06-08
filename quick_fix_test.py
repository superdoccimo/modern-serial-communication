#!/usr/bin/env python3
"""
ModernSerialComm クイック修正テスト
正しい設定ファイルを明示的に指定
"""

import asyncio
import sys

async def test_with_correct_config():
    """正しい設定ファイルでテスト"""
    print("=== ModernSerialComm修正テスト ===")
    
    try:
        from modern_serial_comm import ModernSerialComm
        
        # Linux用設定ファイルを明示的に指定
        comm = ModernSerialComm("serial_config_linux.ini")
        print("✅ 明示的にLinux設定ファイル指定")
        
        # 設定確認
        print(f"設定ポート: {comm.port}")
        print(f"設定ボーレート: {comm.baudrate}")
        
        # 接続試行
        print("接続試行中...")
        result = await comm.connect()
        
        if result:
            print("✅ 接続成功！")
            await comm.send_string("修正テスト成功\n")
            print("✅ 送信成功！")
            await comm.disconnect()
            print("✅ 切断成功！")
            return True
        else:
            print("❌ 接続失敗")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_with_manual_config():
    """手動設定でテスト"""
    print("\n=== 手動設定テスト ===")
    
    try:
        from modern_serial_comm import ModernSerialComm, SerialConfig
        
        # 手動で設定作成
        config = SerialConfig()
        config.config.set('SERIAL', 'port', '/dev/ttyS0')
        config.config.set('SERIAL', 'baudrate', '9600')
        config.config.set('SERIAL', 'timeout', '1.0')
        print("✅ 手動設定作成")
        
        # インスタンス作成
        comm = ModernSerialComm()
        comm.config_manager = config  # 直接設定を注入
        comm._load_settings_from_config()  # 設定再読み込み
        
        print(f"手動設定ポート: {comm.port}")
        print(f"手動設定ボーレート: {comm.baudrate}")
        
        # 接続試行
        print("手動設定で接続試行中...")
        result = await comm.connect()
        
        if result:
            print("✅ 手動設定接続成功！")
            await comm.send_string("手動設定テスト成功\n")
            print("✅ 手動設定送信成功！")
            await comm.disconnect()
            print("✅ 手動設定切断成功！")
            return True
        else:
            print("❌ 手動設定接続失敗")
            return False
            
    except Exception as e:
        print(f"❌ 手動設定エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン実行"""
    print("🔧 ModernSerialComm修正テスト開始")
    print("=" * 50)
    
    # Windows用のイベントループ設定
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # テスト実行
    config_test = await test_with_correct_config()
    manual_test = await test_with_manual_config()
    
    print("\n" + "=" * 50)
    print("📊 修正テスト結果")
    print(f"設定ファイル指定: {'✅ 成功' if config_test else '❌ 失敗'}")
    print(f"手動設定: {'✅ 成功' if manual_test else '❌ 失敗'}")
    
    if config_test or manual_test:
        print("\n🎉 修正成功！ダッシュボードも動作するはずです")
    else:
        print("\n❌ さらなる調査が必要です")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ ユーザーによって中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()