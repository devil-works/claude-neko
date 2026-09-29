#!/usr/bin/env python3
# Claude Code の hook から呼ばれ、猫ペイン用に稼働状態と並列エージェント数を書き出す
# 使い方: busy.py prompt|busy|idle|wait|end|agent_start|agent_stop  (stdin に hook の JSON)
# 子猫 (agents.json) は agent_stop と end でしか消さない。idle/prompt で消すとバックグラウンド実行中の子猫が消えてしまう
import fcntl, json, os, shutil, sys, time

cmd = sys.argv[1] if len(sys.argv) > 1 else "idle"
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
# セッションごとに分ける (複数ウィンドウで猫が混ざらないように)
BASE = os.environ.get("NEKO_DIR") or os.path.expanduser("~/.claude/statusline")
D = os.path.join(BASE, d.get("session_id") or "")
os.makedirs(D, exist_ok=True)
BUSY, AGENTS = D + "/busy.json", D + "/agents.json"

def write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)

def load(path):
    try:
        return json.load(open(path))
    except Exception:
        return {}

with open(D + "/.lock", "w") as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    if cmd in ("prompt", "busy", "idle", "wait", "end"):
        state = "busy" if cmd == "prompt" else ("idle" if cmd == "end" else cmd)
        write(BUSY, {"state": state, "ts": time.time(), "session_id": d.get("session_id", "")})
        if cmd == "end":
            write(AGENTS, {"agents": {}})
            # 自分のセッションと、1 日以上更新のない取り残しを片付ける
            for name in os.listdir(BASE):
                path = os.path.join(BASE, name)
                if os.path.isdir(path) and (path == D or time.time() - os.path.getmtime(path) > 86400):
                    shutil.rmtree(path, ignore_errors=True)
    elif cmd == "agent_start":
        a = load(AGENTS).get("agents", {})
        aid = str(d.get("agent_id") or d.get("agentId") or ("anon-%d" % int(time.time() * 1000)))
        a[aid] = {"type": d.get("agent_type") or d.get("agentType") or "", "ts": time.time()}
        write(AGENTS, {"agents": a})
    elif cmd == "agent_stop":
        a = load(AGENTS).get("agents", {})
        aid = str(d.get("agent_id") or d.get("agentId") or "")
        # 内部エージェント (SubagentStart なし・agent_type 空) の Stop も届くので、知らない id は無視する
        a.pop(aid, None)
        write(AGENTS, {"agents": a})
