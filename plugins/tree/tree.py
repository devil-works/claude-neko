#!/usr/bin/env python3
# tmux ペインで動くディレクトリツリー。選んだパスを tmux バッファに入れるか、Claude のペインへ直接打ち込む
# 使い方: tree.py <Claude の pane id> [起点ディレクトリ]
import curses, os, subprocess, sys

PANE = sys.argv[1] if len(sys.argv) > 1 else ""
ROOT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else ".")
HELP = "↑↓ move  → ← open/close  Enter/右click insert  y copy  a-z jump  . hidden  q quit"

def children(path, hidden):
    try:
        names = os.listdir(path)
    except OSError:
        return []
    names = [n for n in names if hidden or not n.startswith(".")]
    return sorted(names, key=lambda n: (not os.path.isdir(os.path.join(path, n)), n.lower()))

def flatten(path, depth, opened, hidden, out):
    for n in children(path, hidden):
        p = os.path.join(path, n)
        d = os.path.isdir(p)
        out.append((p, depth, d))
        if d and p in opened:
            flatten(p, depth + 1, opened, hidden, out)
    return out

def tmux(*args):
    subprocess.run(["tmux", *args])

def main(scr):
    curses.curs_set(0)
    curses.use_default_colors()
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    curses.init_pair(1, 81, -1)
    curses.init_pair(2, 240, -1)
    curses.init_pair(3, 220, -1)
    DIR, DIM, NOTE = curses.color_pair(1), curses.color_pair(2), curses.color_pair(3)
    opened, hidden, cur, top, msg = {ROOT}, False, 0, 0, ""
    while True:
        rows = flatten(ROOT, 0, opened, hidden, [])
        h, w = scr.getmaxyx()
        body = max(1, h - 2)
        cur = max(0, min(cur, len(rows) - 1))
        top = min(top, cur)
        if cur >= top + body:
            top = cur - body + 1
        scr.erase()
        scr.addnstr(0, 0, ROOT, w - 1, DIR | curses.A_BOLD)
        for i, (p, depth, d) in enumerate(rows[top:top + body]):
            mark = ("▾ " if p in opened else "▸ ") if d else "  "
            line = "  " * depth + mark + os.path.basename(p) + ("/" if d else "")
            attr = (DIR if d else 0) | (curses.A_REVERSE if top + i == cur else 0)
            try:
                scr.addnstr(1 + i, 0, line.ljust(w - 1), w - 1, attr)
            except curses.error:
                pass
        try:
            scr.addnstr(h - 1, 0, msg or HELP, w - 1, NOTE if msg else DIM)
        except curses.error:
            pass
        msg = ""
        ch = scr.getch()
        p, _, d = rows[cur] if rows else (ROOT, 0, True)
        if ch == ord("q"):
            break
        elif ch in (curses.KEY_UP, ord("k")):
            cur -= 1
        elif ch in (curses.KEY_DOWN, ord("j")):
            cur += 1
        elif ch in (curses.KEY_RIGHT, ord("l"), ord(" ")) and d:
            opened.symmetric_difference_update({p})
        elif ch in (curses.KEY_LEFT, ord("h")):
            if d and p in opened:
                opened.discard(p)
            else:
                parent = os.path.dirname(p)
                cur = next((i for i, r in enumerate(rows) if r[0] == parent), cur)
        elif ch == ord("."):
            hidden = not hidden
        elif ch in (curses.KEY_ENTER, 10, 13):
            tmux("send-keys", "-t", PANE, "-l", p + " ")
            msg = "inserted: " + p
        elif ch == ord("y"):
            tmux("set-buffer", "--", p)
            msg = "copied (prefix+] to paste): " + p
        elif 0x20 < ch < 0x7F and rows:
            # 押した文字で始まる名前へジャンプ (現在位置の次から探し、末尾まで無ければ先頭に戻る)
            c = chr(ch).lower()
            order = list(range(cur + 1, len(rows))) + list(range(0, cur + 1))
            cur = next((i for i in order if os.path.basename(rows[i][0]).lower().startswith(c)), cur)
        elif ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, b = curses.getmouse()
            except curses.error:
                continue
            row = top + my - 1
            if 0 <= row < len(rows):
                cur = row
                p, _, d = rows[cur]
                if b & curses.BUTTON1_DOUBLE_CLICKED and d:
                    opened.symmetric_difference_update({p})
                elif b & (curses.BUTTON3_PRESSED | curses.BUTTON3_CLICKED | curses.BUTTON3_RELEASED):
                    tmux("send-keys", "-t", PANE, "-l", p + " ")
                    msg = "inserted: " + p

curses.wrapper(main)
