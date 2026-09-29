# -*- coding: utf-8 -*-
"""
Ninja Quest 🥷  (Streamlit, mobile-first battle game for kids 8-15)
Run:  streamlit run app.py
Progress local JSON file (progress.json) me save hota hai.
"""
import copy
import json
import math
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# =====================================================================
# CONFIG  (yahan se timer / ranges / rewards badal sakte ho)
# =====================================================================
TIMER_SECONDS = 15                      # Turbo mode: har question ka countdown
SPEED_SECONDS = 60                      # Lightning round ka time
BREAK_MINUTES = 25                      # itni der baad "break lo" ka pyara reminder
QUEST_BONUS = 20                        # daily quest poora karne par coins
XP_PER_LEVEL = 100
DIFF_MAX = {"Easy": 10, "Medium": 20, "Hard": 30}          # range
DIFF_LABEL = {"Easy": "🟢 Chill", "Medium": "🟠 Pro", "Hard": "🔴 Legend"}
TOPICS = {                              # key: (icon, world ka naam, css class)
    "table": ("🚀", "Rocket Boost", "g-table"),
    "square": ("🟦", "Block Builder", "g-square"),
    "cube": ("🧊", "Ice Fortress", "g-cube"),
    "frac": ("🍕", "Pizza Power", "g-frac"),
}
AVATARS = [("🥷", 1), ("🦊", 1), ("🐼", 1), ("🦁", 1), ("🐯", 2), ("🦄", 3), ("🐲", 5), ("🤖", 7), ("👑", 10)]
RANKS = ["Rookie", "Ninja", "Samurai", "Wizard", "Champion", "Legend"]
PRAISE = ["Boom! 💥", "Zabardast! 🌟", "Superb! 🚀", "Tez ho tum! ⚡", "Kya baat hai! 🎉", "Champion! 🏆"]
OOPS = ["Oops! Agli baar pakka 💪", "Bas thoda sa chook gaye 😅", "Koi baat nahi, hero! 🦸", "Chalo phir se! 🔥"]
IST = timezone(timedelta(hours=5, minutes=30))     # India time
BATTLE_HP = 5                           # monster ko haraane ke liye kitne sahi vaar chahiye
HEARTS = 3                              # hero ke dil (galat par ek kam)
WIN_COINS, WIN_XP = 5, 20               # ladai jeetne ka inaam
MONSTERS = {                            # world: (emoji, naam)
    "table": ("👾", "Alien Bug"), "square": ("🗿", "Brick Golem"), "cube": ("⛄", "Frost Giant"),
    "frac": ("🦖", "Pizza-saurus"), "mixed": ("🐉", "Mystery Dragon"), "mistakes": ("🤖", "Rusty Robot"),
}

DEFAULT_PROG = {
    "name": "", "avatar": "🥷", "xp": 0, "coins": 0,
    "daily": {},        # {"2026-07-01": {"total": 10, "correct": 8}}
    "topics": {t: {"total": 0, "correct": 0, "time": 0.0} for t in TOPICS},
    "mistakes": [],     # galat questions (streak = repair lab me kitni baar sahi)
    "best_streak": 0, "cur_streak": 0, "best_speed": 0,
    "settings": {"daily_goal": 20, "timer_on": False, "sound": True, "difficulty": "Hard"},
    "resume": None,
}

