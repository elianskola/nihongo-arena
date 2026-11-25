# 語 Nihongo Arena

A chess.com-style site for practising Japanese vocabulary **in sentences**: rated 1-v-1 battles with Elo, plus Anki-style spaced-repetition study.

## Run it

Needs Python 3.10+.

```bash
pip install -r requirements.txt
python run.py            # → http://localhost:8000
```

On Windows you can double-click `run.bat`; on macOS/Linux, `./run.sh`.

To let friends on the same Wi-Fi join, they open `http://<your-computer's-IP>:8000`. If they're elsewhere, you'll need to put it on a host (Render, Railway, Fly.io, a VPS). Use the start command `uvicorn server.main:app --host 0.0.0.0 --port $PORT`, and set `ARENA_DB` to a persistent disk path so accounts survive restarts.

## How it plays

| | |
|---|---|
| **Time controls** | Blitz 1 min · Rapid 3 min · Classical 5 min. Each has its own Elo. |
| **Battle** | Both players get the identical sentence set at the same moment. The clock is server-side. |
| **Question types (mixed)** | *Meaning*: highlighted word in a sentence, pick its meaning. *Fill the blank*: pick the word that fits (translation shown as a hint). *Reading*: type the reading in kana or romaji (`taberu` → たべる). *Translate*: pick the sentence's translation. |
| **Scoring** | +10 correct, −5 wrong (so blind guessing doesn't pay). The higher score wins; a tie goes to accuracy, then it's a draw. |
| **Elo** | Everyone starts at 800. K = 40 for your first 30 games in a time control, then K = 20. |
| **Difficulty** | The players' average rating picks the level: < 1000 → N5, 1000–1299 → N4, 1300+ → N3. About 20% of cards come from easier levels. |
| **Furigana** | < 1000: on every kanji. 1000–1399: only on the target word. 1400+: hidden (hover or tap to peek). Reading questions never show the target's furigana. |
| **No opponent?** | After about 12 s in the queue you're offered a bot at your rating. Bot games are **unrated**. |
| **Challenge a friend** | Creates a private link (rated or unrated). Keep the page open until your friend accepts. |
| **Missed words** | Every card you miss in a battle goes straight into your study queue and comes up first. |

## Study (SRS)

SM-2 like Anki: Again / Hard / Good / Easy. There are learning steps (1 min, 10 min), graduation at 1 day (Easy = 4 days), ease adjustments, and lapses. New cards per day can be changed in Settings (default 10). New cards come from your level first, then easier ones. Keys: `Space` reveals, `1`–`4` grade.

## Vocabulary database

670 hand-written sentence cards: **N5 257 · N4 228 · N3 185**. Each card has a target word, reading, part of speech, English and Swedish meanings, and an English and Swedish translation of the sentence.

The sources are in `data/src/*.txt`, one card per line:

```
level|word|reading|pos|meaning_en|meaning_sv|sentence|translation_en|translation_sv
N5|食べる|たべる|v|to eat|att äta|毎朝パンを[食べます]。|I eat bread every morning.|Jag äter bröd varje morgon.
```

- Put `[brackets]` around the target word as it appears in the sentence.
- `pos` is one of `n v adj na adv`. Distractors are drawn from the same part of speech.
- Furigana is generated automatically. To force a reading, write `{漢字|よみ}` in the sentence.

To add cards, edit or add a `.txt` file, then rebuild `data/cards.json` (the server only reads this file):

```bash
pip install fugashi unidic-lite   # only needed for rebuilding
python tools/build_cards.py
```

## Project layout

```
server/main.py     FastAPI app: REST API, WebSocket, static files
server/game.py     matchmaking, matches, bots, Elo, challenges
server/cards.py    card loading, question generation, level/furigana tiers
server/srs.py      SM-2 scheduler
server/kana.py     romaji → kana for typed answers
server/db.py       SQLite schema + auth (PBKDF2 password hashes)
static/            single-page frontend (no build step)
data/cards.json    built card database
tests/e2e_test.py  end-to-end test: run the server, then `python tests/e2e_test.py http://localhost:8000`
```

Data is stored in `arena.db` (SQLite) in the project folder.
