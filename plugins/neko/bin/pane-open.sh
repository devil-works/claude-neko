#!/bin/bash
# SessionStart: tmux 内なら Claude のペインの下に猫ペインを開く
# stdin の hook JSON から session_id を取り、その猫だけを表示する (既にあれば新しい session_id で起動し直す)
[ -n "$TMUX_PANE" ] || exit 0
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
SID="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("session_id",""))' 2>/dev/null)"
CMD="python3 $ROOT/neko.py $SID"
OLD="$(tmux list-panes -t "$TMUX_PANE" -F '#{pane_id} #{pane_start_command}' | awk '/neko.py/{print $1; exit}')"
if [ -n "$OLD" ]; then
  tmux respawn-pane -k -t "$OLD" "$CMD"
else
  tmux split-window -d -t "$TMUX_PANE" -v -l 6 "$CMD"
fi