# =====================================================================
# CSS  (mobile-first game look, light background par hamesha readable)
# =====================================================================
CSS = """
#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], .stDeployButton {display:none !important; visibility:hidden !important;}
.stApp {background:linear-gradient(180deg,#ede9fe 0%,#dbeafe 100%); color-scheme:light;}
.block-container {max-width:480px; padding:1rem .9rem 4rem !important;}
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stMarkdownContainer"] *,
.stApp label, .stApp label *, .stApp [data-testid="stWidgetLabel"] *, .stApp summary, .stApp summary *,
.stApp button[data-baseweb="tab"] *, .stApp [data-testid="stCaptionContainer"] * {color:#1e1b4b;}
.stApp input {color:#111 !important; background:#fff !important;}
[data-baseweb="input"], [data-baseweb="base-input"] {background:#fff !important; border-radius:14px !important;}
[data-baseweb="select"] > div {background:#fff !important; color:#111 !important;}
[data-baseweb="select"] * {color:#111 !important;}
.stButton, [data-testid="stFormSubmitButton"] {width:100%;}
.stButton > button, [data-testid="stFormSubmitButton"] > button {
  width:100%; min-height:60px; font-size:20px; font-weight:700; border-radius:18px;
  background:#fff; color:#1e1b4b; border:2px solid #a78bfa; box-shadow:0 3px 0 #a78bfa;}
.stButton > button p, [data-testid="stFormSubmitButton"] > button p {font-size:20px; font-weight:700; color:inherit;}
button[kind="primary"], button[kind="primaryFormSubmit"],
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background:#16a34a !important; border-color:#15803d !important; color:#fff !important; box-shadow:0 4px 0 #15803d !important;}
button[kind="primary"] p, button[kind="primaryFormSubmit"] p,
[data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primaryFormSubmit"] p {color:#fff !important;}
[data-testid="stForm"] {border:none !important; padding:0 !important;}
[data-testid="stNumberInput"] input {font-size:30px !important; height:64px; text-align:center; font-weight:700;}
[data-testid="stNumberInput"] button {display:none !important;}
.st-key-fracbox [data-testid="stHorizontalBlock"] {flex-direction:row !important; flex-wrap:nowrap !important; align-items:center; gap:.4rem;}
.st-key-fracbox [data-testid="stColumn"], .st-key-fracbox [data-testid="column"] {min-width:0 !important; width:auto !important; flex:1 1 0 !important;}
[class*="st-key-card_"] button {min-height:92px; border:none !important; color:#fff !important; box-shadow:0 5px 0 rgba(0,0,0,.28) !important;}
[class*="st-key-card_"] button p {font-size:24px !important; font-weight:800; color:#fff !important;}
[class*="st-key-card_"] button:hover {filter:brightness(1.1); color:#fff;}
.st-key-card_table button {background:linear-gradient(135deg,#f97316,#ef4444) !important;}
.st-key-card_square button {background:linear-gradient(135deg,#3b82f6,#6366f1) !important;}
.st-key-card_cube button {background:linear-gradient(135deg,#06b6d4,#0e7490) !important;}
.st-key-card_frac button {background:linear-gradient(135deg,#ec4899,#a855f7) !important;}
.st-key-card_mixed button {background:linear-gradient(135deg,#f59e0b,#b45309) !important;}
.st-key-card_mistakes button {background:linear-gradient(135deg,#64748b,#1e293b) !important;}
.g-table {background:linear-gradient(135deg,#f97316,#ef4444);}
.g-square {background:linear-gradient(135deg,#3b82f6,#6366f1);}
.g-cube {background:linear-gradient(135deg,#06b6d4,#0e7490);}
.g-frac {background:linear-gradient(135deg,#ec4899,#a855f7);}
.g-mixed {background:linear-gradient(135deg,#f59e0b,#b45309);}
.hero {display:flex; align-items:center; gap:12px; border-radius:22px; padding:14px; margin:4px 0 10px; background:linear-gradient(135deg,#7c3aed,#4f46e5); box-shadow:0 5px 0 #3730a3;}
.hero .av {font-size:46px; line-height:1; background:rgba(255,255,255,.2); border-radius:18px; padding:8px;}
.hero .hi {flex:1; min-width:0;}
.hero .hi b {display:block; font-size:20px;}
.hero .hi span {font-size:13px; opacity:.9;}
.hero .coins {font-size:18px; font-weight:800; background:rgba(255,255,255,.2); border-radius:14px; padding:8px 10px;}
.xpbar {height:12px; border-radius:8px; background:rgba(255,255,255,.3); overflow:hidden; margin:5px 0 2px;}
.xpbar > div {height:100%; background:#facc15; border-radius:8px;}
.stApp .arena, .stApp .arena *, .stApp .hero, .stApp .hero *, .stApp .qcard, .stApp .qcard *, .stApp .res, .stApp .res *, .stApp .mini, .stApp .mini * {color:#fff !important;}
.tiles {display:flex; gap:8px; margin:8px 0;}
.tile {flex:1; background:rgba(255,255,255,.75); border-radius:16px; padding:10px 4px; text-align:center; box-shadow:0 2px 0 rgba(0,0,0,.08);}
.tile b {display:block; font-size:22px;}
.tile span {font-size:12px; opacity:.75;}
.qcard {border-radius:24px; padding:22px 12px; text-align:center; margin:10px 0; box-shadow:0 5px 0 rgba(0,0,0,.25);}
.qcard .qt {font-size:15px; opacity:.95;}
.qcard .qx {font-size:clamp(28px,9vw,44px); font-weight:800; margin-top:6px; word-break:break-word;}
.res {border-radius:20px; padding:16px; text-align:center; font-size:28px; font-weight:800; margin:10px 0;}
.res span {display:block; font-size:18px; font-weight:600; margin-top:6px;}
.res.ok {background:#16a34a;} .res.bad {background:#f97316;} .res.time {background:#d97706;}
.mini {border-radius:12px; padding:8px; text-align:center; font-weight:700; margin:6px 0;}
.mini.ok {background:#16a34a;} .mini.bad {background:#f97316;}
.tip {background:#fef9c3; border-left:5px solid #facc15; border-radius:12px; padding:12px; margin:8px 0; font-size:16px;}
.pop {animation:pop .5s ease-out;}
.shake {animation:shake .5s;}
.flash {position:fixed; inset:0; pointer-events:none; z-index:9998; animation:flash .9s ease-out forwards;}
.flash.green {background:rgba(34,197,94,.45);} .flash.red {background:rgba(249,115,22,.45);}
@keyframes pop {0%{transform:scale(.5);opacity:0} 70%{transform:scale(1.12)} 100%{transform:scale(1);opacity:1}}
@keyframes shake {0%,100%{transform:translateX(0)} 20%{transform:translateX(-12px)} 40%{transform:translateX(12px)} 60%{transform:translateX(-8px)} 80%{transform:translateX(8px)}}
@keyframes flash {0%{opacity:1} 100%{opacity:0}}
.stApp .arena .dmg {color:#facc15 !important;}
.arena {display:flex; align-items:center; justify-content:space-around; gap:6px; border-radius:22px; padding:14px 8px; margin:8px 0; background:linear-gradient(180deg,#312e81,#1e1b4b); box-shadow:0 5px 0 #0f0d2e;}
.arena .side {flex:1; text-align:center; position:relative;}
.arena .big {font-size:54px; line-height:1.1;}
.arena .vs {font-size:26px;}
.arena .hearts {font-size:18px; margin-top:4px;}
.arena .mname {font-size:12px; opacity:.9;}
.hpbar {height:12px; border-radius:8px; background:rgba(255,255,255,.25); overflow:hidden; margin:6px 6px 2px;}
.hpbar > div {height:100%; background:linear-gradient(90deg,#ef4444,#f97316); transition:width .5s;}
.side.hit .big {animation:shake .5s; filter:drop-shadow(0 0 10px #facc15);}
.side.hurt {animation:shake .5s;}
.side.down .big {opacity:.4; transform:rotate(90deg);}
.dmg {position:absolute; top:-8px; right:6px; font-weight:800; font-size:20px; animation:floatup .9s forwards;}
@keyframes floatup {0%{opacity:1;transform:translateY(0)} 100%{opacity:0;transform:translateY(-30px)}}
.st-key-opts [data-testid="stHorizontalBlock"] {flex-direction:row !important; flex-wrap:nowrap !important; gap:.6rem;}
.st-key-opts [data-testid="stColumn"], .st-key-opts [data-testid="column"] {min-width:0 !important; width:auto !important; flex:1 1 0 !important;}
[class*="st-key-opt_"] button {min-height:84px; border:none !important; color:#fff !important; box-shadow:0 5px 0 rgba(0,0,0,.28) !important;}
[class*="st-key-opt_"] button p {font-size:30px !important; font-weight:800; color:#fff !important;}
.st-key-opt_0 button {background:linear-gradient(135deg,#60a5fa,#2563eb) !important;}
.st-key-opt_1 button {background:linear-gradient(135deg,#fb923c,#ea580c) !important;}
.st-key-opt_2 button {background:linear-gradient(135deg,#34d399,#059669) !important;}
.st-key-opt_3 button {background:linear-gradient(135deg,#f472b6,#db2777) !important;}
.timer {font-size:22px; font-weight:800; text-align:center; margin-top:4px;}
.tbar {height:12px; border-radius:8px; background:rgba(0,0,0,.12); overflow:hidden; margin-bottom:6px;}
.tbar > div {height:100%; background:#22c55e; transition:width 1s linear;}
.tbar.low > div {background:#ef4444;}
.ctab {width:100%; border-collapse:collapse; font-size:18px; background:rgba(255,255,255,.7); border-radius:12px;}
.ctab td, .ctab th {padding:8px; text-align:center; border-bottom:1px solid rgba(0,0,0,.1);}
.ctab th {background:rgba(124,58,237,.15);}
.trow {padding:12px; border-radius:16px; background:rgba(255,255,255,.75); margin:6px 0; display:flex; justify-content:space-between; gap:8px; flex-wrap:wrap;}
.trow.weak {background:#ffedd5; border:2px solid #f97316;}
"""


