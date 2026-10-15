# ktakaki0805.github.io

[Quarto](https://quarto.org/) で書き出す静的サイトです。`main` に push すると、GitHub Actions がサイトを書き出して GitHub Pages に公開します。

## 手元で確認する

開発環境は [mise](https://mise.jdx.dev/) で用意します。Quarto・Python・[uv](https://docs.astral.sh/uv/) の版は `mise.toml` に書いてあり、GitHub Actions も同じ版を使います。

```sh
mise install              # Quarto 1.10.19、Python 3.13、uv を入れる
mise run preview          # 下書き（draft: true）も含めてプレビュー
mise run preview-public   # 公開される記事だけでプレビュー（quarto preview）
mise run render           # _site/ に書き出す
```

各タスクは `uv run` を通して Quarto を動かします。記事の中で実行する Python のパッケージ（Jupyter、NumPy、matplotlib など）は `pyproject.toml` と `uv.lock` に書いてあり、`uv run` が `.venv/` に自動でそろえます。

Quarto・Python・uv の版を上げるときは、`mise.toml` の数字を書き換えて `mise install` します。

## 記事を書く

`posts/<日付>/index.qmd` を作ります。図や文献のファイルは同じフォルダに置きます。同じ日に2本目の記事を書くときは、`posts/2026-10-08-2/` のように番号を付けます。

```
posts/2026-10-08/
  index.qmd           記事  → /posts/2026-10-08/
  references.bib      この記事で引用する文献
  gp-regression.svg   図
```

```yaml
---
title: "記事のタイトル"
subtitle: "一覧にも出る副題"          # 省略可
date: 2026-10-08
categories: [機械学習, ガウス過程]     # タグ
bibliography: references.bib          # 文献を引用する記事だけ
summary: |                            # 省略可。見出しの下に「要旨」として出る
  要旨の本文。$\mathcal{O}(n^3)$ のような数式や @titsias2009 のような引用も書ける。
draft: true                           # 下書き。公開するときに消す
---
```

一覧やタグのページでは、タイトルと副題は文字だけで表示します（`*` や `$` などの記号は取り除きます）。副題に数式を入れたいときは `𝒪(𝑛³)` のように Unicode の文字で書いてください。

### 使える書き方

| 要素 | 書き方 | 表示 |
|:--|:--|:--|
| 見出し | `## 実装 {#sec-impl}` | 自動で番号が付く（`{#sec-…}` は参照用、省略可） |
| 数式 | `$x^2$`、`$$ … $$ {#eq-elbo}` | MathJax v4（STIX Two）で組む。ラベルを付けた式に番号が付く |
| 図 | `![キャプション](plot.svg){#fig-gp}` | 本文幅の図。キャプションは右の欄に出る |
| 表 | パイプ表の下に `: キャプション {#tbl-cmp}` | 本文幅で、上下に太い罫を引いた学術論文風の表。列幅は中身に合わせて自動で決まる |
| 相互参照 | `@sec-impl`、`@fig-gp`、`@tbl-cmp`、`@eq-elbo` | 第4節、図1、表1、式 (3) |
| 文献の引用 | `@titsias2009`、`[@rasmussen2006]`、`[@a; @b]` | Titsias (2009)、(Rasmussen & Williams, 2006)。参考文献は記事の末尾に APA 形式で並ぶ |
| 脚注 | `本文[^1]` と `[^1]: 注` | 広い画面では本文の横に傍注として出る |
| コード | ```` ```{.python filename="a.py" code-line-numbers="true"} ```` | ファイル名・言語名・行番号・コピーボタン付き |
| Mermaid | ```` ```{mermaid} ```` と `%%| label: fig-flow`、`%%| fig-cap: …` | 書体と色はサイトに合わせる。ダークモードにも追従 |
| 命題・証明 | `::: {#prp-name}` … `:::`、`::: {.proof}` … `:::` | 命題1、証明（定理は `#thm-`、補題は `#lem-`、定義は `#def-`） |
| 注記 | `::: {.callout-note}`、`::: {.callout-warning}` | 薄い地色の囲み |
| 強調 | `*強調*` | 和文は傍点、欧文はイタリック |

文献は記事ごとに、記事のフォルダの `references.bib` に書き、front matter の `bibliography: references.bib` で読み込みます。タイトルは文頭だけを大文字にし（sentence case）、固有名詞は `{G}aussian` のように波括弧で守ります。

図は、線や文字の色を CSS の `@media (prefers-color-scheme: dark)` で切り替える SVG にすると、ダークモードでも読みやすくなります（`posts/2026-10-08/gp-regression.svg` が例です）。PNG などの画像は、ダークモードでは明るさを少し落として表示します。

図や表は本文の幅に収め、右の欄（傍注・キャプション）にははみ出させません。Mermaid の図は本文の幅（最大 680px）に合わせて縮むので、横に長いフローチャートで文字が小さくなるときは、ラベルを `<br>` で折り返し、`%%{init: …}%%` で文字の大きさと間隔を指定します（`posts/2026-10-08/index.qmd` の図2が例です）。

### コードを実行する記事

記事の中で Python を実行する場合（```` ```{python} ````）は、front matter に `jupyter: python3` を書きます。手元で `mise run preview` か `mise run render` をしてから、`_freeze/` フォルダもコミットします。GitHub Actions では計算をやり直さず、その結果を使います。記事を単体で書き出す（`uv run quarto render posts/<記事>/index.qmd`）と、`_freeze/` があってもコードを実行し直します。

- パッケージを足すときは `uv add <名前>`（例：`uv add scipy`）を実行し、`pyproject.toml` と `uv.lock` をコミットします。
- 図の中の日本語には、システムの日本語フォント（Noto Sans CJK JP、ヒラギノなど）を使います。Ubuntu では `sudo apt install fonts-noto-cjk` で入ります。フォントを入れたあとも図の日本語が「□」になるときは、matplotlib のフォントのキャッシュ（`~/.cache/matplotlib/fontlist-*.json`）を消してから書き出し直します。

## 公開する

1. このフォルダを GitHub のリポジトリに push します。

   ```sh
   git init -b main
   git add -A
   git commit -m "ブログの初期構成"
   git remote add origin git@github.com:<ユーザー名>/<リポジトリ名>.git
   git push -u origin main
   ```

2. リポジトリの **Settings → Pages → Build and deployment → Source** を **GitHub Actions** にします。
3. 以後は `main` に push するたびに `.github/workflows/publish.yml` が動き、mise で Quarto を入れて書き出し、公開します。

公開先の URL を変えたときは、`_quarto.yml` の `site-url` も直します（RSS などの URL に使います）。

## ファイルの構成

```
mise.toml                 開発環境（Quarto・Python・uv の版）とよく使うコマンド
pyproject.toml / uv.lock  記事の中で実行する Python のパッケージ
_quarto.yml               サイト全体の設定（ナビ、言語、数式、引用の形式など）
index.qmd                 トップ（記事一覧）
tags/index.qmd            タグ一覧（URL は /tags/）
posts/                    記事（記事ごとのフォルダに index.qmd・図・references.bib）。posts/_metadata.yml は全記事に共通の設定
styles/blog.scss          デザイン（書体、色、版面、ダークモード）
_templates/               記事の見出しブロックと、一覧・タグのテンプレート
filters/                  「図1」「式 (3)」「第4節」などの表記を整える処理と、読了目安の計算
assets/                   数式の設定、favicon、APA 形式の引用スタイル
_quarto-drafts.yml        下書きも表示するための設定（--profile drafts）
_quarto-production.yml    本番だけの設定（Google Analytics）。GitHub Actions が QUARTO_PROFILE=production で読み込む
```

色や書体は `styles/blog.scss` の先頭にまとめてあります。ライトとダークの色は `:root` と `@media (prefers-color-scheme: dark)` の CSS 変数で指定しています。
