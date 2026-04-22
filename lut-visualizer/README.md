# LUT Interpreter — 特徴量ビジュアライザ

`.cube` 形式の 3D LUT ファイルから抽出した 40 次元特徴量ベクトルを、ブラウザ上でインタラクティブに可視化するツールです。

```
[lut_features モジュール] → features.json → [LUT Interpreter] → ブラウザで可視化
```

---

## 機能

### View A — 散布図（PCA / UMAP）
- 全 LUT を 2 次元に射影してプロット
- **PCA** (高速・決定論的) と **UMAP** (非線形・クラスタ構造を保持) を切り替え可能
- ホイールズームとドラッグパン
- LUT をクリックしてレーダー比較に追加（最大 4 個）
- ホバーで主要特徴量のツールチップ表示

### View B — レーダーチャート
- 選択した LUT を 5 カテゴリのレーダーチャートで比較
  - 色相帯別挙動（hue shift / 彩度変化 / 明度変化）
  - トーン挙動（shadow / midtone / highlight の Lab 変化）
  - グローバル色調（色温度・ティント・彩度・コントラスト）
  - 輝度依存 hue シフト
  - 非線形性指標

### その他
- **URL 状態共有** — 選択中の LUT と射影方法がクエリパラメータに反映される
- **ダーク / ライトテーマ** 切り替え
- **PNG / SVG エクスポート**（"LUT Interpreter" ウォーターマーク付き）

---

## セットアップ

Node.js 20 以上が必要です。

```bash
cd lut-visualizer
npm install
```

---

## ローカル開発

```bash
npm run dev
```

→ `http://localhost:5173` でブラウザが使えます。

---

## テスト・型チェック

```bash
# Vitest でテスト実行
npm test

# TypeScript 型チェック
npx tsc --noEmit

# ビルド確認
npm run build
```

---

## データの更新

`public/data/features.json` は `lut_features` Python モジュールで生成します。  
サンプル LUT を再生成したり、自前の `.cube` ファイルを追加する場合は以下を実行してください。

```bash
# lut_features の Python 環境を使う
cd ../lut_features

# ① サンプル LUT を再生成 (public/data/sample_luts/ に出力)
uv run python ../lut-visualizer/scripts/generate_sample_luts.py

# ② features.json を再生成
uv run python ../lut-visualizer/scripts/export_features.py \
  --lut-dir ../lut-visualizer/public/data/sample_luts/ \
  --out     ../lut-visualizer/public/data/features.json
```

自前の LUT を追加するには `--luts` で個別ファイルを指定するか、`--lut-dir` でディレクトリごと渡せます。

```bash
uv run python ../lut-visualizer/scripts/export_features.py \
  --luts /path/to/my_look.cube /path/to/another.cube \
  --out  ../lut-visualizer/public/data/features.json
```

---

## プロジェクト構成

```
lut-visualizer/
├── public/
│   └── data/
│       ├── features.json          # 特徴量データ (自動生成)
│       └── sample_luts/           # サンプル .cube ファイル
├── scripts/
│   ├── generate_sample_luts.py   # サンプル LUT 生成スクリプト
│   └── export_features.py        # features.json 生成スクリプト
├── src/
│   ├── components/
│   │   ├── scatter/               # View A: 散布図コンポーネント
│   │   ├── radar/                 # View B: レーダーチャートコンポーネント
│   │   └── common/                # 共通 UI コンポーネント
│   ├── hooks/                     # データ取得・射影・URL 状態フック
│   ├── lib/
│   │   ├── projection/pca.ts      # PCA 実装
│   │   ├── colormap.ts            # 選択色パレット
│   │   ├── normalize.ts           # レーダー用正規化
│   │   └── export.ts              # PNG / SVG エクスポート
│   ├── store/useAppStore.ts       # Zustand グローバルステート
│   ├── types/features.ts          # features.json の型定義
│   └── workers/umap.worker.ts     # UMAP 計算 (Web Worker)
└── tests/lib/                     # Vitest ユニットテスト
```

---

## features.json スキーマ

```jsonc
{
  "schema_version": "1.0",
  "generated_at": "2026-04-22T00:15:35Z",
  "feature_schema": {
    "categories": [{ "id": "hue_bands", "label": "色相帯別挙動", "feature_ids": ["..."] }],
    "features":   [{ "id": "hue_band_R_hue_shift", "label": "赤 hueシフト",
                     "unit": "度", "neutral_value": 0.0, "typical_range": [-30.0, 30.0] }]
  },
  "luts": [
    {
      "id": "cinematic_orange_teal",
      "name": "cinematic orange teal",
      "source_path": "...",
      "features": { "hue_band_R_hue_shift": -8.3, "..." : "..." },
      "thumbnail_path": "thumbnails/cinematic_orange_teal.jpg"
    }
  ]
}
```

---

## デプロイ (GitHub Pages)

`develop` または `main` ブランチへの push で自動デプロイされます。

```
https://<org>.github.io/<repo>/
```

手動でトリガーする場合は GitHub Actions タブ →  
**"Deploy Visualizer to GitHub Pages"** → **"Run workflow"**

### GitHub Pages の初期設定（一度だけ）

1. リポジトリ → **Settings** → **Pages**
2. **Source** を **GitHub Actions** に変更
3. **Environments** → `github-pages` → デプロイ許可ブランチに `develop` を追加

---

## 技術スタック

| 役割 | ライブラリ |
|------|-----------|
| UI フレームワーク | React 18 + TypeScript |
| ビルド | Vite 5 |
| スタイリング | Tailwind CSS v3 |
| 散布図 | D3.js v7 |
| レーダーチャート | Recharts |
| 状態管理 | Zustand |
| UMAP | umap-js (Web Worker) |
| エクスポート | html-to-image |
| テスト | Vitest |