def inject_css():
    st.markdown("<style>" + re.sub(r"\s*\n\s*", " ", CSS) + "</style>", unsafe_allow_html=True)


# =====================================================================
# STORAGE  (progress.json load / save)
# =====================================================================
def progress_path():
    """?u=naam lagane par alag file (progress_naam.json) - cloud par har bachche ke liye alag."""
    uid = re.sub(r"[^a-zA-Z0-9_-]", "", str(st.query_params.get("u", "")))[:20]
    name = f"progress_{uid}.json" if uid else "progress.json"
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def load_progress(path):
    data = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}                      # file nahi hai / kharab hai -> fresh start
    prog = copy.deepcopy(DEFAULT_PROG)
    for k, v in data.items():
        if k in ("settings", "topics") and isinstance(v, dict):
            prog[k].update(v)
        else:
            prog[k] = v
    for t in TOPICS:
        prog["topics"].setdefault(t, {"total": 0, "correct": 0, "time": 0.0})
    return prog


def save_progress():
    ss = st.session_state
    try:
        tmp = ss.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(ss.prog, f, ensure_ascii=False, indent=1)
        os.replace(tmp, ss.path)
    except OSError:
        ss.save_error = True


def S(key):
    """Setting padho."""
    return st.session_state.prog["settings"].get(key, DEFAULT_PROG["settings"][key])


def today_str():
    return datetime.now(IST).strftime("%Y-%m-%d")


def today_counts():
    d = st.session_state.prog["daily"].get(today_str(), {})
    return d.get("correct", 0), d.get("total", 0)


