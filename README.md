# x-offsec-bot

X（旧Twitter）上のオフェンシブセキュリティ情報を日次で収集し、GitHub Pages向け静的サイトを生成するボットです。

## ローカル実行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/feedback_update.py
python scripts/collect.py --max-results 80
python scripts/normalize.py
python scripts/dedupe_rank.py --top-n 30
python scripts/summarize.py --max-preview 20
python scripts/build_site.py
```

生成物:
- `data/daily/final_latest.json`
- `data/daily/YYYY-MM-DD.json`
- `docs/index.html`

## 必要なSecrets

- `X_BEARER_TOKEN`（設定するとX APIから実データ収集。未設定時はmockモード）
- `OPENAI_API_KEY`（将来のLLM要約拡張用、現時点では任意）

## フィードバック運用（バックエンドなし）

- `.github/ISSUE_TEMPLATE/post_feedback.yml` で `feedback` Issueを作成。
- Issue本文に `Domain: example.com` を含め、`good` / `noise` ラベルで評価。
- `scripts/feedback_update.py` が日次で `data/config/feedback_rules.json` を更新。
