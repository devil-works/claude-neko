#!/bin/bash
# SessionStart: tmux 内なら Claude のペインの左に全高のツリーペインを開く (既にあれば何もしない)
[ -n "$TMUX_PANE" ] || exit 0
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
tmux list-panes -t "$TMUX_PANE" -F '#{pane_start_command}' | grep -q tree.py && exit 0
tmux split-window -d -f -h -b -t "$TMUX_PANE" -l 40 "python3 $ROOT/tree.py $TMUX_PANE '$PWD'"
