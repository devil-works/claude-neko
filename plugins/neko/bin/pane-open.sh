#!/bin/bash
# SessionStart: tmux 内なら Claude のペインの下に猫ペインを開く (既にあれば何もしない)
[ -n "$TMUX_PANE" ] || exit 0
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
tmux list-panes -t "$TMUX_PANE" -F '#{pane_start_command}' | grep -q neko.py && exit 0
tmux split-window -d -t "$TMUX_PANE" -v -l 6 "python3 $ROOT/neko.py"
