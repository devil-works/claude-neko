# claude-neko

Claude Code を tmux で飼うための 2 つのプラグイン。

- **neko** — コンテキスト残量で表情が変わる猫。`claude` を起動すると下ペインに自動で現れ、作業中は動き、サブエージェントが走ると子猫が並ぶ
- **tree** — 左ペインのディレクトリツリー。`Enter` / 右クリックで選んだパスを Claude のプロンプトへ挿入、`y` で tmux バッファへコピー

依存は tmux と python3（標準ライブラリのみ）。Linux / macOS / WSL で動く。tmux の中で `claude` を起動することが前提で、tmux が無い環境ではペインは開かない。

このプラグインは hook としてあなたの端末でスクリプトを実行する。何をして何をしないかは [SECURITY.md](SECURITY.md) にまとめてある。

## インストール

Claude Code 内で:

```
/plugin marketplace add devil-works/claude-neko
/plugin install neko@claude-neko
/plugin install tree@claude-neko
```

### バージョンを固定する

`main` の最新を追いたくない場合は、`~/.claude/settings.json` でタグを指定して登録する。以後の更新は自分でタグを上げるまで取り込まれない。

```json
{
  "extraKnownMarketplaces": {
    "claude-neko": {
      "source": {"source": "github", "repo": "devil-works/claude-neko", "ref": "v0.1.1"}
    }
  }
}
```

タグとコミットは作者の SSH 鍵で署名してある。`git verify-tag v0.1.1` で検証できる。

### statusLine の設定（neko に必要）

猫はステータスライン用スクリプト `cat.py` が書き出す状態ファイルを読む。statusLine はプラグインから登録できないため、`~/.claude/settings.json` に追加する。

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/plugins/marketplaces/claude-neko/plugins/neko/cat.py",
    "padding": 0
  }
}
```

`cat.py` 自体はモデル名とカレントディレクトリを控えめに表示するだけ。

### tmux の外から起動する場合

`bin/claude-neko` を PATH に置くと、tmux セッションを作って `claude` を起動する。引数はそのまま `claude` に渡る。

```
ln -s ~/.claude/plugins/marketplaces/claude-neko/bin/claude-neko ~/.local/bin/claude-neko
claude-neko --resume
```

すでに tmux の中なら何もいらない。`claude` と打つだけでペインが揃う。

## 状態ファイル

`~/.claude/statusline/` に `state.json` / `busy.json` / `agents.json` を書く。環境変数 `NEKO_DIR` で場所を変えられる。

## 開発

ローカルのクローンをマーケットプレイスとして登録すると、編集がそのまま反映される。

```
/plugin marketplace add ~/src/claude-neko
```

変更後は `/reload-plugins` か Claude を再起動する。

## ライセンス

MIT
