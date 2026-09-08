#!/usr/bin/env python3
# tmux ペインで動くコンテキスト残量猫
# cat.py (statusLine) が書く state.json を読み、使用率に応じて表情・汗・震えが変わる
import curses, json, os, time, random, unicodedata

D = os.environ.get("NEKO_DIR") or os.path.expanduser("~/.claude/statusline")
STATE, BUSY, AGENTS = D + "/state.json", D + "/busy.json", D + "/agents.json"
BATON = [" /", " \\", "♪＼"]
FPS = 8
AGENT_TTL = 3600   # SubagentStop を取りこぼした子猫はこの秒数で消す

# (上限%, 目, 口, ラベル, 色番号, 汗の発生率, 震え幅)
MOODS = [
    (30,  "^ ^", "w", "のんびり",     1, 0.00, 0),
    (50,  "o o", "w", "ちょっと暑い", 2, 0.10, 0),
    (65,  "o o", "~", "汗だく",       3, 0.35, 0),
    (80,  "> <", "~", "つらい...",    4, 0.55, 1),
    (90,  "T T", "o", "泣いてる",     5, 0.75, 1),
    (101, "x x", "O", "限界!!",       6, 0.95, 2),
]
TAIL = ["~", "-", "~", "_"]
THINK = [".", "o", "?", "?", "?", " "]
FLAME = [" ) ( ", " ( ) ", ") ( )", "( ) ("]

def mood_of(used):
    for i, m in enumerate(MOODS):
        if used < m[0]:
            return i, m
    return len(MOODS) - 1, MOODS[-1]

def read_state(cache, path=None):
    path = path or STATE
    try:
        mt = os.path.getmtime(path)
        if mt != cache.get("_mt"):
            with open(path) as f:
                d = json.load(f)
            d["_mt"] = mt
            return d
    except Exception:
        pass
    return cache

