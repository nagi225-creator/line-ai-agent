# LINE自動応答AIエージェント

SnsClub LINE公式アカウント用のAI自動応答システムです。  
生成AI（GPT-4）を活用し、顧客一人ひとりにパーソナライズされた対話を実現します。

## 🔗 Lステップとの連携

このシステムは **Lステップと共存** する設計です。

```
┌─────────────────────────────────────────────────────────┐
│                    LINE公式アカウント                      │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                      Lステップ                            │
│  ・顧客管理、タグ付け                                       │
│  ・リッチメニュー                                          │
│  ・セグメント配信                                          │
│  ・「AI対話モード」タグで切り替え                            │
└─────────────────────────────────────────────────────────┘
                           │
              「AI対話モード」タグがある顧客のみ
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   AIエージェント                          │
│  ・1対1の自然言語対話                                      │
│  ・パーソナライズ応答                                       │
│  ・ペルソナ自動判定 → Lステップにタグ同期                    │
│  ・人間へのハンドオフ                                       │
└─────────────────────────────────────────────────────────┘
```

## 🎯 主な機能

- **自然言語対話**: 顧客からの自由なメッセージに対し、文脈を理解した自然な応答を生成
- **パーソナライズ応答**: 顧客の職業、興味、課題に基づいた最適な情報提供
- **ペルソナ自動判定**: 会話内容から顧客のペルソナを自動的に推定
- **ナレッジベース連携**: 成功事例やFAQを活用した説得力のある対話
- **会話履歴管理**: 過去の会話を記憶し、継続性のある対話を実現
- **Lステップ連携**: タグ・カスタムフィールドの双方向同期
- **人間へのハンドオフ**: クレームや特別対応が必要な場合にスタッフに転送

## 📁 プロジェクト構成

```
インサイドセールスAI/
├── main.py                 # FastAPIメインアプリケーション
├── config.py               # 設定管理
├── requirements.txt        # 依存パッケージ
├── .env.example           # 環境変数テンプレート
├── app/
│   ├── __init__.py
│   ├── models.py          # データモデル定義
│   ├── database.py        # データベース管理
│   ├── knowledge_base.py  # ナレッジベース管理
│   ├── persona_analyzer.py # ペルソナ分析
│   ├── ai_engine.py       # OpenAI連携・応答生成
│   ├── line_handler.py    # LINE Webhook処理
│   └── lstep_client.py    # Lステップ API連携
├── data/
│   ├── knowledge/
│   │   ├── success_cases.json  # 成功事例
│   │   └── faq.json           # FAQ
│   └── database.db            # SQLiteデータベース
└── prompts/
    └── system_prompt.txt      # AIシステムプロンプト
```

## 🚀 セットアップ

### 1. 依存パッケージのインストール

```bash
cd インサイドセールスAI
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env` ファイルを編集し、以下の値を設定：

```env
# LINE Messaging API
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token
LINE_CHANNEL_SECRET=your_channel_secret

# OpenAI API
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview

# Lステップ連携（任意）
LSTEP_API_KEY=your_lstep_api_key
LSTEP_ACCOUNT_ID=your_lstep_account_id
LSTEP_AI_MODE_TAG=AI対話モード
```

### 3. LINE Developersの設定

1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. Messaging APIチャネルを作成
3. チャネルアクセストークンとチャネルシークレットを取得
4. Webhook URLを設定: `https://your-domain.com/webhook`
5. Webhookの利用をONに設定

### 4. Lステップの設定

1. Lステップの管理画面 > 設定 > API設定 からAPIキーを取得
2. AI対話を有効にしたい顧客に「AI対話モード」タグを付与
3. このタグが付いた顧客にのみAIが応答します

### 4. アプリケーションの起動

```bash
python main.py
```

または

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 開発用エンドポイント

| エンドポイント | メソッド | 説明 |
|:---|:---|:---|
| `/` | GET | ヘルスチェック |
| `/health` | GET | 詳細ヘルスチェック（Lステップ連携状態含む） |
| `/webhook` | POST | LINE Webhook |
| `/api/customers/{user_id}` | GET | 顧客情報取得 |
| `/api/customers/{user_id}/messages` | GET | 会話履歴取得 |
| `/api/knowledge/cases` | GET | 成功事例一覧 |
| `/api/knowledge/faqs` | GET | FAQ一覧 |

## 🔄 Lステップとの役割分担

| 機能 | Lステップ | AIエージェント |
|:---|:---:|:---:|
| 顧客管理・タグ付け | ✅ | 📤 同期 |
| リッチメニュー | ✅ | - |
| セグメント配信 | ✅ | - |
| シナリオ配信 | ✅ | - |
| 1対1の自由対話 | - | ✅ |
| ペルソナ自動判定 | 📥 同期 | ✅ |
| 成功事例の紹介 | - | ✅ |
| FAQ応答 | - | ✅ |
| 人間へのハンドオフ | ✅ 通知受信 | ✅ 転送 |

## 📊 ペルソナタイプ

システムは以下の4つのペルソナを自動判定します：

| ペルソナ | 特徴 |
|:---|:---|
| 副業ワーカー | 会社員で副業収入を求めている |
| 子育てママ | 育児と両立できる在宅収入を求めている |
| ビジネスオーナー | 事業の集客にInstagramを活用したい |
| 自己実現チャレンジャー | 新しい可能性に挑戦したい |

## 🗂 ナレッジベースのカスタマイズ

### 成功事例の追加

`data/knowledge/success_cases.json` を編集：

```json
{
  "id": "case_xxx",
  "title": "タイトル",
  "customer_profile": "顧客属性",
  "genre": "ジャンル",
  "initial_situation": "開始時の状況",
  "achievement": "達成した成果",
  "period": "期間",
  "success_points": "成功のポイント",
  "related_personas": ["副業ワーカー"],
  "related_challenges": ["時間が無い"],
  "keywords": ["副業", "会社員"]
}
```

### FAQの追加

`data/knowledge/faq.json` を編集：

```json
{
  "id": "faq_xxx",
  "category": "カテゴリ",
  "question": "質問",
  "answer": "回答",
  "related_personas": ["全て"],
  "keywords": ["キーワード1", "キーワード2"]
}
```

## 🌐 本番デプロイ

### Google Cloud Functions

```bash
gcloud functions deploy line-ai-agent \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars LINE_CHANNEL_ACCESS_TOKEN=xxx,LINE_CHANNEL_SECRET=xxx,OPENAI_API_KEY=xxx
```

### AWS Lambda

```bash
# serverless framework使用
serverless deploy
```

## 📝 ライセンス

Private - SnsClub専用

## 🔗 関連ドキュメント

- [要件定義書](https://github.com/nagiando-byte/line-ai-agent-requirements)
- [LINE Messaging API ドキュメント](https://developers.line.biz/ja/docs/messaging-api/)
- [OpenAI API ドキュメント](https://platform.openai.com/docs/)
