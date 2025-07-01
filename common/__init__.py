"""
Modern Serial Communication - Common Modules
共通モジュールパッケージ
"""

__version__ = "1.0.0"
__author__ = "Modern Serial Communication Team"

# 共通モジュールのインポート
from .port_utils import detect_available_ports, get_platform_default_port, validate_port_access
from .config_manager import ConfigManager
from .localization import LocalizedStrings, get_localized_strings
from .ui_components import SerialStats, SendPanel, ConnectionPanel

__all__ = [
    'detect_available_ports',
    'get_platform_default_port', 
    'validate_port_access',
    'ConfigManager',
    'LocalizedStrings',
    'get_localized_strings',
    'SerialStats',
    'SendPanel',
    'ConnectionPanel'
]