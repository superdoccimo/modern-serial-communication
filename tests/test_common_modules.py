#!/usr/bin/env python3
"""
Modern Serial Communication - Common Modules Test Suite
共通モジュールの自動テスト
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.localization import LocalizationManager, get_localized_strings
from common.config_manager import ConfigManager
from common.port_utils import detect_available_ports, get_platform_default_port, validate_port_access


class TestLocalizationManager:
    """ローカライゼーション機能のテスト"""
    
    def test_japanese_localization(self):
        """日本語ローカライゼーションテスト"""
        mgr = LocalizationManager("jp")
        assert mgr.get("connect") == "接続"
        assert mgr.get("disconnect") == "切断"
        assert mgr.get("app_title") == "📡 Modern Serial Communication Dashboard"
    
    def test_english_localization(self):
        """英語ローカライゼーションテスト"""
        mgr = LocalizationManager("en")
        assert mgr.get("connect") == "Connect"
        assert mgr.get("disconnect") == "Disconnect"
        assert mgr.get("app_title") == "📡 Modern Serial Communication Dashboard"
    
    def test_string_formatting(self):
        """文字列フォーマットテスト"""
        mgr = LocalizationManager("jp")
        formatted = mgr.get("connected", "COM1")
        assert "COM1" in formatted
        assert "✅" in formatted
    
    def test_missing_key(self):
        """存在しないキーのテスト"""
        mgr = LocalizationManager("jp")
        result = mgr.get("nonexistent_key")
        assert result == "[nonexistent_key]"
    
    def test_language_switching(self):
        """言語切り替えテスト"""
        mgr = LocalizationManager("jp")
        assert mgr.get("send") == "送信"
        
        mgr.set_language("en")
        assert mgr.get("send") == "Send"


class TestConfigManager:
    """設定管理機能のテスト"""
    
    def test_config_creation(self):
        """設定マネージャー作成テスト"""
        config = ConfigManager()
        assert config is not None
        assert config.config is not None
    
    def test_serial_config_retrieval(self):
        """シリアル設定取得テスト"""
        config = ConfigManager()
        serial_config = config.get_serial_config()
        
        assert "port" in serial_config
        assert "baudrate" in serial_config
        assert isinstance(serial_config["baudrate"], int)
        assert serial_config["baudrate"] > 0
    
    def test_app_config_retrieval(self):
        """アプリケーション設定取得テスト"""
        config = ConfigManager()
        app_config = config.get_app_config()
        
        assert "language" in app_config
        assert "max_data_rows" in app_config
        assert isinstance(app_config["max_data_rows"], int)
    
    def test_config_validation(self):
        """設定検証テスト"""
        config = ConfigManager()
        is_valid, errors = config.validate_config()
        
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_platform_section_detection(self):
        """プラットフォーム別セクション検出テスト"""
        config = ConfigManager()
        section = config._get_platform_section()
        
        assert section in ["SERIAL_WINDOWS", "SERIAL_LINUX", "SERIAL_MACOS"]
    
    def test_language_detection(self):
        """言語検出テスト"""
        config = ConfigManager()
        language = config.get_language()
        
        assert language in ["jp", "en"]


class TestPortUtils:
    """ポートユーティリティ機能のテスト"""
    
    def test_port_detection(self):
        """ポート検出テスト"""
        ports = detect_available_ports()
        
        assert isinstance(ports, list)
        assert len(ports) > 0  # 少なくともloop://ポートは存在するはず
        
        # loop://ポートが含まれているか確認
        loop_port_found = any(port[0] == "loop://" for port in ports)
        assert loop_port_found, "loop:// port should always be available"
    
    def test_platform_default_port(self):
        """プラットフォームデフォルトポートテスト"""
        default_port = get_platform_default_port()
        
        assert isinstance(default_port, str)
        assert len(default_port) > 0
        
        # プラットフォーム別の期待値確認
        if sys.platform == "win32":
            assert default_port.startswith("COM")
        elif sys.platform.startswith("linux"):
            assert default_port.startswith("/dev/")
    
    def test_port_validation_loop(self):
        """ループバックポート検証テスト"""
        is_valid, error_msg = validate_port_access("loop://")
        
        assert is_valid is True
        assert error_msg == ""
    
    def test_port_validation_empty(self):
        """空ポート検証テスト"""
        is_valid, error_msg = validate_port_access("")
        
        assert is_valid is False
        assert "空です" in error_msg or "empty" in error_msg.lower()
    
    def test_port_validation_socket(self):
        """ソケットポート検証テスト"""
        is_valid, error_msg = validate_port_access("socket://localhost:5000")
        
        assert is_valid is True
        assert error_msg == ""
    
    @patch('os.path.exists')
    def test_linux_port_validation_nonexistent(self, mock_exists):
        """Linux非存在ポート検証テスト"""
        if not sys.platform.startswith('linux'):
            pytest.skip("Linux-specific test")
        
        mock_exists.return_value = False
        
        is_valid, error_msg = validate_port_access("/dev/ttyUSB999")
        
        assert is_valid is False
        assert "存在しません" in error_msg or "not exist" in error_msg.lower()


class TestModuleIntegration:
    """モジュール統合テスト"""
    
    def test_all_modules_importable(self):
        """全モジュールインポートテスト"""
        try:
            from common import (
                LocalizationManager, ConfigManager, 
                detect_available_ports, SerialStats
            )
            # インポートが成功すればOK
            assert True
        except ImportError as e:
            pytest.fail(f"Module import failed: {e}")
    
    def test_localization_config_integration(self):
        """ローカライゼーション・設定統合テスト"""
        config = ConfigManager()
        language = config.get_language()
        
        mgr = LocalizationManager(language)
        title = mgr.get("app_title")
        
        assert isinstance(title, str)
        assert len(title) > 0
    
    def test_port_detection_localization_integration(self):
        """ポート検出・ローカライゼーション統合テスト"""
        from common.port_utils import format_port_list
        
        ports = detect_available_ports()
        formatted = format_port_list(ports, max_items=5)
        
        assert isinstance(formatted, str)
        assert "ポート" in formatted or "Port" in formatted


# パフォーマンステスト
class TestPerformance:
    """パフォーマンステスト"""
    
    def test_port_detection_performance(self):
        """ポート検出パフォーマンステスト"""
        import time
        
        start_time = time.time()
        ports = detect_available_ports()
        end_time = time.time()
        
        # 5秒以内に完了すること
        assert end_time - start_time < 5.0
        assert len(ports) > 0
    
    def test_localization_performance(self):
        """ローカライゼーションパフォーマンステスト"""
        import time
        
        mgr = LocalizationManager("jp")
        
        start_time = time.time()
        for _ in range(1000):
            mgr.get("connect")
        end_time = time.time()
        
        # 1000回の文字列取得が1秒以内に完了すること
        assert end_time - start_time < 1.0


if __name__ == "__main__":
    # 直接実行時のテスト
    print("🧪 Running common modules tests...")
    
    # 基本的なテストを実行
    test_loc = TestLocalizationManager()
    test_loc.test_japanese_localization()
    test_loc.test_english_localization()
    print("✅ Localization tests passed")
    
    test_config = TestConfigManager()
    test_config.test_config_creation()
    test_config.test_serial_config_retrieval()
    print("✅ Config manager tests passed")
    
    test_port = TestPortUtils()
    test_port.test_port_detection()
    test_port.test_platform_default_port()
    print("✅ Port utils tests passed")
    
    test_integration = TestModuleIntegration()
    test_integration.test_all_modules_importable()
    print("✅ Integration tests passed")
    
    print("🎉 All tests completed successfully!")