def put(win, y, x, s, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        s, x = s[-x:], 0
    s = s[: w - x]
    if not s:
        return
    try:
        win.addstr(y, x, s, attr)
    except curses.error:
        pass

def main(scr):
    curses.curs_set(0)
    scr.nodelay(True)
    curses.use_default_colors()
    if curses.COLORS >= 256:
        cols = [114, 150, 220, 214, 203, 196, 81, 240]
    else:
        cols = [2, 2, 3, 3, 1, 1, 6, 0]
    for i, c in enumerate(cols):
        curses.init_pair(i + 1, c, -1)
    C = lambda i: curses.color_pair(i + 1)
    DROP, DIM = C(6), C(7)

    state = {}
    busy = {}
    agents = {}
    drops = []          # [x, y, 文字]
    frame = 0
    blink_until = 0
    next_blink = time.time() + random.uniform(2, 5)
    last_read = 0
    pos = None          # 猫の x 座標 (float)
    target = None       # 目的地
    pause_until = 0     # 休憩終了時刻
    facing = 1          # 1=右向き -1=左向き

    while True:
        ch = scr.getch()
        if ch in (ord("q"), 27):
            break
        now = time.time()
        if now - last_read > 0.5:
            state = read_state(state)
            busy = read_state(busy, BUSY)
            agents = read_state(agents, AGENTS)
            last_read = now

        h, w = scr.getmaxyx()
        scr.erase()

        has = "used" in state
        used = max(0.0, min(100.0, float(state.get("used", 0)))) if has else 0.0
        size = state.get("size") or 0
        mi, (_, eyes, mouth, label, ci, sweat, trem) = mood_of(used)
        col = C(ci - 1)

        # まばたき (余裕がある時だけ)
        if has and mi <= 2:
            if now >= next_blink:
                blink_until = now + 0.15
                next_blink = now + random.uniform(2, 5)
            if now < blink_until:
                eyes = "- -"
        if not has:
            eyes, mouth, label = "- -", "z", "zzz (待機中)"
            col = DIM

        # 稼働状態: busy=走る / wait=こっちを見る / idle=のんびり散歩
        mode = busy.get("state", "idle") if has else "idle"
        # 子猫はメインのターンが終わっても (mode が idle/wait でも) 走り終わるまで表示する
        n_agents = sum(1 for a in agents.get("agents", {}).values() if now - a.get("ts", 0) < AGENT_TTL) if has else 0
        cw, chh = 10, 4
        min_x = 48 if w > 40 else 0
        max_x = max(min_x, w - cw - 1)
        if pos is None:
            pos = float(max_x)
        pos = max(min_x, min(max_x, pos))
        moving = False
        if mode == "busy" or n_agents:
            # 座って考え中 (目は上を見る) / 子猫がいる間は指揮を続ける
            target = None
            if mi <= 2:
                eyes = "o o" if n_agents else "' '"
        elif mode == "wait":
            target = None
            eyes = "o o"
        else:
            speed = [0.6, 0.45, 0.25, 0.12, 0.05, 0.0][mi]
            if speed > 0 and now >= pause_until:
                if target is None:
                    target = random.randint(min_x, max_x)
                if abs(target - pos) < speed:
                    pos = float(target)
                    target = None
                    pause_until = now + random.uniform(1, 4) * (1 + mi)
                else:
                    facing = 1 if target > pos else -1
                    pos += speed * facing
                    moving = True
        ox = random.randint(-trem, trem) if trem else 0
        cx = int(round(pos)) + ox
        cy = h - chh
        cheek = ";" if mi >= 3 and has else " "
        tail = TAIL[(frame // 3) % len(TAIL)] if mi < 5 else "!"
        step = 4
        legs = '(")_(")' if (not moving or frame % step < step // 2) else '(") (")'
        if facing == 1:
            body = ' %s%s' % (legs, tail)
        else:
            body = '%s%s ' % (tail, legs)
        art = [
            "  /\\_/\\   ",
            " ( %s )  " % eyes,
            " (%s %s %s)  " % (cheek, mouth, cheek),
            body,
        ]
        # 並列エージェントの小猫たち (指揮者の左に整列、交互に跳ねる)
        shown = 0
        for i in range(n_agents):
            ax = cx - 9 * (i + 1)
            if ax < min_x:
                break
            bob = 1 if (frame // 3 + i) % 2 == 0 else 0
            ears = "/\\_/\\" if bob else "/\\-/\\"
            put(scr, cy + 2 - bob, ax, " " + ears, C(0))
            put(scr, cy + 3 - bob, ax, "(=o.o=)", C(0))
            if bob:
                put(scr, cy + 3, ax, "       ")
            shown += 1
        if n_agents > shown:
            put(scr, cy + 3, max(min_x, cx - 9 * (shown + 1)), "+%d" % (n_agents - shown), DIM)

        # 汗の粒: 頭の両脇から湧いて落ちる
        if has and sweat and random.random() < sweat:
            side = random.choice([cx, cx + 8])
            drops.append([side, cy + 1, "'"])
        alive = []
        for d in drops:
            if frame % 2 == 0:
                d[1] += 1
                d[2] = "." if d[2] == "," else ","
            if d[1] < h:
                put(scr, d[1], d[0], d[2], DROP)
                alive.append(d)
        drops = alive[-60:]

        if has and mi == 5:
            put(scr, cy - 1, cx + 2, FLAME[frame % len(FLAME)], C(5) | curses.A_BOLD)
        if mode == "busy" and not n_agents:
            put(scr, cy - 1, cx + 7, THINK[(frame // 4) % len(THINK)], C(0) | curses.A_BOLD)
        if mode == "wait":
            put(scr, cy - 1, cx + 7, "!" if frame % 8 < 6 else " ", C(2) | curses.A_BOLD)
        for i, line in enumerate(art):
            put(scr, cy + i, cx, line, col | (curses.A_BOLD if mi >= 4 and has else 0))
        if n_agents:
            put(scr, cy + 1, cx - 2, BATON[(frame // 2) % len(BATON)], C(2) | curses.A_BOLD)

        # 左側: バーと数値
        if w > 40:
            bw = max(10, min(30, w - cw - 30))
            fill = int(round(used / 100.0 * bw))
            size_s = ("%dM" % (size // 1000000)) if size >= 1000000 else (("%dk" % (size // 1000)) if size else "?")
            put(scr, 0, 1, "context neko", DIM | curses.A_BOLD)
            if n_agents:
                st = ("~ conducting %d agents" % n_agents, C(0))
            else:
                st = {"busy": ("? thinking", C(0)), "wait": ("! waiting for you", C(2))}.get(mode, ("- idle", DIM))
            put(scr, 0, 15, st[0], st[1])
            put(scr, 1, 1, "█" * fill, col)
            put(scr, 1, 1 + fill, "░" * (bw - fill), DIM)
            put(scr, 1, 2 + bw, "%3d%% / %s" % (int(used), size_s), col | curses.A_BOLD)
            put(scr, 2, 1, label, col | curses.A_BOLD)
            put(scr, 2, 2 + sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in label), str(state.get("model", "")), DIM)

        scr.refresh()
        frame += 1
        time.sleep(1.0 / FPS)

if __name__ == "__main__":
    os.environ.setdefault("ESCDELAY", "25")
    curses.wrapper(main)
