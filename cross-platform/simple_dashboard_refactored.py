#!/usr/bin/env python3
"""
Simple Enhanced Serial Communication Dashboard - Refactored Version
共通ライブラリを使用したリファクタリング版簡易ダッシュボード

元のコード行数: 539行 → リファクタリング後: 約150行 (約72%削減)
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label
from textual.binding import Binding
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 共通ライブラリインポート
from common.base_dashboard import BaseDashboard
from common.ui_components import ConnectionPanel, PortInfoPanel
from common.port_utils import get_platform_default_port


class SimpleEnhancedDashboard(BaseDashboard):
    """シンプル版拡張ダッシュボード（リファクタリング版）"""
    
    # カスタムキーバインド追加
    BINDINGS = BaseDashboard.BINDINGS + [
        Binding("p", "set_preset", "Preset Port", show=True),
    ]
    
    def __init__(self, language: str = "jp", **kwargs):
        """
        初期化
        
        Args:
            language: 表示言語 ("jp" または "en")
        """
        super().__init__(language=language, **kwargs)
        
        # アプリ固有のタイトル設定
        self.title = "📡 Simple Enhanced Serial Dashboard"
        self.sub_title = self.loc.get("app_subtitle")
    
    def compose_left_panel(self) -> ComposeResult:
        """左パネル構成"""
        # 接続制御パネル（手動入力版）
        yield SimpleConnectionPanel(self.loc, id="connection_panel")
        
        # 基底クラスの共通パネル（送信・統計）
        yield from super().compose_left_panel()
        
        # ポート情報パネル
        yield PortInfoPanel(self.loc, id="port_info_panel")
    
    async def handle_custom_button(self, event: Button.Pressed) -> None:
        """カスタムボタン処理"""
        button_id = event.button.id
        
        if button_id == "connect_btn":
            await self.handle_connect()
        elif button_id == "disconnect_btn":
            await self.disconnect_serial()
    
    async def handle_connect(self):
        """接続処理"""
        port_input = self.query_one("#port_input", Input)
        port = port_input.value.strip()
        
        if not port:
            self.log_message(self.loc.get("port_not_entered"))
            return
        
        await self.connect_serial(port)
    
    def update_connection_ui(self, connected: bool, port: str = ""):
        """接続状態に応じたUI更新"""
        try:
            connect_btn = self.query_one("#connect_btn", Button)
            disconnect_btn = self.query_one("#disconnect_btn", Button)
            
            connect_btn.disabled = connected
            disconnect_btn.disabled = not connected
        except:
            pass
    
    def on_ports_detected(self, ports: list):
        """ポート検出後の処理"""
        try:
            # ポート情報パネル更新
            port_info = self.query_one("#port_info_panel", PortInfoPanel)
            port_info.update_port_list()
        except:
            pass
    
    def set_preset_port(self) -> None:
        """プリセットポート設定"""
        preset_port = get_platform_default_port()
        
        try:
            port_input = self.query_one("#port_input", Input)
            port_input.value = preset_port
            self.log_message(self.loc.get("preset_port_set", preset_port))
        except:
            pass
    
    def action_set_preset(self) -> None:
        """プリセットポート設定アクション（キーバインド用）"""
        self.set_preset_port()


class SimpleConnectionPanel(ConnectionPanel):
    """シンプル接続制御パネル（手動入力版）"""
    
    def __init__(self, localization=None, **kwargs):
        # 手動入力モードで初期化
        super().__init__(localization=localization, use_select=False, **kwargs)
    
    def compose(self) -> ComposeResult:
        """パネル構成"""
        yield Label(self.loc.get("port_control"), classes="panel-title")
        
        # ポート入力
        default_port = get_platform_default_port()
        yield Input(
            placeholder=self.loc.get("port_placeholder", default_port), 
            id="port_input", 
            value=default_port
        )
        
        # 接続ボタン
        with Horizontal(classes="button-row"):
            yield Button(self.loc.get("connect"), id="connect_btn", variant="success")
            yield Button(self.loc.get("disconnect"), id="disconnect_btn", variant="error", disabled=True)
        
        # 制御ボタン
        with Horizontal(classes="button-row"):
            yield Button(self.loc.get("detect_ports"), id="detect_ports_btn", variant="default")
            yield Button(self.loc.get("preset"), id="preset_btn", variant="default")


def main():
    """メイン実行関数"""
    # Windows環境でのイベントループポリシー設定
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 言語設定（環境変数やコマンドライン引数から取得可能）
    import os
    language = os.environ.get('DASHBOARD_LANG', 'jp')
    
    # アプリケーション起動
    app = SimpleEnhancedDashboard(language=language)
    app.run()


if __name__ == "__main__":
    main()