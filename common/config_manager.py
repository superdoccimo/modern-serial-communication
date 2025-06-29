#!/usr/bin/env python3
"""
Configuration Manager - 設定管理
統一された設定ファイル管理機能
"""

import os
import sys
import configparser
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """統一設定管理クラス"""
    
    DEFAULT_CONFIG = {
        'SERIAL_WINDOWS': {
            'port': 'COM2',
            'baudrate': '9600',
            'bytesize': '8',
            'parity': 'N',
            'stopbits': '1',
            'timeout': '1.0',
            'rtscts': 'False',
            'dsrdtr': 'False',
            'xonxoff': 'False'
        },
        'SERIAL_LINUX': {
            'port': '/dev/ttyS0',
            'baudrate': '9600',
            'bytesize': '8',
            'parity': 'N',
            'stopbits': '1',
            'timeout': '1.0',
            'rtscts': 'False',
            'dsrdtr': 'False',
            'xonxoff': 'False'
        },
        'SERIAL_MACOS': {
            'port': '/dev/tty.usbserial',
            'baudrate': '9600',
            'bytesize': '8',
            'parity': 'N',
            'stopbits': '1',
            'timeout': '1.0',
            'rtscts': 'False',
            'dsrdtr': 'False',
            'xonxoff': 'False'
        },
        'APP': {
            'language': 'auto',
            'log_level': 'INFO',
            'timestamp_format': '%%Y-%%m-%%d %%H:%%M:%%S.%%f',
            'max_data_rows': '1000',
            'max_sparkline_points': '100',
            'auto_save_interval': '300'  # 秒
        },
        'NETWORK': {
            'tcp_host': 'localhost',
            'tcp_port': '5000',
            'use_tcp': 'false',
            'tcp_timeout': '5.0'
        },
        'LOGGING': {
            'level': 'INFO',
            'format': 'json_lines',
            'output_file': 'serial_log.jsonl',
            'max_file_size': '10485760',  # 10MB
            'backup_count': '5'
        },
        'UI': {
            'theme': 'auto',
            'show_sparkline': 'true',
            'show_statistics': 'true',
            'table_auto_scroll': 'true'
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        設定管理クラス初期化
        
        Args:
            config_file: 設定ファイルパス（Noneの場合は自動選択）
        """
        self.config_file = Path(config_file) if config_file else self._get_default_config_file()
        self.config = configparser.ConfigParser()
        self.config.read_dict(self.DEFAULT_CONFIG)  # デフォルト設定をロード
        self.load_config()
    
    def _get_default_config_file(self) -> Path:
        """デフォルト設定ファイルパスを取得"""
        return Path("serial_config.ini")
    
    def _get_platform_section(self) -> str:
        """現在のプラットフォームに対応するセクション名を取得"""
        if sys.platform == "win32":
            return "SERIAL_WINDOWS"
        elif sys.platform.startswith("linux"):
            return "SERIAL_LINUX"
        elif sys.platform == "darwin":
            return "SERIAL_MACOS"
        else:
            return "SERIAL_LINUX"  # デフォルト
    
    def load_config(self) -> bool:
        """
        設定ファイルを読み込み
        
        Returns:
            bool: 読み込み成功の場合True
        """
        if self.config_file.exists():
            try:
                self.config.read(self.config_file, encoding='utf-8')
                logger.info(f"Configuration loaded from {self.config_file}")
                return True
            except Exception as e:
                logger.error(f"Error reading config file {self.config_file}: {e}")
                self._create_default_config()
                return False
        else:
            logger.warning(f"Config file {self.config_file} not found. Creating default configuration.")
            self._create_default_config()
            self.save_config()
            return True
    
    def _create_default_config(self):
        """デフォルト設定を作成"""
        self.config.clear()
        self.config.read_dict(self.DEFAULT_CONFIG)
        logger.info("Default configuration created.")
    
    def save_config(self) -> bool:
        """
        設定ファイルを保存
        
        Returns:
            bool: 保存成功の場合True
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config file {self.config_file}: {e}")
            return False
    
    def get_serial_config(self, port: Optional[str] = None) -> Dict[str, Any]:
        """
        現在のプラットフォームに応じたシリアル設定を取得
        
        Args:
            port: 使用するポート（Noneの場合は設定ファイルから取得）
            
        Returns:
            Dict[str, Any]: シリアル設定辞書
        """
        section = self._get_platform_section()
        
        # ポートが指定された場合は上書き
        config = dict(self.config[section])
        if port:
            config['port'] = port
        
        # データ型変換
        try:
            config['baudrate'] = int(config['baudrate'])
            config['bytesize'] = int(config['bytesize'])
            config['stopbits'] = float(config['stopbits'])
            config['timeout'] = float(config['timeout']) if config['timeout'] != 'None' else None
            config['rtscts'] = config['rtscts'].lower() == 'true'
            config['dsrdtr'] = config['dsrdtr'].lower() == 'true'
            config['xonxoff'] = config['xonxoff'].lower() == 'true'
        except (ValueError, KeyError) as e:
            logger.error(f"Error converting serial config values: {e}")
            # デフォルト値で補完
            config.update({
                'baudrate': 9600,
                'bytesize': 8,
                'stopbits': 1.0,
                'timeout': 1.0,
                'rtscts': False,
                'dsrdtr': False,
                'xonxoff': False
            })
        
        return config
    
    def set_serial_config(self, **kwargs) -> bool:
        """
        シリアル設定を更新
        
        Args:
            **kwargs: 設定値（port, baudrate, bytesize等）
            
        Returns:
            bool: 更新成功の場合True
        """
        section = self._get_platform_section()
        
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        for key, value in kwargs.items():
            self.config.set(section, key, str(value))
        
        logger.info(f"Serial config updated: {kwargs}")
        return self.save_config()
    
    def get_app_config(self) -> Dict[str, Any]:
        """
        アプリケーション設定を取得
        
        Returns:
            Dict[str, Any]: アプリケーション設定辞書
        """
        config = dict(self.config['APP'])
        
        # データ型変換
        try:
            config['max_data_rows'] = int(config['max_data_rows'])
            config['max_sparkline_points'] = int(config['max_sparkline_points'])
            config['auto_save_interval'] = int(config['auto_save_interval'])
        except (ValueError, KeyError) as e:
            logger.error(f"Error converting app config values: {e}")
            config.update({
                'max_data_rows': 1000,
                'max_sparkline_points': 100,
                'auto_save_interval': 300
            })
        
        return config
    
    def get_network_config(self) -> Dict[str, Any]:
        """
        ネットワーク設定を取得
        
        Returns:
            Dict[str, Any]: ネットワーク設定辞書
        """
        config = dict(self.config['NETWORK'])
        
        # データ型変換
        try:
            config['tcp_port'] = int(config['tcp_port'])
            config['tcp_timeout'] = float(config['tcp_timeout'])
            config['use_tcp'] = config['use_tcp'].lower() == 'true'
        except (ValueError, KeyError) as e:
            logger.error(f"Error converting network config values: {e}")
            config.update({
                'tcp_port': 5000,
                'tcp_timeout': 5.0,
                'use_tcp': False
            })
        
        return config
    
    def get_ui_config(self) -> Dict[str, Any]:
        """
        UI設定を取得
        
        Returns:
            Dict[str, Any]: UI設定辞書
        """
        config = dict(self.config['UI'])
        
        # データ型変換
        try:
            config['show_sparkline'] = config['show_sparkline'].lower() == 'true'
            config['show_statistics'] = config['show_statistics'].lower() == 'true'
            config['table_auto_scroll'] = config['table_auto_scroll'].lower() == 'true'
        except (ValueError, KeyError) as e:
            logger.error(f"Error converting UI config values: {e}")
            config.update({
                'show_sparkline': True,
                'show_statistics': True,
                'table_auto_scroll': True
            })
        
        return config
    
    def get_setting(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        指定されたセクション・キーの設定値を取得
        
        Args:
            section: セクション名
            key: キー名
            fallback: デフォルト値
            
        Returns:
            Any: 設定値
        """
        try:
            return self.config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def set_setting(self, section: str, key: str, value: Any) -> bool:
        """
        設定値を更新
        
        Args:
            section: セクション名
            key: キー名
            value: 設定値
            
        Returns:
            bool: 更新成功の場合True
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
        return self.save_config()
    
    def get_language(self) -> str:
        """
        言語設定を取得
        
        Returns:
            str: 言語コード
        """
        language = self.get_setting('APP', 'language', 'auto')
        
        if language == 'auto':
            # システム言語を自動検出
            import locale
            try:
                system_locale = locale.getdefaultlocale()[0]
                if system_locale and 'ja' in system_locale.lower():
                    return 'jp'
            except Exception:
                pass
            return 'jp'  # デフォルト
        
        return language
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        設定の妥当性を検証
        
        Returns:
            Tuple[bool, List[str]]: (有効性, エラーメッセージリスト)
        """
        errors = []
        
        # 必須セクションの確認
        required_sections = ['SERIAL_WINDOWS', 'SERIAL_LINUX', 'APP']
        for section in required_sections:
            if not self.config.has_section(section):
                errors.append(f"Missing required section: {section}")
        
        # シリアル設定の確認
        try:
            serial_config = self.get_serial_config()
            if serial_config['baudrate'] <= 0:
                errors.append("Invalid baudrate: must be positive")
            if serial_config['bytesize'] not in [5, 6, 7, 8]:
                errors.append("Invalid bytesize: must be 5, 6, 7, or 8")
        except Exception as e:
            errors.append(f"Serial config validation error: {e}")
        
        # ネットワーク設定の確認
        try:
            network_config = self.get_network_config()
            if not (1 <= network_config['tcp_port'] <= 65535):
                errors.append("Invalid TCP port: must be 1-65535")
        except Exception as e:
            errors.append(f"Network config validation error: {e}")
        
        return len(errors) == 0, errors
    
    def export_config(self, export_path: str) -> bool:
        """
        設定をファイルにエクスポート
        
        Args:
            export_path: エクスポート先パス
            
        Returns:
            bool: エクスポート成功の場合True
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logger.info(f"Configuration exported to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting config to {export_path}: {e}")
            return False


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    print("=== 設定管理テスト ===")
    
    # 設定管理インスタンス作成
    config_mgr = ConfigManager()
    
    # シリアル設定取得
    print("\n=== シリアル設定 ===")
    serial_config = config_mgr.get_serial_config()
    for key, value in serial_config.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # アプリケーション設定
    print("\n=== アプリケーション設定 ===")
    app_config = config_mgr.get_app_config()
    for key, value in app_config.items():
        print(f"  {key}: {value}")
    
    # 設定検証
    print("\n=== 設定検証 ===")
    is_valid, errors = config_mgr.validate_config()
    print(f"設定有効性: {is_valid}")
    if errors:
        for error in errors:
            print(f"  エラー: {error}")
    
    # 言語設定
    print(f"\n=== 言語設定 ===")
    language = config_mgr.get_language()
    print(f"言語: {language}")