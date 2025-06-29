#!/usr/bin/env python3
"""
Port Utilities - ポート関連ユーティリティ
共通のポート検出・管理機能
"""

import sys
import glob
import os
from typing import List, Tuple, Optional
import logging

# Linux環境でのみ権限チェック用モジュールをインポート
if sys.platform.startswith("linux"):
    import grp
    import pwd

logger = logging.getLogger(__name__)


def detect_available_ports() -> List[Tuple[str, str]]:
    """
    利用可能なシリアルポートを検出
    
    Returns:
        List[Tuple[str, str]]: [(ポート名, 説明), ...] のリスト
    """
    ports = []
    
    try:
        import serial.tools.list_ports
        for port in serial.tools.list_ports.comports():
            ports.append((port.device, port.description or "Unknown Device"))
        logger.info(f"Found {len(ports)} ports using serial.tools.list_ports")
    except ImportError:
        logger.warning("serial.tools.list_ports not available, using manual detection")
        # 手動検出
        if sys.platform == "win32":
            # Windows COM ポート
            for i in range(1, 21):
                port_name = f"COM{i}"
                ports.append((port_name, f"COM Port {i}"))
        else:
            # Linux/Unix シリアルデバイス
            patterns = ['/dev/ttyS*', '/dev/ttyUSB*', '/dev/ttyACM*', '/dev/ttyAMA*']
            for pattern in patterns:
                for device in glob.glob(pattern):
                    if os.path.exists(device):
                        device_name = os.path.basename(device)
                        ports.append((device, f"Serial Device {device_name}"))
    
    # テスト用ループバックポート追加
    ports.append(("loop://", "Loop back (テスト用)"))
    
    logger.info(f"Total detected ports: {len(ports)}")
    return ports


def get_platform_default_port() -> str:
    """
    プラットフォーム別のデフォルトポートを取得
    
    Returns:
        str: デフォルトポート名
    """
    if sys.platform == "win32":
        return "COM2"
    elif sys.platform.startswith("linux"):
        return "/dev/ttyS0"
    elif sys.platform == "darwin":  # macOS
        return "/dev/tty.usbserial"
    else:
        return "loop://"  # 不明なプラットフォームはテスト用


def validate_port_access(port: str) -> Tuple[bool, str]:
    """
    ポートのアクセス可能性を検証
    
    Args:
        port (str): ポート名
        
    Returns:
        Tuple[bool, str]: (アクセス可能, エラーメッセージ)
    """
    if not port or port.strip() == "":
        return False, "ポート名が空です"
    
    # ループバックポートは常にOK
    if port.startswith("loop://") or port.startswith("socket://"):
        return True, ""
    
    # Linux環境での権限チェック
    if sys.platform.startswith('linux') and port.startswith('/dev/'):
        if not os.path.exists(port):
            # 利用可能なポートを提案
            available_ports = []
            for prefix in ['/dev/ttyUSB', '/dev/ttyACM', '/dev/ttyS']:
                for i in range(10):
                    candidate = f"{prefix}{i}"
                    if os.path.exists(candidate):
                        available_ports.append(candidate)
            
            error_msg = f"{port} が存在しません。"
            if available_ports:
                error_msg += f" 利用可能: {', '.join(available_ports[:5])}"
            else:
                error_msg += " シリアルポートが見つかりません。"
            return False, error_msg
        
        # 権限チェック
        if not os.access(port, os.R_OK | os.W_OK):
            error_msg = f"{port} への権限がありません。"
            try:
                current_user = pwd.getpwuid(os.getuid()).pw_name
                groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
                if 'dialout' not in groups:
                    error_msg += " 解決策: sudo usermod -a -G dialout $USER && logout"
                else:
                    error_msg += " sudoまたはデバイス権限を確認してください。"
            except Exception:
                error_msg += " 権限を確認してください。"
            return False, error_msg
    
    return True, ""


def get_port_suggestions(failed_port: str) -> List[str]:
    """
    接続に失敗したポートに対する代替ポート候補を提案
    
    Args:
        failed_port (str): 失敗したポート名
        
    Returns:
        List[str]: 代替ポート候補のリスト
    """
    suggestions = []
    
    # 利用可能なポートを取得
    available_ports = detect_available_ports()
    
    # 失敗したポートを除外
    for port, desc in available_ports:
        if port != failed_port:
            suggestions.append(port)
    
    # プラットフォーム別推奨ポートを優先
    default_port = get_platform_default_port()
    if default_port in suggestions:
        suggestions.remove(default_port)
        suggestions.insert(0, default_port)
    
    return suggestions[:5]  # 最大5つまで


def format_port_list(ports: List[Tuple[str, str]], max_items: int = 10) -> str:
    """
    ポートリストを見やすい文字列に整形
    
    Args:
        ports: ポートリスト
        max_items: 表示する最大項目数
        
    Returns:
        str: 整形されたポートリスト文字列
    """
    if not ports:
        return "❌ 利用可能なポートがありません"
    
    content = "🔌 利用可能なポート:\n"
    content += "━━━━━━━━━━━━━━━━\n"
    
    for i, (port, desc) in enumerate(ports[:max_items]):
        content += f"{i+1:2d}. {port}\n"
        if len(desc) > 30:
            content += f"    {desc[:30]}...\n"
        else:
            content += f"    {desc}\n"
    
    if len(ports) > max_items:
        content += f"... 他に {len(ports) - max_items} 個のポートがあります\n"
    
    return content


def is_virtual_port(port: str) -> bool:
    """
    仮想ポート（ループバック、ソケット等）かどうかを判定
    
    Args:
        port (str): ポート名
        
    Returns:
        bool: 仮想ポートの場合True
    """
    virtual_prefixes = ["loop://", "socket://", "spy://", "alt://"]
    return any(port.startswith(prefix) for prefix in virtual_prefixes)


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    print("=== ポート検出テスト ===")
    ports = detect_available_ports()
    print(format_port_list(ports))
    
    print(f"\n=== デフォルトポート ===")
    default = get_platform_default_port()
    print(f"デフォルトポート: {default}")
    
    print(f"\n=== ポート検証テスト ===")
    valid, msg = validate_port_access(default)
    print(f"検証結果: {valid}, メッセージ: {msg}")