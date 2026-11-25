import asyncio
import json
import random
import secrets
import time

from . import db, srs
from .cards import CARDS, build_question_set, card_reveal, correct_answer_text, furi_tier, render_question
from .kana import reading_matches

TC = db.TIME_CONTROLS
COUNTDOWN = 3.0
PTS_CORRECT, PTS_WRONG = 10, -5
BOT_NAMES = ["Bot·Sakura", "Bot·Kenji", "Bot·Yuki", "Bot·Haruto", "Bot·Aoi", "Bot·Ren", "Bot·Mei"]


def elo_k(games):
    return 40 if games < 30 else 20


def elo_update(ra, rb, score_a, games_a, games_b):
    ea = 1 / (1 + 10 ** ((rb - ra) / 400))
    na = ra + elo_k(games_a) * (score_a - ea)
    nb = rb + elo_k(games_b) * ((1 - score_a) - (1 - ea))
    return na, nb


class Hub:
    """Tracks live websocket connections per user."""

    def __init__(self):
        self.conns = {}  # uid -> set(ws)

    def add(self, uid, ws):
        self.conns.setdefault(uid, set()).add(ws)

    def remove(self, uid, ws):
        s = self.conns.get(uid)
        if s:
            s.discard(ws)
            if not s:
                del self.conns[uid]

    def online(self, uid):
        return uid in self.conns

    async def send(self, uid, msg):
        for ws in list(self.conns.get(uid, ())):
            try:
                await ws.send_text(json.dumps(msg, ensure_ascii=False))
            except Exception:
                pass

    def count(self):
        return len(self.conns)


hub = Hub()


class Player:
    def __init__(self, uid, name, rating, games, lang, bot=False):
        self.uid, self.name, self.rating, self.games, self.lang, self.bot = uid, name, rating, games, lang, bot
        self.tier = furi_tier(rating)
        self.idx = 0
        self.correct = 0
        self.wrong = 0
        self.answers = []  # [q_index, given, ok, ms]
        self.q_started = 0.0

    @property
    def score(self):
        return self.correct * PTS_CORRECT + self.wrong * PTS_WRONG

    @property
    def accuracy(self):
        n = self.correct + self.wrong
        return self.correct / n if n else 0.0

    def public(self):
        return {"name": self.name, "rating": round(self.rating), "bot": self.bot,
                "correct": self.correct, "wrong": self.wrong, "score": self.score}


