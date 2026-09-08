# Security

このプラグインはあなたの端末で hook としてシェルスクリプトと Python を実行します。
インストール前に何をするかを把握できるよう、挙動をすべて書いておきます。
コードは合計 300 行程度なので、読んで確かめることを勧めます。

## 何をするか

| 対象 | 内容 |
|---|---|
| 実行するもの | `bash`、`python3`（標準ライブラリのみ）、`tmux` |
| 書き込む場所 | `~/.claude/statusline/` 配下の `state.json` / `busy.json` / `agents.json` / `.lock` のみ（`NEKO_DIR` で変更可） |
| tmux 操作 | 自分のウィンドウへのペイン作成・削除、`send-keys` によるプロンプトへのパス挿入、`set-buffer` |
| 読む場所 | tree は起点ディレクトリ配下のファイル名のみ。ファイル内容は読まない |

## 何をしないか

- ネットワークアクセスをしない（`urllib` / `requests` / `curl` などは一切使わない）
- `sudo` や権限昇格をしない
- hook は標準出力に何も書かない。Claude の文脈にテキストを注入する経路を持たない
- `~/.claude/statusline/` 以外のファイルを書き換えない。設定ファイルには触れない
- 外部パッケージをインストールしない。依存は `tmux` と `python3` だけ

`statusLine` 用の `cat.py` は Claude Code が渡す JSON を読み、モデル名とカレントディレクトリを画面下に表示するだけです。

## 改ざん対策

- リリースはタグで行い、タグとコミットは作者の SSH 鍵で署名しています
- `main` ブランチは force-push と削除を禁止し、署名付きコミットのみ受け付けます
- インストール時はタグで固定することを勧めます（README の「バージョンを固定する」を参照）

署名の検証:

```
git clone https://github.com/devil-works/claude-neko
cd claude-neko
git verify-tag v0.1.1
```

作者の署名鍵は GitHub アカウント devil-works に SSH signing key として登録しており、GitHub 上のコミットとタグには Verified バッジが付きます。

## 報告

問題を見つけたら GitHub の Issue か Security Advisory で知らせてください。
