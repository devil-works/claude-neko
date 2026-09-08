#!/usr/bin/env python3
# コンテキスト残量で表情が変わる猫ステータスライン
import json, sys, os, time

try:
    d = json.load(sys.stdin)
except Exception:
    d = {}

cw = d.get("context_window") or {}
used = cw.get("used_percentage")
if used is None:
    cu = cw.get("current_usage") or {}
    size = cw.get("context_window_size") or 0
    tot = sum(cu.get(k, 0) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    used = (tot * 100.0 / size) if size else 0.0
used = max(0.0, min(100.0, float(used)))
size = cw.get("context_window_size") or 0

# tmux ペインの猫 (neko.py) 用に状態を書き出す
try:
    D = os.environ.get("NEKO_DIR") or os.path.expanduser("~/.claude/statusline")
    os.makedirs(D, exist_ok=True)
    st = D + "/state.json"
    tmp = st + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"used": used, "size": size,
                   "model": (d.get("model") or {}).get("display_name") or "",
                   "session_id": d.get("session_id") or "",
                   "ts": time.time()}, f)
    os.replace(tmp, st)
except Exception:
    pass

model = (d.get("model") or {}).get("display_name") or ""
cwd = (d.get("workspace") or {}).get("current_dir") or d.get("cwd") or ""
cwd = cwd.replace(os.path.expanduser("~"), "~")
# 表示は控えめに (猫は neko.py 側)
sys.stdout.write("\033[38;5;245m%s  %s\033[0m" % (model, cwd))