def overall():
    tp = st.session_state.prog["topics"].values()
    total = sum(t["total"] for t in tp)
    correct = sum(t["correct"] for t in tp)
    return total, correct, (correct * 100 // total if total else 0)


def daily_streak():
    """Kitne din lagatar khela (aaj nahi khela to kal se ginti - koi dabav nahi)."""
    daily = st.session_state.prog["daily"]
    d = datetime.now(IST).date()
    if daily.get(d.isoformat(), {}).get("total", 0) == 0:
        d -= timedelta(days=1)
    n = 0
    while daily.get(d.isoformat(), {}).get("total", 0) > 0:
        n += 1
        d -= timedelta(days=1)
    return n


def level_info(xp):
    """(level, rank, xp is level me, next level tak) ."""
    lvl = 1 + xp // XP_PER_LEVEL
    return lvl, RANKS[min(len(RANKS) - 1, (lvl - 1) // 3)], xp % XP_PER_LEVEL


# =====================================================================
# QUESTION GENERATORS  (logic same)
# =====================================================================
TABLE_TIPS = {
    2: "x2 = number ko double karo.",
    3: "x3 = double karo, phir number ek baar aur jodo.",
    4: "x4 = double ka double.",
    5: "x5 = number ka aadha karo aur 10 se guna karo (ya x10 karke aadha).",
    6: "x6 = x5 nikalo, phir number ek baar jodo.",
    7: "x7 = x10 nikalo aur x3 ghatao.",
    8: "x8 = teen baar double karo (x2, x2, x2).",
    9: "x9 = x10 nikalo, phir number ghatao. Jaise 12x9 = 120 - 12 = 108.",
    10: "x10 = number ke aage 0 laga do.",
}
CUBE_LAST = {1: 1, 2: 8, 3: 7, 4: 4, 5: 5, 6: 6, 7: 3, 8: 2, 9: 9, 0: 0}


def gen_table(mx):
    a, b = random.randint(1, mx), random.randint(2, 10)
    return {"topic": "table", "text": f"{a} x {b} = ?", "kind": "num", "answer": a * b,
            "ans_text": str(a * b), "tip": TABLE_TIPS[b]}


def gen_square(mx):
    n = random.randint(1, mx)
    if n % 10 == 5:
        k = n // 10
        tip = f"5 par khatam hone wale square: {k} x {k + 1} = {k * (k + 1)}, uske aage 25 laga do -> {n * n}."
    elif n % 10 == 0:
        tip = f"{n}² = {n // 10}² ke aage 00 = {n * n}."
    elif n <= 10:
        tip = "1 se 10 ke square yaad kar lo (1, 4, 9, 16, 25, 36, 49, 64, 81, 100)."
    else:
        m = (n + 5) // 10 * 10
        d = abs(n - m)
        tip = f"Trick: ({n}+{d}) x ({n}-{d}) + {d}² = {n + d} x {n - d} + {d * d} = {n * n}."
    return {"topic": "square", "text": f"{n}² = ?", "kind": "num", "answer": n * n,
            "ans_text": str(n * n), "tip": tip}


def gen_cube(mx):
    n = random.randint(1, mx)
    ld = n % 10
    tip = (f"{n}³ = {n}² x {n} = {n * n} x {n}. Last digit trick: jis number ka last digit {ld} ho, "
           f"uske cube ka last digit {CUBE_LAST[ld]} hota hai.")
    return {"topic": "cube", "text": f"{n}³ = ?", "kind": "num", "answer": n ** 3,
            "ans_text": str(n ** 3), "tip": tip}


def gen_frac(mx):
    sub = random.choice(["f2p", "pof", "p2f"])
    if sub == "f2p":       # Fraction -> Percentage (Easy me sirf chhote denominators)
        dens = [2, 4, 5, 10] if mx <= 10 else [2, 4, 5, 10, 20, 25]
        den = random.choice(dens)
        num = random.randint(1, den - 1)
        mult = 100 // den
        ans = num * mult
        return {"topic": "frac", "text": f"{num}/{den} = ? %", "kind": "num", "answer": ans,
                "ans_text": f"{ans}%",
                "tip": f"100 / {den} = {mult}. Isliye {num}/{den} = {num} x {mult} = {ans}%."}
    if sub == "pof":       # Percentage of number (answer hamesha poora)
        p = random.randint(1, mx)
        step = 100 // math.gcd(p, 100)
        n = step * random.randint(1, max(1, 200 // step))
        ans = p * n // 100
        return {"topic": "frac", "text": f"{p}% of {n} = ?", "kind": "num", "answer": ans,
                "ans_text": str(ans),
                "tip": f"Pehle 1% nikalo (100 se bhaag): {n}/100 = {n / 100:g}. Phir x {p} = {ans}. (10% = ek zero hatao)"}
    p = random.randint(1, mx)  # Percentage -> Fraction (simplest form)
    g = math.gcd(p, 100)
    a, b = p // g, 100 // g
    tip = (f"{p}% = {p}/100. Upar-neeche {g} se kaato -> {a}/{b}." if g > 1
           else f"{p}% = {p}/100 (pehle se simplest form).")
    return {"topic": "frac", "text": f"{p}% = ? (a/b)", "kind": "frac", "answer": [a, b],
            "ans_text": f"{a}/{b}", "tip": tip}


GENERATORS = {"table": gen_table, "square": gen_square, "cube": gen_cube, "frac": gen_frac}


def make_question(topic, mx):
    return GENERATORS[topic](mx)


def new_question():
    """Naya question banao (pichle se alag)."""
    ss = st.session_state
    mx = DIFF_MAX.get(S("difficulty"), 30)
    q = None
    for _ in range(30):
        if ss.mode == "mistakes":
            ms = ss.prog["mistakes"]
            if not ms:
                q = None
                break
            q = {k: v for k, v in random.choice(ms).items() if k != "streak"}
        elif ss.mode == "speed":
            t = ss.speed["topic"]
            q = make_question(random.choice(list(TOPICS)) if t == "mixed" else t, mx)
        elif ss.mode == "mixed":
            q = make_question(random.choice(list(TOPICS)), mx)
        else:
            q = make_question(ss.topic, mx)
        if q["text"] != ss.last_text:
            break
    ss.q = q
    ss.q_start = time.time()
    ss.answered = False
    ss.result = None
    ss.qid += 1
    ss.options = make_options(q) if q else []
    ss.last_text = q["text"] if q else None
    if ss.mode in ("topic", "mixed", "mistakes") and q:
        ss.prog["resume"] = {"mode": ss.mode, "topic": ss.topic, "q": q, "battle": ss.battle}
    else:
        ss.prog["resume"] = None
    save_progress()


# =====================================================================
# ANSWER CHECKING / REWARDS
# =====================================================================
def is_correct(q, val):
    if q["kind"] == "num":
        return val == q["answer"]
    return list(val) == list(q["answer"])


def make_options(q):
    """4 tap-options: 1 sahi + 3 aisi galat jo sahi jaisi lagti hain."""
    ans = q["answer"]
    if q["kind"] == "num":
        pool = {ans + d for d in (1, -1, 2, -2, 3, -3, 5, -5, 10, -10)}
        r = max(1, round(ans * 0.1))
        pool |= {ans + r, ans - r, ans + 2 * r, ans - 2 * r}
        if len(str(ans)) >= 2:
            pool.add(int(str(ans)[::-1]))              # digits ulte
        pool = sorted(x for x in pool if x >= 0 and x != ans)
        wrong = random.sample(pool, min(3, len(pool)))
        while len(wrong) < 3:
            c = ans + random.randint(1, max(5, ans // 3))
            if c != ans and c not in wrong:
                wrong.append(c)
    else:
        a, b = ans
        cand = [[b, a], [a + 1, b], [a, b + 1], [a * 2, b], [a, b * 2], [a + 1, b + 1],
                [max(1, a - 1), b], [a, max(2, b - 1)]]
        wrong = []
        for n, d in cand:
            if n * b != d * a and [n, d] not in wrong:   # barabar value wale nahi
                wrong.append([n, d])
        random.shuffle(wrong)
        wrong = wrong[:3]
        while len(wrong) < 3:
            n, d = random.randint(1, 9), random.randint(2, 20)
            if n * b != d * a and [n, d] not in wrong:
                wrong.append([n, d])
    opts = wrong + [ans if q["kind"] == "num" else list(ans)]
    random.shuffle(opts)
    return opts


def fmt_option(q, val):
    if q["kind"] == "frac":
        return f"{val[0]}/{val[1]}"
    return f"{val}%" if q["ans_text"].endswith("%") else str(val)





def register_result(q, correct, elapsed):
    """Score, streak, XP, coins, mistakes sab update + save. Reward info return."""
    ss = st.session_state
    prog = ss.prog
    day = prog["daily"].setdefault(today_str(), {"total": 0, "correct": 0})
    day["total"] += 1
    day["correct"] += int(correct)
    t = prog["topics"].setdefault(q["topic"], {"total": 0, "correct": 0, "time": 0.0})
    t["total"] += 1
    t["correct"] += int(correct)
    t["time"] += min(max(elapsed, 0.0), 120.0)
    milestone = False
    if correct:
        prog["cur_streak"] += 1
        prog["best_streak"] = max(prog["best_streak"], prog["cur_streak"])
        milestone = prog["cur_streak"] % 10 == 0
    else:
        prog["cur_streak"] = 0
    # ---- XP / coins / level (koshish par bhi thoda XP milta hai) ----
    old_lvl = level_info(prog["xp"])[0]
    xp = 10 + min(prog["cur_streak"], 10) if correct else 2
    prog["xp"] += xp
    prog["coins"] += 1 if correct else 0
    new_lvl = level_info(prog["xp"])[0]
    goal_hit = day["total"] == prog["settings"]["daily_goal"]
    if goal_hit:
        prog["coins"] += QUEST_BONUS
    # ---- mistakes / repair lab ----
    ms = prog["mistakes"]
    entry = next((m for m in ms if m["text"] == q["text"]), None)
    if ss.mode == "mistakes":
        if entry:
            if correct:
                entry["streak"] = entry.get("streak", 0) + 1
                if entry["streak"] >= 2:          # 2 baar sahi -> list se hatao
                    ms.remove(entry)
            else:
                entry["streak"] = 0
    elif not correct:
        if entry:
            entry["streak"] = 0
        else:
            ms.append({**q, "streak": 0})
            del ms[:-300]
    prog["resume"] = None
    save_progress()
    return {"milestone": milestone, "goal_hit": goal_hit, "xp": xp,
            "level_up": new_lvl > old_lvl, "level": new_lvl}


def finalize_answer(correct, timed_out=False):
    ss = st.session_state
    info = register_result(ss.q, correct, time.time() - ss.q_start)
    res = {"correct": correct, "timeout": timed_out, "fx_done": False, "anim": "hit" if correct else "hurt",
           "msg": random.choice(PRAISE if correct else OOPS), **info}
    b = ss.battle
    if b:                                            # ladai: sahi = monster ko chot, galat = hero ko chot
        if correct:
            b["hp"] -= 1
        else:
            b["hearts"] -= 1
        if b["hp"] <= 0:
            b["over"] = "win"
            ss.prog["coins"] += WIN_COINS
            ss.prog["xp"] += WIN_XP
            new_lvl = level_info(ss.prog["xp"])[0]
            if new_lvl > res["level"]:
                res["level_up"], res["level"] = True, new_lvl
            save_progress()
        elif b["hearts"] <= 0:
            b["over"] = "lose"
    ss.answered = True
    ss.result = res


# =====================================================================
# ANIMATIONS / SOUND / FOCUS
# =====================================================================
def play_sound(kind):
    if not S("sound"):
        return
    notes = {"ok": [(660, 0.12), (880, 0.2)], "bad": [(300, 0.15), (240, 0.25)]}[kind]
    js = ("<script>try{const C=window.AudioContext||window.webkitAudioContext;const ctx=new C();"
          "let t=ctx.currentTime;" + json.dumps(notes) + ".forEach(([f,d])=>{const o=ctx.createOscillator(),"
          "g=ctx.createGain();o.frequency.value=f;g.gain.value=0.15;o.connect(g);g.connect(ctx.destination);"
          "o.start(t);o.stop(t+d);t+=d;});}catch(e){}</script>")
    components.html(js, height=0)





def run_result_fx(res):
    """Animation sirf ek baar chale (rerun par dobara nahi)."""
    if res.get("fx_done"):
        return
    res["fx_done"] = True
    if res["correct"] or res["level_up"]:
        st.balloons()
    if res["correct"]:
        if res.get("milestone"):
            st.snow()
        play_sound("ok")
    else:
        play_sound("bad")
    if res.get("goal_hit"):
        st.snow()
        st.toast(f"🎁 Daily Quest poora! +{QUEST_BONUS} 🪙")


# =====================================================================
# SMALL UI HELPERS
# =====================================================================
def tiles(items):
    h = "".join(f'<div class="tile"><b>{b}</b><span>{s}</span></div>' for b, s in items)
    st.markdown(f'<div class="tiles">{h}</div>', unsafe_allow_html=True)


def hero_card():
    prog = st.session_state.prog
    lvl, rank, cur = level_info(prog["xp"])
    pct = cur * 100 // XP_PER_LEVEL
    st.markdown(
        f'<div class="hero"><div class="av">{prog["avatar"]}</div><div class="hi"><b>{prog["name"] or "Hero"}</b>'
        f'<span>Level {lvl} • {rank}</span><div class="xpbar"><div style="width:{pct}%"></div></div>'
        f'<span>{cur}/{XP_PER_LEVEL} XP</span></div><div class="coins">🪙 {prog["coins"]}</div></div>',
        unsafe_allow_html=True)


def show_question(q):
    icon, name, cls = TOPICS[q["topic"]]
    text = q["text"].replace(" x ", " × ")
    st.markdown(f'<div class="qcard {cls}"><div class="qt">{icon} {name}</div>'
                f'<div class="qx">{text}</div></div>', unsafe_allow_html=True)


def arena(anim=None):
    """Hero vs Monster (monster ka HP bar, hero ke dil)."""
    ss = st.session_state
    b = ss.battle
    emoji, name = MONSTERS[b["mon"]]
    pct = max(0, b["hp"]) * 100 // b["max"]
    hearts = "❤️" * max(0, b["hearts"]) + "🖤" * (HEARTS - max(0, b["hearts"]))
    mc = "side" + (" hit" if anim == "hit" else "") + (" down" if b["hp"] <= 0 else "")
    hc = "side" + (" hurt" if anim == "hurt" else "")
    dmg = '<div class="dmg">-1 💥</div>' if anim == "hit" else ""
    st.markdown(
        f'<div class="arena"><div class="{hc}"><div class="big">{ss.prog["avatar"]}</div>'
        f'<div class="hearts">{hearts}</div></div><div class="vs">⚔️</div>'
        f'<div class="{mc}">{dmg}<div class="big">{emoji}</div><div class="hpbar"><div style="width:{pct}%"></div></div>'
        f'<div class="mname">{name}</div></div></div>', unsafe_allow_html=True)


def option_grid(callback):
    """2x2 bade rangeen buttons - tap karke jawab do."""
    ss = st.session_state
    q = ss.q
    with st.container(key="opts"):
        for row in (0, 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                i = row + j
                col.button(fmt_option(q, ss.options[i]), key=f"opt_{i}", on_click=callback, args=(i,))


def html_table(headers, rows):
    th = "".join(f"<th>{h}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    st.markdown(f'<table class="ctab"><tr>{th}</tr>{tr}</table>', unsafe_allow_html=True)


# =====================================================================
# NAVIGATION CALLBACKS
# =====================================================================
def go_home():
    ss = st.session_state
    if "prog" in ss:
        ss.prog["resume"] = None
        save_progress()
    ss.page = "home"
    ss.q = None
    ss.answered = False
    ss.result = None
    ss.confirm_reset = False


def goto(page):
    st.session_state.page = page


def new_battle():
    ss = st.session_state
    mon = ss.topic if ss.mode == "topic" else ss.mode
    ss.battle = {"mon": mon, "hp": BATTLE_HP, "max": BATTLE_HP, "hearts": HEARTS, "over": None}


def start_quiz(mode, topic=None):
    ss = st.session_state
    ss.mode = mode
    if topic:
        ss.topic = topic
    ss.page = "quiz"
    ss.q = None
    ss.answered = False
    ss.result = None
    ss.last_text = None
    new_battle()


def rematch():
    new_battle()
    new_question()


def tap_answer(i):
    ss = st.session_state
    if ss.answered or ss.q is None:
        return
    if S("timer_on") and time.time() - ss.q_start > TIMER_SECONDS + 1:
        finalize_answer(False, timed_out=True)
        return
    finalize_answer(is_correct(ss.q, ss.options[i]))


def tap_speed(i):
    ss = st.session_state
    s, q = ss.speed, ss.q
    if s["finished"]:
        return
    if time.time() - s["start"] >= SPEED_SECONDS + 0.5:
        finish_speed()
        return
    ok = is_correct(q, ss.options[i])
    register_result(q, ok, time.time() - ss.q_start)
    s["attempted"] += 1
    s["correct"] += int(ok)
    s["last"] = {"ok": ok, "ans": q["ans_text"], "fx": False}
    new_question()


def start_speed(topic):
    ss = st.session_state
    ss.speed = {"topic": topic, "start": time.time(), "attempted": 0, "correct": 0,
                "finished": False, "last": None, "new_best": False}
    ss.mode = "speed"
    ss.page = "speed"
    ss.last_text = None
    new_question()


def start_speed_from_widget():
    start_speed(st.session_state.get("w_speed_topic", "mixed"))


def set_setting(key, wkey):
    st.session_state.prog["settings"][key] = st.session_state[wkey]
    save_progress()


def set_avatar():
    st.session_state.prog["avatar"] = st.session_state["w_avatar_set"]
    save_progress()


def finish_welcome():
    ss = st.session_state
    ss.prog["name"] = (ss.get("w_name") or "").strip()[:15] or "Hero"
    ss.prog["avatar"] = ss.get("w_av") or "🥷"
    save_progress()
    ss.page = "home"


def snooze_break():
    st.session_state.play_start = time.time()


def ask_reset():
    st.session_state.confirm_reset = True


def cancel_reset():
    st.session_state.confirm_reset = False


def do_reset():
    ss = st.session_state
    keep = {k: ss.prog[k] for k in ("name", "avatar", "settings")}
    ss.prog = copy.deepcopy(DEFAULT_PROG)
    ss.prog.update(keep)
    ss.confirm_reset = False
    save_progress()


# =====================================================================
# PAGES
# =====================================================================
def page_welcome():
    st.markdown("# 🥷 Ninja Quest")
    st.markdown("Naye hero ka swagat hai! Apna naam likho aur apna character chuno. Missions tumhara intezaar kar rahe hain 🚀")
    st.text_input("Hero ka naam", key="w_name", max_chars=15, placeholder="Apna naam likho")
    st.radio("Character chuno", [a for a, lv in AVATARS if lv <= 1], horizontal=True, key="w_av")
    st.button("🎮 Game shuru karo!", key="welcome_go", type="primary", on_click=finish_welcome)


def page_home():
    ss = st.session_state
    hero_card()
    c, t = today_counts()
    _, _, acc = overall()
    tiles([(f"{c}/{t}", "Aaj ke ⭐"), (f"🔥 {daily_streak()}", "Din streak"), (f"{acc}%", "Sahi shots")])
    goal = S("daily_goal")
    st.progress(min(1.0, t / goal) if goal else 1.0)
    st.caption(f"🎁 Daily Quest: {t}/{goal} shots" + ("  ✅ Quest complete!" if t >= goal else f" — poora karo, {QUEST_BONUS} 🪙 chest jeeto!"))

    keys = list(DIFF_MAX)
    st.radio("Level chuno", keys, index=keys.index(S("difficulty")), horizontal=True, key="w_diff",
             format_func=lambda k: DIFF_LABEL[k], on_change=set_setting, args=("difficulty", "w_diff"))

    for key, (icon, name, _) in TOPICS.items():
        st.button(f"{icon}  {name}", key=f"card_{key}", on_click=start_quiz, args=("topic", key))
    st.button("🎁  Mystery Box", key="card_mixed", on_click=start_quiz, args=("mixed",))
    n_m = len(ss.prog["mistakes"])
    st.button(f"🔧  Repair Lab ({n_m})", key="card_mistakes", on_click=start_quiz, args=("mistakes",))

    st.markdown("##### 🎮 Aur games")
    st.button("⚡ Lightning Round (60 sec)", key="tool_speed", on_click=goto, args=("speed_setup",))
    st.button("🗺️ Treasure Map (cheat sheets)", key="tool_chart", on_click=goto, args=("chart",))
    st.button("🏆 Hero Card", key="tool_stats", on_click=goto, args=("stats",))

    with st.expander("⚙️ Settings"):
        unlocked = [a for a, lv in AVATARS if lv <= level_info(ss.prog["xp"])[0]]
        if ss.prog["avatar"] not in unlocked:
            unlocked.insert(0, ss.prog["avatar"])
        st.selectbox("🎭 Character (level badhne par naye milte hain)", unlocked,
                     index=unlocked.index(ss.prog["avatar"]), key="w_avatar_set", on_change=set_avatar)
        st.toggle("⏱️ Turbo mode (15 sec / shot)", value=S("timer_on"), key="w_timer",
                  on_change=set_setting, args=("timer_on", "w_timer"))
        st.toggle("🔊 Sound", value=S("sound"), key="w_sound", on_change=set_setting, args=("sound", "w_sound"))
        st.number_input("🎯 Daily Quest (kitne shots)", min_value=5, max_value=1000, value=int(goal), step=5,
                        key="w_goal", on_change=set_setting, args=("daily_goal", "w_goal"))
        if not ss.confirm_reset:
            st.button("🗑️ Reset Progress", key="reset_ask", on_click=ask_reset)
        else:
            st.warning("Pakka? Saara XP, coins, stats aur repair lab delete ho jayega.")
            st.button("Haan, reset karo", key="reset_yes", type="primary", on_click=do_reset)
            st.button("Nahi, rehne do", key="reset_no", on_click=cancel_reset)


@st.fragment(run_every=1)
def quiz_timer():
    """Har second sirf yeh chhota hissa refresh hota hai. Time khatam -> galat."""
    ss = st.session_state
    if ss.answered or ss.q is None:
        return
    left = TIMER_SECONDS - (time.time() - ss.q_start)
    if left <= 0:
        finalize_answer(False, timed_out=True)
        st.rerun()
    pct = max(0, min(100, left / TIMER_SECONDS * 100))
    cls = "low" if left <= 5 else ""
    st.markdown(f'<div class="timer">⏱️ {int(math.ceil(left))}s</div>'
                f'<div class="tbar {cls}"><div style="width:{pct:.0f}%"></div></div>', unsafe_allow_html=True)


def show_result(q):
    ss = st.session_state
    res = ss.result
    ans = q["ans_text"]
    extra = ""
    if res["level_up"]:
        extra += f'<span>🆙 LEVEL UP! Ab Level {res["level"]} 🎊</span>'
    if res["goal_hit"]:
        extra += f'<span>🎁 Daily Quest complete! +{QUEST_BONUS} 🪙</span>'
    if res["correct"]:
        html = (f'<div class="flash green"></div><div class="res ok pop">{res["msg"]}'
                f'<span>+{res["xp"]} XP • 🔥 Combo {ss.prog["cur_streak"]}</span>{extra}</div>')
    else:
        head = "Time khatam! ⏰" if res["timeout"] else res["msg"]
        html = (f'<div class="flash red"></div><div class="res bad shake">{head}'
                f'<span>Sahi answer: {ans}</span><span>+{res["xp"]} XP koshish ke liye 👍</span>{extra}</div>')
    st.markdown(html, unsafe_allow_html=True)
    if not res["correct"] and q.get("tip"):
        st.markdown(f'<div class="tip">🧙 <b>Wizard Tip:</b> {q["tip"]}</div>', unsafe_allow_html=True)
    run_result_fx(res)


def next_question():
    new_question()


def page_quiz():
    ss = st.session_state
    st.button("🏠 Base", key="home_q", on_click=go_home)
    if ss.battle is None:
        new_battle()
    if ss.q is None:
        new_question()
    q = ss.q
    if q is None:                                   # repair lab khali
        st.success("🎉 Repair Lab khali hai — sab theek ho gaya, hero!")
        return
    c, t = today_counts()
    lvl, _, cur = level_info(ss.prog["xp"])
    tiles([(f"🔥 {ss.prog['cur_streak']}", "Combo"), (f"Lv {lvl}", f"{cur}/{XP_PER_LEVEL} XP"),
           (f"{t}/{S('daily_goal')}", "Daily Quest")])
    if not ss.answered and S("timer_on"):
        quiz_timer()
    arena(ss.result["anim"] if ss.answered else None)
    show_question(q)
    if not ss.answered:
        option_grid(tap_answer)
    else:
        show_result(q)
        b = ss.battle
        emoji, name = MONSTERS[b["mon"]]
        if b["over"] == "win":
            st.markdown(f'<div class="res ok pop">🏆 {name} haar gaya!<span>Ladai jeet li! +{WIN_COINS} 🪙 +{WIN_XP} XP</span></div>',
                        unsafe_allow_html=True)
        elif b["over"] == "lose":
            st.markdown(f'<div class="res bad shake">😵 {name} jeet gaya!<span>Koi baat nahi — rematch me haraa do!</span></div>',
                        unsafe_allow_html=True)
        if b["over"]:
            st.button("🔁 Nayi ladai", key="rematch", type="primary", on_click=rematch)
        else:
            st.button("⚔️ Agla vaar", key="next_q", type="primary", on_click=next_question)


# ---------------------------- LIGHTNING ROUND ----------------------------
def finish_speed():
    ss = st.session_state
    s = ss.speed
    if s["finished"]:
        return
    s["finished"] = True
    if s["correct"] > ss.prog["best_speed"]:
        ss.prog["best_speed"] = s["correct"]
        s["new_best"] = s["correct"] > 0
    ss.prog["resume"] = None
    save_progress()


@st.fragment(run_every=1)
def speed_timer():
    s = st.session_state.speed
    if s["finished"]:
        return
    left = SPEED_SECONDS - (time.time() - s["start"])
    if left <= 0:
        finish_speed()
        st.rerun()
    pct = max(0, min(100, left / SPEED_SECONDS * 100))
    cls = "low" if left <= 10 else ""
    st.markdown(f'<div class="timer">⚡ {int(math.ceil(left))}s &nbsp; ✅ {s["correct"]}/{s["attempted"]}</div>'
                f'<div class="tbar {cls}"><div style="width:{pct:.0f}%"></div></div>', unsafe_allow_html=True)


def page_speed_setup():
    st.button("🏠 Base", key="home_ss", on_click=go_home)
    st.markdown("## ⚡ Lightning Round")
    st.write(f"{SPEED_SECONDS} second me jitne shots maar sako! Best score: **{st.session_state.prog['best_speed']}**")
    opts = ["mixed"] + list(TOPICS)
    st.selectbox("World chuno", opts, key="w_speed_topic",
                 format_func=lambda k: "🎁 Mystery (sab worlds)" if k == "mixed" else f"{TOPICS[k][0]} {TOPICS[k][1]}")
    st.button("▶️ Start!", key="speed_go", type="primary", on_click=start_speed_from_widget)


def page_speed():
    ss = st.session_state
    s = ss.speed
    if not s:
        go_home()
        st.rerun()
    st.button("🏠 Base", key="home_sp", on_click=go_home)
    if s["finished"]:
        acc = s["correct"] * 100 // s["attempted"] if s["attempted"] else 0
        avg = SPEED_SECONDS / s["attempted"] if s["attempted"] else 0
        badge = "🏆 Naya best score!" if s["new_best"] else f"Best: {ss.prog['best_speed']}"
        st.markdown(f'<div class="res ok pop">⚡ Round khatam!<span>{s["correct"]} sahi / {s["attempted"]} shots</span>'
                    f'<span>Accuracy {acc}% • {avg:.1f}s per shot</span><span>{badge}</span></div>',
                    unsafe_allow_html=True)
        if s["new_best"] and not s.get("fx"):
            s["fx"] = True
            st.balloons()
            play_sound("ok")
        st.button("🔁 Dobara khelo", key="speed_again", type="primary", on_click=start_speed, args=(s["topic"],))
        return

    q = ss.q
    speed_timer()
    if s["last"]:
        L = s["last"]
        if L["ok"]:
            st.markdown('<div class="mini ok">✅ Sahi!</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="mini bad">Oops! Sahi answer: {L["ans"]}</div>', unsafe_allow_html=True)
        if not L["fx"]:
            L["fx"] = True
            play_sound("ok" if L["ok"] else "bad")
    show_question(q)
    option_grid(tap_speed)


# ---------------------------- HERO CARD (stats) ----------------------------
def page_stats():
    prog = st.session_state.prog
    st.button("🏠 Base", key="home_st", on_click=go_home)
    hero_card()
    total, correct, acc = overall()
    tiles([(total, "Total shots"), (f"{acc}%", "Sahi shots")])
    tiles([(f"🔥 {prog['best_streak']}", "Best combo"), (f"📅 {daily_streak()}", "Din streak"),
           (f"⚡ {prog['best_speed']}", "Best lightning")])

    st.markdown("#### Last 7 din ki power")
    days = [(datetime.now(IST) - timedelta(days=i)).date() for i in range(6, -1, -1)]
    df = pd.DataFrame({"Total": [prog["daily"].get(d.isoformat(), {}).get("total", 0) for d in days],
                       "Sahi": [prog["daily"].get(d.isoformat(), {}).get("correct", 0) for d in days]},
                      index=pd.to_datetime(days))
    st.bar_chart(df, color=["#94a3b8", "#22c55e"])

    st.markdown("#### Worlds ka power meter")
    weak, weak_acc = None, 101
    for key in TOPICS:
        tp = prog["topics"][key]
        if tp["total"] >= 3 and tp["correct"] * 100 / tp["total"] < weak_acc:
            weak, weak_acc = key, tp["correct"] * 100 / tp["total"]
    for key, (icon, name, _) in TOPICS.items():
        tp = prog["topics"][key]
        if tp["total"]:
            a = f'{tp["correct"] * 100 / tp["total"]:.0f}%'
            avg = f'{tp["time"] / tp["total"]:.1f}s/shot'
        else:
            a, avg = "-", "-"
        flag = " 💪 Yahan training karo" if key == weak else ""
        cls = "trow weak" if key == weak else "trow"
        st.markdown(f'<div class="{cls}"><b>{icon} {name}{flag}</b>'
                    f'<span>{a} • {avg} • {tp["total"]} shots</span></div>', unsafe_allow_html=True)
    if weak is None:
        st.caption("Power meter dekhne ke liye kisi world me kam se kam 3 shots maaro.")


# ---------------------------- TREASURE MAP (cheat sheets) ----------------------------
FRAC_LIST = [("1/2", "50%"), ("1/3", "33.33%"), ("2/3", "66.67%"), ("1/4", "25%"), ("3/4", "75%"),
             ("1/5", "20%"), ("2/5", "40%"), ("3/5", "60%"), ("4/5", "80%"), ("1/6", "16.67%"),
             ("5/6", "83.33%"), ("1/8", "12.5%"), ("3/8", "37.5%"), ("5/8", "62.5%"), ("7/8", "87.5%"),
             ("1/10", "10%"), ("1/12", "8.33%"), ("1/16", "6.25%"), ("1/20", "5%"), ("1/25", "4%"),
             ("1/40", "2.5%"), ("1/50", "2%")]


def page_chart():
    st.button("🏠 Base", key="home_ch", on_click=go_home)
    st.markdown("## 🗺️ Treasure Map")
    st.caption("Secret cheat sheets — inhe yaad kar lo to shots aur tez lagenge!")
    tabs = st.tabs(["🚀 Rocket", "🟦 Block", "🧊 Ice", "🍕 Pizza"])
    with tabs[0]:
        n = st.selectbox("Kaun sa number?", list(range(1, 31)), index=1, key="w_tbl")
        html_table(["Boost", "Power"], [(f"{n} × {i}", n * i) for i in range(1, 11)])
    with tabs[1]:
        html_table(["n", "n²"], [(i, i * i) for i in range(1, 31)])
    with tabs[2]:
        html_table(["n", "n³"], [(i, i ** 3) for i in range(1, 31)])
    with tabs[3]:
        html_table(["Slice", "Percent"], FRAC_LIST)


# =====================================================================
# MAIN
# =====================================================================
def init_state():
    ss = st.session_state
    if "prog" in ss:
        return
    ss.path = progress_path()
    ss.prog = load_progress(ss.path)
    ss.update(page="home", mode="topic", topic="table", q=None, q_start=time.time(), answered=False,
              result=None, qid=0, last_text=None, speed=None, confirm_reset=False, save_error=False,
              play_start=time.time(), battle=None, options=[])
    if not ss.prog.get("name"):
        ss.page = "welcome"            # pehli baar: naam + character chuno
        return
    r = ss.prog.get("resume")          # refresh ke baad wahi question wapas
    if (isinstance(r, dict) and isinstance(r.get("q"), dict) and r.get("mode") in ("topic", "mixed", "mistakes")
            and all(k in r["q"] for k in ("topic", "text", "kind", "answer", "ans_text"))
            and r["q"]["topic"] in TOPICS):
        ss.page, ss.mode, ss.q = "quiz", r["mode"], r["q"]
        ss.topic = r.get("topic") if r.get("topic") in TOPICS else "table"
        ss.last_text = r["q"]["text"]
        ss.qid = 1
        ss.options = make_options(ss.q)
        b = r.get("battle")
        if isinstance(b, dict) and all(k in b for k in ("mon", "hp", "max", "hearts", "over")) and b["mon"] in MONSTERS:
            ss.battle = b


PAGES = {"welcome": page_welcome, "home": page_home, "quiz": page_quiz, "speed_setup": page_speed_setup,
         "speed": page_speed, "stats": page_stats, "chart": page_chart}


def main():
    st.set_page_config(page_title="Ninja Quest", page_icon="🥷", layout="centered",
                       initial_sidebar_state="collapsed")
    inject_css()
    init_state()
    ss = st.session_state
    # Pyara break reminder (rokta nahi, bas yaad dilata hai)
    if (ss.page in ("home", "stats") or (ss.page == "quiz" and ss.answered)) and time.time() - ss.play_start > BREAK_MINUTES * 60:
        st.info(f"😎 Hero, {BREAK_MINUTES} minute se khel rahe ho! Paani piyo, aankhein aaram do, phir wapas aana.")
        st.button("Theek hai, aur khelna hai 🎮", key="break_ok", on_click=snooze_break)
    PAGES.get(ss.page, page_home)()
    if ss.get("save_error"):
        st.caption("⚠️ Progress file save nahi ho payi (disk read-only ho sakti hai).")


try:
    main()
except Exception:                       # app crash na ho - friendly message
    st.error("😕 Kuch gadbad ho gayi. Base par jaakar dobara try karo.")
    st.button("🏠 Base", key="err_home", on_click=go_home)
