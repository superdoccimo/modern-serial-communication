# 📡 Modern Serial Communication

**商用シリアル監視ツールの無料・オープンソース代替品**

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

Modern Serial Communicationは、高価な商用ソリューションに代わる軽量で高機能なPython製シリアルポート監視・通信ツールです。レガシーシリアル機器を扱う開発者、エンジニア、研究者に最適です。

## ✨ 特徴

### 🚀 コア機能
- **リアルタイムシリアル監視** - タイムスタンプ付きライブデータ可視化
- **複数接続タイプ対応** - 直接シリアルポート、TCPブリッジ、仮想ポート
- **非同期I/O** - ノンブロッキング通信で最適なパフォーマンス
- **クロスプラットフォーム** - Windows、Linux、macOSで動作

### 📊 高度な監視機能
- **ライブデータテーブル** - リアルタイムパケット表示とフィルタリング
- **スパークライングラフ** - データフローの視覚的表現
- **統計分析** - パケット数、スループット、タイミング分析
- **構造化ログ** - データ分析用JSON Lines形式

### 🔧 開発者フレンドリー
- **ターミナルUI（TUI）** - Textualによる美しいコンソールインターフェース
- **CSV出力** - 簡単なデータ分析とレポート作成
- **設定可能** - INI形式の設定管理
- **プラグイン対応** - カスタムプロトコル用の拡張可能アーキテクチャ

### 🌐 エンタープライズ機能
- **VM対応** - 仮想マシン環境用TCPブリッジ
- **MQTT対応** - IoTダッシュボード統合（開発中）
- **WebSocket出力** - ブラウザベース監視（開発中）
- **REST API** - プログラマティックアクセスと自動化

## 🎯 商用ツールより優れている理由

| 機能 | 商用ツール | Modern Serial Comm |
|------|------------|-------------------|
| **価格** | $60-200+ | **無料・オープンソース** |
| **プラットフォーム** | Windows専用 | **クロスプラットフォーム** |
| **カスタマイズ** | 制限あり | **無制限** |
| **自動化** | GUI のみ | **API + スクリプト** |
| **VM対応** | 複雑な設定 | **内蔵TCPブリッジ** |
| **データ出力** | 独自形式 | **標準形式** |

## 🚀 クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/superdoccimo/modern-serial-communication.git
cd modern-serial-communication

# 依存関係をインストール
pip install -r requirements.txt

# ダッシュボードを実行
python serial_dashboard.py
```

### 基本的な使用方法

1. **ダッシュボード起動**
   ```bash
   python serial_dashboard.py
   ```

2. **シリアルポートに接続**
   - ポート名を入力（例：`COM1`, `/dev/ttyUSB0`）
   - 緑色の接続ボタンをクリック
   - データ監視開始！

3. **VM環境の場合**
   - TCPブリッジを使用：`socket://host:port`
   - 例：`socket://localhost:5000`

### コマンドライン操作

- `q` - アプリケーション終了
- `c` - 全データクリア
- `s` - データをCSVに保存
- `r` - 記録の開始/停止

## 📋 要件

- Python 3.8+
- pyserial
- pyserial-asyncio
- textual
- rich

## 🔧 設定

`serial_config.ini`ファイルで設定を管理：

```ini
[SERIAL]
port = COM1
baudrate = 9600
bytesize = 8
parity = N
stopbits = 1
timeout = 1.0

[NETWORK]
tcp_host = localhost
tcp_port = 5000
use_tcp = false

[LOGGING]
level = INFO
format = json_lines
output_file = serial_log.jsonl
```

## 🏭 使用例

### 製造業・産業用途
- レガシー機器の監視
- 生産ライン データ収集
- 品質管理システム
- センサーデータ取得

### 開発・テスト
- 組み込みシステムのデバッグ
- プロトコル分析
- デバイステスト
- IoT開発

### 研究・教育
- 実験用データログ
- 学生プロジェクト
- プロトコル学習
- システム統合

## 🌐 VMとリモートアクセス

