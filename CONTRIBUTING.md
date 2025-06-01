# Contributing to Modern Serial Communication

このプロジェクトに貢献していただき、ありがとうございます！

## 🚀 クイックスタート

### 開発環境のセットアップ

```bash
# 1. リポジトリをフォーク・クローン
git clone https://github.com/superdoccimo/modern-serial-communication.git
cd modern-serial-communication

# 2. 仮想環境作成（推奨）
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. 依存関係インストール
pip install -r requirements.txt

# 4. 動作確認
python port_checker.py
python serial_dashboard.py
```

## 📁 プロジェクト構成

```
modern-serial-communication/
├── serial_dashboard.py      # メインダッシュボードアプリ
├── modern_serial_comm.py    # コアシリアル通信ライブラリ
├── port_checker.py          # ポート検出ユーティリティ
├── test_data_sender.py      # テスト用データ送信ツール
├── requirements.txt         # Python依存関係
├── serial_config.ini        # 設定ファイル（自動生成）
├── setup.py                # pip パッケージ設定
├── LICENSE                 # MITライセンス
├── README.md               # メインドキュメント（英語）
├── README-ja.md            # 日本語ドキュメント
└── CONTRIBUTING.md         # このファイル
```

## 🔧 主要コンポーネント

### 1. `modern_serial_comm.py` - コアライブラリ
- `SerialConfig`: INI設定管理
- `SerialLogger`: JSON Lines ログ出力
- `ModernSerialComm`: メイン通信クラス

### 2. `serial_dashboard.py` - TUIダッシュボード
- `SerialStats`: 統計情報表示
- `ConnectionPanel`: 接続制御UI
- `SendPanel`: データ送信UI
- `SerialDashboard`: メインアプリケーション

### 3. `port_checker.py` - ポート検出
- 利用可能シリアルポート一覧
- 接続テスト機能
- 設定ファイル自動生成

### 4. `test_data_sender.py` - テストツール
- 様々なデータパターン送信
- ダッシュボード動作確認用

## 🐛 バグレポート

バグを見つけた場合は、以下の情報と共にIssueを作成してください：

```markdown
## 環境情報
- OS: Windows 10 / macOS 13 / Ubuntu 20.04
- Python version: 3.9.7
- 関連ハードウェア: COM1, USB-シリアル変換器など

## 再現手順
1. `python serial_dashboard.py` を実行
2. COM1 に接続を試行
3. エラーが発生

## 期待される動作
正常に接続できる

## 実際の動作
接続エラーが発生

## エラーメッセージ
```
Connection failed: ...
```

## ログファイル
serial_log.jsonl の関連部分を添付
```

## 💡 機能提案

新機能のアイデアがあれば、以下のテンプレートでIssueを作成してください：

```markdown
## 機能概要
WebSocket出力機能

## 背景・課題
ブラウザからリアルタイムでシリアルデータを監視したい

## 提案する解決策
WebSocketサーバーを追加し、受信データをブロードキャスト

## 代替案
HTTP APIでのポーリング

## 追加情報
参考実装：...
```

## 🔀 プルリクエスト

### ブランチ戦略
- `main`: 安定版
- `develop`: 開発版
- `feature/xxx`: 新機能
- `bugfix/xxx`: バグ修正

### プルリクエストの手順

1. **Issueの作成** (任意だが推奨)
2. **ブランチ作成**
   ```bash
   git checkout -b feature/websocket-output
   ```

3. **開発・テスト**
   ```bash
   # 変更を実装
   # 動作確認
   python serial_dashboard.py
   ```

4. **コミット**
   ```bash
   git add .
   git commit -m "Add WebSocket output feature

   - Add WebSocketServer class
   - Broadcast received data to connected clients
   - Update configuration for WebSocket settings
   
   Fixes #123"
   ```

5. **プッシュ・プルリクエスト作成**
   ```bash
   git push origin feature/websocket-output
   ```

### コミットメッセージ規約

```
タイプ: 簡潔な説明

詳細な説明（必要に応じて）

- 変更点1
- 変更点2

Fixes #issue_number
```

**タイプ**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: フォーマット、セミコロンなど
- `refactor`: リファクタリング
- `test`: テスト追加
- `chore`: ビルド、設定など

## 🧪 テスト

### 手動テスト手順

1. **基本接続テスト**
   ```bash
   python port_checker.py
   # 利用可能ポートを確認
   ```

2. **ダッシュボードテスト**
   ```bash
   python serial_dashboard.py
   # 1. 接続テスト
   # 2. データ受信確認
   # 3. CSV出力テスト
   ```

3. **データ送信テスト**
   ```bash
   python test_data_sender.py
   # 1. 通常テスト
   # 2. 大量データテスト
   ```

### 自動テスト（今後追加予定）

```bash
# ユニットテスト
python -m pytest tests/

# 統合テスト
python -m pytest tests/integration/

# カバレッジ
python -m pytest --cov=modern_serial_comm
```

## 📝 コーディング規約

### Python スタイル
- [PEP 8](https://www.python.org/dev/peps/pep-0008/) に準拠
- 行長: 88文字（Black デフォルト）
- docstring: [Google Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)

### 推奨ツール
```bash
# フォーマッター
pip install black
black .

# リンター
pip install flake8
flake8 .

# 型チェック
pip install mypy
mypy .
```

## 🏷️ リリースプロセス

### バージョニング
[Semantic Versioning](https://semver.org/) を使用:
- `1.0.0`: 初回リリース
- `1.0.1`: バグ修正
- `1.1.0`: 新機能追加
- `2.0.0`: 破壊的変更

### リリース手順
1. `develop` → `main` マージ
2. バージョンタグ作成
3. GitHub Release 作成
4. PyPI アップロード（今後）

## 🤝 コミュニティ

### 議論・質問
- GitHub Discussions を使用
- 日本語・英語どちらでも OK

### 行動規範
- 建設的で敬意のあるコミュニケーション
- 技術的な議論に集中
- 初心者を歓迎し、サポート

## 📚 参考資料

### 関連技術
- [Textual Documentation](https://textual.textualize.io/)
- [pySerial Documentation](https://pyserial.readthedocs.io/)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### シリアル通信
- [RS-232 Standard](https://en.wikipedia.org/wiki/RS-232)
- [Virtual Serial Port Tools](https://freevirtualserialports.com/)

ご不明な点があれば、お気軽にIssueやDiscussionでお尋ねください！