class Match:
    def __init__(self, tc, p1: Player, p2: Player, rated):
        self.id = secrets.token_urlsafe(8)
        self.tc = tc
        self.duration = TC[tc]
        self.players = [p1, p2]
        self.rated = rated and not p1.bot and not p2.bot
        self.level, self.questions = build_question_set((p1.rating + p2.rating) / 2, self.duration // 2 + 20)
        now = time.time()
        self.starts_at = now + COUNTDOWN
        self.ends_at = self.starts_at + self.duration
        self.finished = False
        self.result = None

    def player(self, uid):
        for p in self.players:
            if p.uid == uid and not p.bot:
                return p
        return None

    def opponent(self, p):
        return self.players[1] if self.players[0] is p else self.players[0]

    def question_msg(self, p):
        if p.idx >= len(self.questions):  # extremely fast player: extend the set
            _, more = build_question_set(sum(x.rating for x in self.players) / 2, 20)
            self.questions += more
        p.q_started = time.time()
        return {"type": "question", "match_id": self.id, "q": p.idx,
                "data": render_question(self.questions[p.idx], p.lang, p.tier)}

    def intro_msg(self, p):
        o = self.opponent(p)
        return {"type": "match_start", "match_id": self.id, "tc": self.tc, "duration": self.duration,
                "rated": self.rated, "level": self.level, "server_now": time.time(),
                "starts_at": self.starts_at, "ends_at": self.ends_at,
                "you": p.public(), "opponent": o.public(), "tier": p.tier}

    async def broadcast_scores(self):
        for p in self.players:
            if not p.bot:
                await hub.send(p.uid, {"type": "scores", "match_id": self.id,
                                       "you": p.public(), "opponent": self.opponent(p).public()})

    def check(self, p, q_index, given):
        q = self.questions[q_index]
        if q["t"] == "reading":
            return reading_matches(str(given), CARDS[q["c"]]["reading"])
        try:
            return q["o"][int(given)] == q["c"]
        except (ValueError, IndexError, TypeError):
            return False

    async def submit(self, p, q_index, given):
        now = time.time()
        if self.finished or now < self.starts_at or now > self.ends_at or q_index != p.idx:
            return
        ok = self.check(p, q_index, given)
        ms = int((now - p.q_started) * 1000)
        p.answers.append([q_index, given, ok, ms])
        if ok:
            p.correct += 1
        else:
            p.wrong += 1
        p.idx += 1
        if not p.bot:
            q = self.questions[q_index]
            if not ok:
                srs.add_missed(p.uid, q["c"])
            correct_idx = q["o"].index(q["c"]) if "o" in q else None
            await hub.send(p.uid, {"type": "feedback", "match_id": self.id, "q": q_index, "ok": ok,
                                   "correct_index": correct_idx,
                                   "correct_text": correct_answer_text(q, p.lang),
                                   "card": card_reveal(q["c"], p.lang)})
            await hub.send(p.uid, self.question_msg(p))
        await self.broadcast_scores()

    def decide(self):
        a, b = self.players
        if a.score != b.score:
            return "p1" if a.score > b.score else "p2"
        if round(a.accuracy, 4) != round(b.accuracy, 4):
            return "p1" if a.accuracy > b.accuracy else "p2"
        return "draw"

    async def finish(self):
        if self.finished:
            return
        self.finished = True
        a, b = self.players
        res = self.decide()
        self.result = res
        before = [a.rating, b.rating]
        after = before[:]
        if self.rated:
            s = {"p1": 1.0, "p2": 0.0, "draw": 0.5}[res]
            after = list(elo_update(a.rating, b.rating, s, a.games, b.games))
            for p, new, sc in ((a, after[0], s), (b, after[1], 1 - s)):
                col = "wins" if sc == 1 else "losses" if sc == 0 else "draws"
                db.ex(f"UPDATE ratings SET rating=?, games=games+1, {col}={col}+1 WHERE user_id=? AND tc=?",
                      new, p.uid, self.tc)
                db.ex("INSERT INTO rating_history (user_id, tc, rating, match_id, ts) VALUES (?,?,?,?,?)",
                      p.uid, self.tc, new, self.id, time.time())
        data = {"questions": self.questions, "answers": [a.answers, b.answers]}
        db.ex("""INSERT INTO matches (id, tc, rated, bot, level, p1_id, p2_id, p2_name, p1_score, p2_score,
                 p1_correct, p1_wrong, p2_correct, p2_wrong, result, p1_before, p1_after, p2_before, p2_after,
                 started_at, ended_at, data) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              self.id, self.tc, int(self.rated), int(b.bot), self.level, a.uid, None if b.bot else b.uid, b.name,
              a.score, b.score, a.correct, a.wrong, b.correct, b.wrong, res,
              before[0], after[0], before[1], after[1], self.starts_at, time.time(), json.dumps(data))
        for i, p in enumerate(self.players):
            if p.bot:
                continue
            mine = "p1" if i == 0 else "p2"
            outcome = "draw" if res == "draw" else ("win" if res == mine else "loss")
            missed = len({self.questions[x[0]]["c"] for x in p.answers if not x[2]})
            await hub.send(p.uid, {"type": "match_end", "match_id": self.id, "outcome": outcome,
                                   "rated": self.rated, "you": p.public(), "opponent": self.opponent(p).public(),
                                   "accuracy": round(p.accuracy * 100), "opp_accuracy": round(self.opponent(p).accuracy * 100),
                                   "rating_before": round(before[i]), "rating_after": round(after[i]),
                                   "missed_added": missed, "tc": self.tc})
        manager.end(self)


class Manager:
    def __init__(self):
        self.queues = {tc: [] for tc in TC}  # tc -> [ {uid, rating, since} ]
        self.matches = {}  # match_id -> Match
        self.by_user = {}  # uid -> match_id
        self.challenges = {}  # code -> {uid, tc, rated, created}

    # ----- helpers -----
    def make_player(self, uid, tc):
        u = db.q1("SELECT * FROM users WHERE id=?", uid)
        r = db.q1("SELECT * FROM ratings WHERE user_id=? AND tc=?", uid, tc)
        return Player(uid, u["username"], r["rating"], r["games"], u["lang"])

    def active(self, uid):
        mid = self.by_user.get(uid)
        m = self.matches.get(mid) if mid else None
        return m if m and not m.finished else None

    def dequeue(self, uid):
        for tc in self.queues:
            self.queues[tc] = [e for e in self.queues[tc] if e["uid"] != uid]

    def in_queue(self, uid):
        for tc, lst in self.queues.items():
            if any(e["uid"] == uid for e in lst):
                return tc
        return None

    # ----- lifecycle -----
    async def start(self, m: Match):
        self.matches[m.id] = m
        for p in m.players:
            if not p.bot:
                self.by_user[p.uid] = m.id
                self.dequeue(p.uid)
                await hub.send(p.uid, m.intro_msg(p))
        asyncio.create_task(self._run(m))

    async def _run(self, m: Match):
        await asyncio.sleep(max(0, m.starts_at - time.time()))
        for p in m.players:
            if p.bot:
                asyncio.create_task(self._bot(m, p))
            else:
                await hub.send(p.uid, m.question_msg(p))
        await asyncio.sleep(max(0, m.ends_at - time.time()))
        await m.finish()

    async def _bot(self, m: Match, p: Player):
        acc = min(0.96, max(0.55, 0.72 + (p.rating - 800) / 1500))
        avg = min(7.0, max(2.2, 5.5 - (p.rating - 800) / 300))
        while not m.finished and time.time() < m.ends_at:
            q = m.questions[p.idx] if p.idx < len(m.questions) else None
            if q is None:
                m.question_msg(p)
                continue
            extra = 1.6 if q["t"] in ("reading", "translate") else 1.0
            await asyncio.sleep(max(0.8, random.gauss(avg * extra, avg * 0.35)))
            if m.finished or time.time() > m.ends_at:
                break
            p.q_started = time.time()
            if random.random() < acc:
                given = CARDS[q["c"]]["reading"] if q["t"] == "reading" else q["o"].index(q["c"])
            else:
                given = "x" if q["t"] == "reading" else random.choice([i for i in range(len(q["o"])) if q["o"][i] != q["c"]])
            await m.submit(p, p.idx, given)

    def end(self, m: Match):
        for p in m.players:
            if not p.bot and self.by_user.get(p.uid) == m.id:
                del self.by_user[p.uid]
        # keep finished match briefly for late messages
        asyncio.get_event_loop().call_later(60, lambda: self.matches.pop(m.id, None))

    # ----- matchmaking -----
    async def enqueue(self, uid, tc):
        if self.active(uid):
            return
        self.dequeue(uid)
        r = db.q1("SELECT rating FROM ratings WHERE user_id=? AND tc=?", uid, tc)["rating"]
        self.queues[tc].append({"uid": uid, "rating": r, "since": time.time()})
        await hub.send(uid, {"type": "queued", "tc": tc})
        await self.try_pair(tc)

    async def try_pair(self, tc):
        q = self.queues[tc]
        now = time.time()
        q[:] = [e for e in q if hub.online(e["uid"])]
        q.sort(key=lambda e: e["since"])
        used = set()
        for i, a in enumerate(q):
            if a["uid"] in used:
                continue
            win_a = 150 + 30 * (now - a["since"])
            best = None
            for b in q[i + 1:]:
                if b["uid"] in used or b["uid"] == a["uid"]:
                    continue
                win_b = 150 + 30 * (now - b["since"])
                diff = abs(a["rating"] - b["rating"])
                if diff <= min(win_a, win_b) and (best is None or diff < abs(a["rating"] - best["rating"])):
                    best = b
            if best:
                used |= {a["uid"], best["uid"]}
                m = Match(tc, self.make_player(a["uid"], tc), self.make_player(best["uid"], tc), rated=True)
                await self.start(m)
        q[:] = [e for e in q if e["uid"] not in used]

    async def pair_loop(self):
        while True:
            await asyncio.sleep(1)
            for tc in TC:
                if len(self.queues[tc]) >= 2:
                    await self.try_pair(tc)
            now = time.time()
            for code in [c for c, v in self.challenges.items() if now - v["created"] > 1800]:
                del self.challenges[code]

    async def play_bot(self, uid, tc):
        if self.active(uid):
            return
        me = self.make_player(uid, tc)
        bot_rating = max(400, me.rating + random.randint(-60, 60))
        bot = Player(-1, random.choice(BOT_NAMES), bot_rating, 99, "en", bot=True)
        await self.start(Match(tc, me, bot, rated=False))

    # ----- challenges -----
    def create_challenge(self, uid, tc, rated):
        for c in [c for c, v in self.challenges.items() if v["uid"] == uid]:
            del self.challenges[c]
        code = secrets.token_urlsafe(6)
        self.challenges[code] = {"uid": uid, "tc": tc, "rated": rated, "created": time.time()}
        return code

    async def accept_challenge(self, uid, code):
        ch = self.challenges.get(code)
        if not ch:
            return "This challenge has expired or doesn't exist."
        if ch["uid"] == uid:
            return "You can't accept your own challenge. Send the link to a friend."
        if not hub.online(ch["uid"]):
            return "The challenger is not online right now."
        if self.active(ch["uid"]) or self.active(uid):
            return "One of you is already in a match."
        del self.challenges[code]
        tc = ch["tc"]
        m = Match(tc, self.make_player(ch["uid"], tc), self.make_player(uid, tc), rated=ch["rated"])
        await self.start(m)
        return None

    def stats(self):
        return {"online": hub.count(), "playing": sum(1 for m in self.matches.values() if not m.finished),
                "queues": {tc: len(v) for tc, v in self.queues.items()}}


manager = Manager()