モダンな開発環境に最適：

### Docker/VM設定
```bash
# ホスト：COMポートをTCPにブリッジ
ncat -l -p 5000 --sh-exec "plink -serial COM7 -sercfg 9600,8n1"

# ゲスト：TCP経由で接続
python serial_dashboard.py
# 使用：socket://host:5000
```

### SSH/リモート開発
- ターミナルベースUIはSSH経由で動作
- GUI依存なし
- 軽量で応答性が良い

## 📦 プロジェクト構成

```
modern-serial-communication/
├── serial_dashboard.py      # メインTUIアプリケーション
├── modern_serial_comm.py    # コアライブラリ
├── port_checker.py          # ポート検出ツール
├── test_data_sender.py      # テストユーティリティ
├── requirements.txt         # 依存関係
├── serial_config.ini        # 設定ファイル
├── README.md               # このファイル（英語）
└── README-ja.md            # このファイル（日本語）
```

## 🚧 ロードマップ

### 短期
- [ ] ブラウザUI用WebSocket出力
- [ ] IoTダッシュボード用MQTT統合
- [ ] カスタムプロトコル用プラグインシステム
- [ ] 高度なフィルタリングと検索

### 長期
- [ ] Webベース GUI オプション
- [ ] データベース統合
- [ ] マルチポート監視
- [ ] プロトコルデコーダー（Modbusなど）

## 🤝 貢献

貢献を歓迎します！以下の方法でご協力ください：

1. リポジトリを**フォーク**
2. 機能ブランチを**作成**
3. 変更を**コミット**
4. ブランチに**プッシュ**
5. プルリクエストを**オープン**

### 開発環境セットアップ

```bash
# フォークをクローン
git clone https://github.com/superdoccimo/modern-serial-communication.git

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windowsの場合：venv\Scripts\activate

# 開発用依存関係インストール
pip install -r requirements.txt

# テスト実行（今後追加予定）
python -m pytest
```

## 📄 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🙏 謝辞

- 美しいTUIのために[Textual](https://github.com/Textualize/textual)を使用
- アクセス可能なオープンソースシリアル通信ツールの必要性にインスパイア
- Pythonシリアル通信コミュニティに感謝

## 💡 なぜこれを作ったのか

多くの開発者やエンジニアがまだレガシーシリアル機器を使用していますが、商用監視ツールは高価で、Windows専用、そして柔軟性に欠けます。私たちは強力なツールが以下であるべきだと信じています：

- **アクセス可能** - 無料でオープンソース
- **モダン** - 現在のベストプラクティスで構築
- **柔軟** - 簡単にカスタマイズ・拡張可能
- **クロスプラットフォーム** - Pythonが動作するあらゆる場所で動作

シリアル通信を誰もがアクセスできるものにする取り組みにご参加ください！

---

**[⭐ このリポジトリにスター](https://github.com/superdoccimo/modern-serial-communication.git)** を付けて、役に立ったら教えてください！

**[📧 お問い合わせ](mailto:summer@minokamo.xyz)** エンタープライズサポートやカスタム開発について。

## 🔍 スクリーンショット

### メインダッシュボード
```
📡 Modern Serial Communication Dashboard — Python-powered real-time monitoring
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🔌 接続制御               ┃                                                                        ┃
┃ ┌─────────────────────────┐ ┃ 時刻      方向  データ                              長さ              ┃
┃ │COM1                     │ ┃ 20:25:46  📥RX  SENSOR,1,29.23,TEMP               16                 ┃
┃ └─────────────────────────┘ ┃ 20:25:47  📥RX  {"id": 2, "timestamp": "2025...   87                 ┃
┃ [🟢接続] [🔴切断]          ┃                                                                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 機能一覧
- ✅ リアルタイムデータ表示
- ✅ 統計情報（パケット数、バイト数、レート）
- ✅ スパークライン（データ量グラフ）
- ✅ CSV出力
- ✅ 構造化ログ
- ✅ キーボードショートカット
- ✅ 接続状態管理