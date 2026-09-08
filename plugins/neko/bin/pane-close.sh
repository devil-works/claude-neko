#!/bin/bash
# SessionEnd: 同じウィンドウの猫ペインを閉じる
[ -n "$TMUX_PANE" ] || exit 0
tmux list-panes -t "$TMUX_PANE" -F '#{pane_id} #{pane_start_command}' | awk '/neko.py/{print $1}' | xargs -r -n1 tmux kill-pane -t
