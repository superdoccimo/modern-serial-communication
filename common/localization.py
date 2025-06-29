#!/usr/bin/env python3
"""
Localization - 多言語対応
統一された文字列リソース管理
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class LocalizedStrings:
    """多言語文字列定義クラス"""
    
    # 日本語文字列
    JP = {
        # アプリケーション情報
        "app_title": "📡 Modern Serial Communication Dashboard",
        "app_subtitle": "クロスプラットフォーム対応シリアル通信ツール",
        
        # UI コンポーネント
        "select_port": "🔌 ポート選択",
        "port_control": "🔌 接続制御", 
        "data_send": "📤 データ送信",
        "statistics": "📊 統計情報",
        "port_info": "🔌 ポート情報",
        
        # ボタン
        "connect": "接続",
        "disconnect": "切断",
        "send": "送信",
        "clear": "クリア",
        "detect_ports": "ポート検出",
        "preset": "設定値",
        "save_csv": "CSV保存",
        "clear_data": "データクリア",
        
        # プレースホルダー
        "port_placeholder": "ポート名を入力 (例: {})",
        "send_placeholder": "送信データを入力...",
        
        # メッセージ
        "connecting": "接続中...",
        "connected": "✅ {} に接続しました",
        "disconnected": "🔌 接続を切断しました",
        "connection_failed": "❌ {} への接続に失敗しました",
        "connection_error": "❌ 接続エラー: {}",
        "not_connected": "❌ 接続されていません",
        "port_not_selected": "❌ ポートを選択してください",
        "port_not_entered": "❌ ポートを入力してください",
        "data_sent": "📤 送信: {}",
        "data_received": "📥 受信: {}",
        "send_failed": "❌ 送信に失敗しました",
        "data_processing_error": "❌ データ処理エラー: {}",
        "data_cleared": "🗑️ データをクリアしました",
        "no_data_to_save": "💾 保存するデータがありません",
        "data_saved": "💾 {} に保存しました ({} 件)",
        "save_error": "❌ 保存エラー: {}",
        "config_not_found": "⚠️ {} が見つかりません。手動設定を使用します",
        "detecting_ports": "🔍 ポート検出中...",
        "ports_detected": "🔌 {} 個のポートを検出しました",
        "preset_port_set": "🎯 プリセットポート設定: {}",
        "app_started": "📡 Enhanced Serial Dashboard 起動完了",
        "app_help": "💡 'd'でポート検出、'q'で終了、'c'でデータクリア、's'でCSV保存",
        
        # 統計情報
        "stats_received": "📥 受信: {} ({} B)",
        "stats_sent": "📤 送信: {} ({} B)", 
        "stats_time": "⏱️  時間: {}",
        "stats_rate": "📈 速度: {:.1f} pkt/s",
        
        # ポート情報
        "available_ports": "🔌 利用可能ポート:",
        "no_ports": "❌ ポートなし",
        
        # テーブルヘッダー
        "table_time": "時刻",
        "table_direction": "方向",
        "table_data": "データ",
        "table_length": "長さ",
        "table_rx": "📥 RX",
        "table_tx": "📤 TX",
        
        # エラーメッセージ
        "permission_denied": "権限がありません",
        "port_not_found": "ポートが見つかりません",
        "device_busy": "デバイスが使用中です",
        "timeout_error": "タイムアウトエラー",
        "connection_lost": "接続が切断されました",
        
        # キーバインド
        "key_quit": "終了",
        "key_clear": "クリア",
        "key_save": "保存",
        "key_detect": "検出",
    }
    
    # 英語文字列
    EN = {
        # Application info
        "app_title": "📡 Modern Serial Communication Dashboard",
        "app_subtitle": "Cross-platform serial communication tool",
        
        # UI Components
        "select_port": "🔌 Select Port",
        "port_control": "🔌 Port Control",
        "data_send": "📤 Data Send",
        "statistics": "📊 Statistics",
        "port_info": "🔌 Port Info",
        
        # Buttons
        "connect": "Connect",
        "disconnect": "Disconnect",
        "send": "Send",
        "clear": "Clear",
        "detect_ports": "Detect Ports",
        "preset": "Preset",
        "save_csv": "Save CSV",
        "clear_data": "Clear Data",
        
        # Placeholders
        "port_placeholder": "Enter port name (e.g., {})",
        "send_placeholder": "Enter data to send...",
        
        # Messages
        "connecting": "Connecting...",
        "connected": "✅ Connected to {}",
        "disconnected": "🔌 Disconnected",
        "connection_failed": "❌ Failed to connect to {}",
        "connection_error": "❌ Connection error: {}",
        "not_connected": "❌ Not connected",
        "port_not_selected": "❌ Please select a port",
        "port_not_entered": "❌ Please enter a port",
        "data_sent": "📤 Sent: {}",
        "data_received": "📥 Received: {}",
        "send_failed": "❌ Failed to send data",
        "data_processing_error": "❌ Data processing error: {}",
        "data_cleared": "🗑️ Data cleared",
        "no_data_to_save": "💾 No data to save",
        "data_saved": "💾 Saved to {} ({} records)",
        "save_error": "❌ Save error: {}",
        "config_not_found": "⚠️ {} not found. Using manual configuration",
        "detecting_ports": "🔍 Detecting ports...",
        "ports_detected": "🔌 Detected {} ports",
        "preset_port_set": "🎯 Preset port set: {}",
        "app_started": "📡 Enhanced Serial Dashboard started",
        "app_help": "💡 Press 'd' to detect ports, 'q' to quit, 'c' to clear data, 's' to save CSV",
        
        # Statistics
        "stats_received": "📥 Received: {} ({} B)",
        "stats_sent": "📤 Sent: {} ({} B)",
        "stats_time": "⏱️  Time: {}",
        "stats_rate": "📈 Rate: {:.1f} pkt/s",
        
        # Port info
        "available_ports": "🔌 Available Ports:",
        "no_ports": "❌ No ports",
        
        # Table headers
        "table_time": "Time",
        "table_direction": "Direction",
        "table_data": "Data",
        "table_length": "Length",
        "table_rx": "📥 RX",
        "table_tx": "📤 TX",
        
        # Error messages
        "permission_denied": "Permission denied",
        "port_not_found": "Port not found",
        "device_busy": "Device busy",
        "timeout_error": "Timeout error",
        "connection_lost": "Connection lost",
        
        # Key bindings
        "key_quit": "Quit",
        "key_clear": "Clear",
        "key_save": "Save",
        "key_detect": "Detect",
    }


def get_localized_strings(language: str = "jp") -> Dict[str, Any]:
    """
    指定された言語の文字列辞書を取得
    
    Args:
        language (str): 言語コード ("jp" または "en")
        
    Returns:
        Dict[str, Any]: 文字列辞書
    """
    if language.lower() == "en":
        return LocalizedStrings.EN
    else:
        return LocalizedStrings.JP


def get_string(key: str, language: str = "jp", *args, **kwargs) -> str:
    """
    指定されたキーの文字列を取得（フォーマット対応）
    
    Args:
        key (str): 文字列キー
        language (str): 言語コード
        *args: フォーマット引数
        **kwargs: フォーマット引数
        
    Returns:
        str: ローカライズされた文字列
    """
    strings = get_localized_strings(language)
    
    if key not in strings:
        logger.warning(f"Localization key '{key}' not found for language '{language}'")
        return f"[{key}]"  # キーが見つからない場合
    
    text = strings[key]
    
    # フォーマット処理
    if args or kwargs:
        try:
            return text.format(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error formatting string '{key}': {e}")
            return text
    
    return text


def get_supported_languages() -> List[str]:
    """
    サポートされている言語のリストを取得
    
    Returns:
        List[str]: 言語コードのリスト
    """
    return ["jp", "en"]


def detect_system_language() -> str:
    """
    システムの言語設定を検出
    
    Returns:
        str: 検出された言語コード
    """
    import locale
    import os
    
    # 環境変数から言語を検出
    lang_env = os.environ.get('LANG', '').lower()
    if 'ja' in lang_env or 'jp' in lang_env:
        return "jp"
    
    # システムロケールから検出
    try:
        system_locale = locale.getdefaultlocale()[0]
        if system_locale and ('ja' in system_locale.lower() or 'jp' in system_locale.lower()):
            return "jp"
    except Exception:
        pass
    
    # デフォルトは日本語
    return "jp"


class LocalizationManager:
    """ローカライゼーション管理クラス"""
    
    def __init__(self, language: str = None):
        self.language = language or detect_system_language()
        self.strings = get_localized_strings(self.language)
        logger.info(f"Localization initialized for language: {self.language}")
    
    def get(self, key: str, *args, **kwargs) -> str:
        """文字列を取得"""
        return get_string(key, self.language, *args, **kwargs)
    
    def set_language(self, language: str):
        """言語を変更"""
        if language in get_supported_languages():
            self.language = language
            self.strings = get_localized_strings(language)
            logger.info(f"Language changed to: {language}")
        else:
            logger.warning(f"Unsupported language: {language}")


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    print("=== ローカライゼーション テスト ===")
    
    # 自動言語検出
    detected_lang = detect_system_language()
    print(f"検出された言語: {detected_lang}")
    
    # 日本語テスト
    print("\n=== 日本語テスト ===")
    mgr_jp = LocalizationManager("jp")
    print(f"タイトル: {mgr_jp.get('app_title')}")
    print(f"接続メッセージ: {mgr_jp.get('connected', 'COM1')}")
    
    # 英語テスト
    print("\n=== 英語テスト ===")
    mgr_en = LocalizationManager("en")
    print(f"Title: {mgr_en.get('app_title')}")
    print(f"Connect message: {mgr_en.get('connected', 'COM1')}")
    
    # 言語切り替えテスト
    print("\n=== 言語切り替えテスト ===")
    mgr = LocalizationManager("jp")
    print(f"日本語: {mgr.get('connect')}")
    mgr.set_language("en")
    print(f"英語: {mgr.get('connect')}")