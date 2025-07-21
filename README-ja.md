# 📡 Modern Serial Communication

**商用シリアル監視ツールの無料・オープンソース代替品**

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![VMware](https://img.shields.io/badge/VMware-supported-orange.svg)

Modern Serial Communicationは、高価な商用ソリューション（$60-200+）に代わる軽量で高機能なPython製シリアルポート監視・通信ツールです。物理環境から仮想環境まで、あらゆる開発シーンに対応します。

## ✨ 特徴

### 🚀 コア機能
- **リアルタイムシリアル監視** - タイムスタンプ付きライブデータ可視化
- **自動ポート検出** - 利用可能なシリアルポートを自動検出・表示
- **複数接続タイプ対応** - 直接シリアルポート、TCPブリッジ、仮想ポート
- **非同期I/O** - ノンブロッキング通信で最適なパフォーマンス
- **完全クロスプラットフォーム** - Windows、Linux、macOSで同一機能

### 🖥️ VMware/仮想環境対応
- **VMwareブリッジ対応** - Host-Guest間シリアル通信
- **設定ファイル自動選択** - プラットフォーム別設定の自動適用
- **診断ツール内蔵** - 接続問題の自動診断・解決提案
- **仮想ポート最適化** - `/dev/ttyS*`、`COM*`の自動判定

### 📊 高度な監視機能
- **ライブデータテーブル** - リアルタイムパケット表示とフィルタリング
- **スパークライングラフ** - データフローの視覚的表現
- **統計分析** - パケット数、スループット、エラーレート分析
- **構造化ログ** - データ分析用JSON Lines形式出力

### 🔧 開発者エクスペリエンス
- **美しいターミナルUI** - Textualによる直感的コンソールインターフェース
- **CSV出力** - データ分析とレポート作成の簡素化
- **INI設定管理** - 環境別設定の簡単管理
- **豊富な診断ツール** - 問題特定から解決まで自動化

## 🎯 商用ツールを超える理由

| 機能 | 商用ツール | Modern Serial Comm |
|------|------------|-------------------|
| **価格** | $60-200+ | **無料・オープンソース** |
| **プラットフォーム** | Windows専用 | **Windows・Linux・macOS** |
| **VM対応** | 複雑な設定必須 | **自動検出・簡単設定** |
| **ポート検出** | 手動入力 | **自動検出・選択UI** |
| **カスタマイズ** | 制限あり | **完全カスタマイズ可能** |
| **診断機能** | 基本的 | **高度な自動診断** |
| **データ出力** | 独自形式 | **CSV・JSON・標準形式** |
| **自動化** | GUI操作のみ | **API・スクリプト対応** |

## 🚀 クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/superdoccimo/modern-serial-communication.git
cd modern-serial-communication

# 依存関係をインストール
pip install -r requirements.txt
```

### 使用方法

#### シンプル版（推奨・安定動作）
```bash
python simple_dashboard.py
```
- ポート自動検出機能
- 安定したUI動作
- 初心者にも最適

#### 高機能版（上級者向け）
```bash
python serial_dashboard.py
```
- 全機能搭載
- 高度なカスタマイズ
- プロフェッショナル用途

### VMware環境での使用

#### 1. VMware設定
1. 仮想マシン設定 → Hardware → Serial Port
2. "Use physical serial port" または "Bridged"を選択
3. Windows Host: COM2, Linux Guest: /dev/ttyS0

#### 2. 両方でダッシュボード起動
```bash
# Windows Host
python simple_dashboard.py
# ポート: COM2

# Linux Guest  
python simple_dashboard.py
# ポート: /dev/ttyS0
```

#### 3. リアルタイム双方向通信テスト
両方のダッシュボードでメッセージ送受信！

### ハイブリッドダッシュボードとリモートクライアント
`hybrid_network_dashboard.py` をホスト側で実行し、別PCから
`remote_client_dashboard.py` を使って接続することで、シリアル通信を
ネットワーク経由で操作できます。

## 📦 プロジェクト構成

```
modern-serial-communication/
├── simple_dashboard.py         # シンプル版ダッシュボード（推奨）
├── serial_dashboard.py         # 高機能版ダッシュボード
├── modern_serial_comm.py       # コアライブラリ
├── async_serial_debug.py       # 診断ツール
├── linux_port_checker.py      # Linux用ポートチェッカー
├── hybrid_network_dashboard.py  # ハイブリッド通信サーバー
├── remote_client_dashboard.py   # リモート接続クライアント
├── serial_config_windows.ini   # Windows用設定
├── serial_config_linux.ini     # Linux用設定
├── requirements.txt            # 依存関係
├── README.md                   # このファイル（英語）
└── README-ja.md               # このファイル（日本語）
```

## 🛠️ 診断・トラブルシューティング

### 自動診断ツール
```bash
# 包括的な診断実行
python async_serial_debug.py

# Linux専用診断
python linux_port_checker.py
```

### よくある問題と解決法

#### 1. Linuxで接続できない
```bash
# 権限確認・修正
sudo usermod -a -G dialout $USER
logout  # 必須：再ログイン
```

#### 2. VMwareで通信できない
- Host側: COM2を使用
- Guest側: /dev/ttyS0を使用
- VMware設定でシリアルポートをブリッジ

#### 3. ポートが見つからない
```bash
# ポート検出ツール実行
python simple_dashboard.py
# 「ポート検出」ボタンをクリック
```

## 🏭 実用的な使用例

### 開発・テスト環境
```bash
# デバイスシミュレーター (Linux)
python simple_dashboard.py
# ポート: /dev/ttyS0

# 制御ソフトウェア (Windows)  
python simple_dashboard.py
# ポート: COM2
```

### 製造業・IoT
- レガシー機器監視
- センサーデータ収集
- 品質管理システム
- プロトコル解析

### 教育・研究
- シリアル通信学習
- プロトコル開発
- データロギング
- システム統合テスト

## 🌟 主要な改善点

### v2.0の新機能
- ✅ **ポート自動検出** - 手動入力不要
- ✅ **VMware完全対応** - 設定から通信まで自動化
- ✅ **診断ツール統合** - 問題の自動特定・解決
- ✅ **プラットフォーム最適化** - OS別設定の自動適用
- ✅ **安定性向上** - エラーハンドリング強化

### 商用ツールにない独自機能
- 🚀 **シンプル版UI** - 学習コストゼロ
- 🚀 **VMware診断** - 仮想環境専用トラブルシューティング
- 🚀 **双方向テスト** - 同一ツールでHost-Guest通信
- 🚀 **オープンソース** - 完全カスタマイズ可能

## 📋 システム要件

- **Python**: 3.8以上
- **OS**: Windows 10+, Linux (Ubuntu 20.04+), macOS 10.15+
- **メモリ**: 最小256MB、推奨512MB
- **仮想環境**: VMware Workstation/Player, VirtualBox対応

### 依存関係
```txt
pyserial>=3.5
pyserial-asyncio>=0.6
textual>=0.1.18
rich>=10.0.0
```

## 🚧 ロードマップ

### v2.1 (近日リリース)
- [ ] Web UI版追加
- [ ] MQTT/IoT対応
- [ ] プロトコルデコーダー
- [ ] マルチポート同時監視

### v3.0 (計画中)
- [ ] AI支援診断
- [ ] クラウド連携
- [ ] モバイルアプリ
- [ ] エンタープライズ機能

## 📖 解説・チュートリアル

### 解説ページ
- [Modern Serial Communication 詳細解説](https://minokamo.tokyo/2025/06/03/9050/)
- [実践的な使い方とトラブルシューティング](https://minokamo.tokyo/2025/06/05/9063/)

### Youtube動画
- [Modern Serial Communication デモンストレーション](https://youtu.be/IJkWY9RMJFo)

## 🤝 貢献・サポート

### コントリビューション歓迎
1. **Issue報告** - バグや要望をお気軽に
2. **Pull Request** - 機能追加や改善
3. **ドキュメント** - 使用例や翻訳
4. **テスト** - 環境別動作確認

### エンタープライズサポート
- カスタム開発
- 導入コンサルティング
- 保守サポート
- トレーニング

**[📧 お問い合わせ](mailto:github@minokamo.xyz)**

## 📄 ライセンス

MIT License - 商用利用・改変・再配布自由

## 🙏 謝辞

- [Textual](https://github.com/Textualize/textual) - 美しいTUI
- [PySerial](https://github.com/pyserial/pyserial) - 信頼性の高いシリアル通信
- オープンソースコミュニティの皆様

---

**[⭐ GitHubでスター](https://github.com/superdoccimo/modern-serial-communication)** をお願いします！

**役に立ったら[スポンサー](https://github.com/sponsors/yourusername)として応援してください 💖**

### 📸 スクリーンショット

#### シンプル版ダッシュボード
```
📡 Simple Enhanced Serial Dashboard — Auto-detect ports & Cross-platform
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🔌 ポート選択               ┃                                                                        ┃
┃ ┌─────────────────────────┐ ┃ 時刻      方向  データ                              長さ              ┃  
┃ │/dev/ttyS0              │ ┃ 22:30:15  📥RX  Hello from Windows!               18                 ┃
┃ └─────────────────────────┘ ┃ 22:30:16  📤TX  Hello from Linux!                 17                 ┃
┃ [🟢接続] [🔴切断] [🔍検出]  ┃ 22:30:17  📥RX  VMware test successful           22                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 💡 なぜModern Serial Communicationなのか？

**業界の課題**:
- 商用ツールは高価（$60-200+）
- Windows専用で制約が多い
- VMware環境での設定が複雑
- カスタマイズが困難

**私たちの解決策**:
- ✅ 完全無料・オープンソース
- ✅ 真のクロスプラットフォーム対応
- ✅ VMware環境への最適化
- ✅ 無制限のカスタマイズ性

**結果**: プロフェッショナルグレードの機能を、誰でも無料で利用可能に！
