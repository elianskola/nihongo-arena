/* Nihongo Arena — single page app */
"use strict";

const S = {
  user: null, stats: null, study: null, ws: null, wsRetry: 0, lang: "en",
  selTc: "blitz", match: null, queue: null, challenge: null, afterLogin: null,
};
const TCS = {
  blitz: { secs: 60, ico: "⚡" },
  rapid: { secs: 180, ico: "⏱" },
  classical: { secs: 300, ico: "🏯" },
};

// ---------------------------------------------------------------- i18n
const I18N = {
  en: {
    play: "Play", study: "Study", leaderboard: "Leaderboard", profile: "Profile", settings: "Settings",
    login: "Log in", register: "Sign up", logout: "Log out", online: "online", playing: "in battles",
    blitz: "Blitz", rapid: "Rapid", classical: "Classical", min: "min",
    hero_title: "Battle for your Japanese.",
    hero_sub: "Rated vocabulary duels in real sentences. Answer faster and more accurately than your opponent before the clock runs out — win and climb the Elo ladder. Every word you miss goes straight into your Anki-style review deck.",
    play_rated: "Play rated", play_bot: "Practice vs bot (unrated)", challenge: "Challenge a friend",
    your_ratings: "Your ratings", games: "games", study_panel: "Today's study", study_now: "Study now",
    recent: "Recent battles", no_games: "No battles yet — play your first one!",
    how_title: "How battles work",
    how1: "Both players get the exact same sentence cards at the same time.",
    how2: "Four question types are mixed: word meaning, fill-the-blank, type the reading, translate the sentence.",
    how3: "+10 points for a correct answer, −5 for a wrong one. Highest score when the clock hits zero wins; ties go to accuracy.",
    how4: "Your rating decides the vocabulary: under 1000 = JLPT N5, 1000–1299 = N4, 1300+ = N3. Furigana fades as you climb.",
    searching: "Searching for an opponent…", cancel: "Cancel", nobody: "Nobody at your level right now?",
    q_meaning: "What does the highlighted word mean here?", q_cloze: "Which word fits the blank? (dictionary form)",
    q_reading: "Type the reading of", q_reading2: "(kana or romaji, dictionary form)",
    q_translate: "Choose the correct translation", t_meaning: "Meaning", t_cloze: "Fill the blank", t_reading: "Reading", t_translate: "Translate",
    submit: "Submit", correct: "Correct", wrong: "Wrong", accuracy: "Accuracy", score: "Score", answered: "Answered",
    unrated: "Unrated", rated: "Rated", get_ready: "Get ready", you: "You",
    win: "Victory!", loss: "Defeat", draw: "Draw", rematch: "New battle", review_match: "Review battle",
    study_missed: "Study missed words", close: "Close", missed_added: "missed words added to your review deck",
    rating: "Rating", new: "New", learning: "Learning", review: "Review", missed: "From battles",
    show_answer: "Show answer", again: "Again", hard: "Hard", good: "Good", easy: "Easy",
    done_title: "All caught up!", done_sub: "No more cards due right now. Play a battle — missed words come back here.",
    next_due: "Next card due", deck_progress: "Deck progress", seen: "seen", mature: "mature",
    study_prompt: "What does the highlighted word mean?",
    player: "Player", wld: "W / L / D", joined: "Joined", rating_history: "Rating history", match_history: "Match history",
    opponent: "Opponent", result: "Result", date: "Date", type: "Type", tc: "Time control",
    username: "Username", password: "Password", no_account: "No account?", have_account: "Already have an account?",
    lang_label: "Meaning & translation language", new_per_day: "New study cards per day", save: "Save", saved: "Saved",
    challenge_title: "Challenge a friend", challenge_link: "Send this link to your friend:", copy: "Copy",
    copied: "Copied!", waiting_friend: "Waiting for your friend to open the link… keep this page open.",
    create_link: "Create link", rated_game: "Rated game", challenged_you: "challenges you to a battle",
    accept: "Accept challenge", login_to_accept: "Log in to accept", offline_chal: "The challenger isn't online right now.",
    login_needed: "Log in to play rated battles and keep your study progress.",
    question: "Question", your_answer: "Answer", no_answer: "—", ms: "s",
    leader_empty: "No rated games in this time control yet.",
    keys: "Keys", level: "Level", streak_note: "Missed battle words show up first in your study queue.",
  },
  sv: {
    play: "Spela", study: "Plugga", leaderboard: "Topplista", profile: "Profil", settings: "Inställningar",
    login: "Logga in", register: "Skapa konto", logout: "Logga ut", online: "online", playing: "i matcher",
    blitz: "Blixt", rapid: "Snabb", classical: "Klassisk", min: "min",
    hero_title: "Kämpa för din japanska.",
    hero_sub: "Rankade ordförrådsdueller i riktiga meningar. Svara snabbare och mer korrekt än motståndaren innan tiden tar slut — vinn och klättra på Elo-stegen. Varje ord du missar hamnar direkt i din Anki-liknande repetitionslek.",
    play_rated: "Spela rankat", play_bot: "Träna mot bot (orankat)", challenge: "Utmana en vän",
    your_ratings: "Dina ratingar", games: "matcher", study_panel: "Dagens plugg", study_now: "Plugga nu",
    recent: "Senaste matcher", no_games: "Inga matcher än — spela din första!",
    how_title: "Så fungerar matcherna",
    how1: "Båda spelarna får exakt samma meningskort samtidigt.",
    how2: "Fyra frågetyper blandas: ordets betydelse, fyll i luckan, skriv läsningen, översätt meningen.",
    how3: "+10 poäng för rätt svar, −5 för fel. Högst poäng när klockan når noll vinner; vid lika avgör träffsäkerheten.",
    how4: "Din rating styr ordförrådet: under 1000 = JLPT N5, 1000–1299 = N4, 1300+ = N3. Furiganan försvinner när du klättrar.",
    searching: "Letar efter en motståndare…", cancel: "Avbryt", nobody: "Ingen på din nivå just nu?",
    q_meaning: "Vad betyder det markerade ordet här?", q_cloze: "Vilket ord passar i luckan? (grundform)",
    q_reading: "Skriv läsningen av", q_reading2: "(kana eller romaji, grundform)",
    q_translate: "Välj rätt översättning", t_meaning: "Betydelse", t_cloze: "Fyll i luckan", t_reading: "Läsning", t_translate: "Översätt",
    submit: "Svara", correct: "Rätt", wrong: "Fel", accuracy: "Träffsäkerhet", score: "Poäng", answered: "Besvarade",
    unrated: "Orankad", rated: "Rankad", get_ready: "Gör dig redo", you: "Du",
    win: "Seger!", loss: "Förlust", draw: "Oavgjort", rematch: "Ny match", review_match: "Granska matchen",
    study_missed: "Plugga missade ord", close: "Stäng", missed_added: "missade ord lades till i din repetitionslek",
    rating: "Rating", new: "Nya", learning: "Lär", review: "Repetera", missed: "Från matcher",
    show_answer: "Visa svar", again: "Igen", hard: "Svårt", good: "Bra", easy: "Lätt",
    done_title: "Allt klart!", done_sub: "Inga fler kort att repetera just nu. Spela en match — missade ord dyker upp här.",
    next_due: "Nästa kort", deck_progress: "Framsteg", seen: "sedda", mature: "inlärda",
    study_prompt: "Vad betyder det markerade ordet?",
    player: "Spelare", wld: "V / F / O", joined: "Gick med", rating_history: "Ratinghistorik", match_history: "Matchhistorik",
    opponent: "Motståndare", result: "Resultat", date: "Datum", type: "Typ", tc: "Tidskontroll",
    username: "Användarnamn", password: "Lösenord", no_account: "Inget konto?", have_account: "Har du redan ett konto?",
    lang_label: "Språk för betydelser och översättningar", new_per_day: "Nya kort per dag", save: "Spara", saved: "Sparat",
    challenge_title: "Utmana en vän", challenge_link: "Skicka den här länken till din vän:", copy: "Kopiera",
    copied: "Kopierat!", waiting_friend: "Väntar på att din vän öppnar länken… håll sidan öppen.",
    create_link: "Skapa länk", rated_game: "Rankad match", challenged_you: "utmanar dig till en match",
    accept: "Anta utmaningen", login_to_accept: "Logga in för att anta", offline_chal: "Utmanaren är inte online just nu.",
    login_needed: "Logga in för att spela rankat och spara dina framsteg.",
    question: "Fråga", your_answer: "Svar", no_answer: "—", ms: "s",
    leader_empty: "Inga rankade matcher i den här tidskontrollen än.",
    keys: "Tangenter", level: "Nivå", streak_note: "Missade ord från matcher kommer först i pluggkön.",
  },
};
const t = (k) => (I18N[S.lang] && I18N[S.lang][k]) || I18N.en[k] || k;

// ---------------------------------------------------------------- utils
const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* ignore */ } },
};

async function api(path, body) {
  const opts = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const r = await fetch(path, opts);
  let data = null;
  try { data = await r.json(); } catch { /* empty */ }
  if (!r.ok) throw new Error((data && data.detail) || r.statusText);
  return data;
}

function toast(msg, ms = 2200) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove("show"), ms);
}

function modal(html) {
  $("#modal-root").innerHTML = html ? `<div class="modal-bg"><div class="modal">${html}</div></div>` : "";
  return $("#modal-root .modal");
}

function fmtIvl(sec) {
  if (sec < 60) return "<1m";
  if (sec < 3600) return Math.round(sec / 60) + "m";
  if (sec < 86400) return Math.round(sec / 3600) + "h";
  const d = sec / 86400;
  if (d < 30) return Math.round(d) + "d";
  if (d < 365) return (d / 30).toFixed(1) + "mo";
  return (d / 365).toFixed(1) + "y";
}
const fmtDate = (ts) => new Date(ts * 1000).toLocaleDateString(S.lang === "sv" ? "sv-SE" : "en-GB", { day: "numeric", month: "short", year: "numeric" });
const delta = (a, b) => { const d = b - a; return d > 0 ? `<span class="delta-up">+${d}</span>` : d < 0 ? `<span class="delta-down">${d}</span>` : `<span class="muted">±0</span>`; };
const initial = (n) => esc((n || "?").replace(/^Bot·/, "")[0].toUpperCase());

/** Render sentence segments as ruby HTML. tier: full | target | hover */
function sentenceHTML(segs, tier = "full", cls = "") {
  const parts = segs.map((s) => {
    if (s.blank) return `<span class="blank"></span>`;
    const tc = s.x ? ' class="tgt"' : "";
    if (s.r) return `<ruby${tc}>${esc(s.t)}<rt>${esc(s.r)}</rt></ruby>`;
    return s.x ? `<span class="tgt">${esc(s.t)}</span>` : esc(s.t);
  });
  return `<div class="sentence furi-${tier} ${cls}">${parts.join("")}</div>`;
}
function wordFuriHTML(segs) {
  return segs.map((s) => (s.r ? `<ruby>${esc(s.t)}<rt>${esc(s.r)}</rt></ruby>` : esc(s.t))).join("");
}
document.addEventListener("click", (e) => {
  const r = e.target.closest(".furi-hover ruby");
  if (r) r.classList.toggle("show");
});

// ------------------------------------------------- romaji -> kana preview (mirror of server/kana.py)
const KT = (() => {
  const m = {};
  const add = (s) => s.split(" ").forEach((p) => { const [k, v] = p.split("="); m[k] = v; });
  add("a=あ i=い u=う e=え o=お ka=か ki=き ku=く ke=け ko=こ ga=が gi=ぎ gu=ぐ ge=げ go=ご sa=さ si=し shi=し su=す se=せ so=そ za=ざ zi=じ ji=じ zu=ず ze=ぜ zo=ぞ ta=た ti=ち chi=ち tu=つ tsu=つ te=て to=と da=だ di=ぢ du=づ de=で do=ど na=な ni=に nu=ぬ ne=ね no=の ha=は hi=ひ hu=ふ fu=ふ he=へ ho=ほ ba=ば bi=び bu=ぶ be=べ bo=ぼ pa=ぱ pi=ぴ pu=ぷ pe=ぺ po=ぽ ma=ま mi=み mu=む me=め mo=も ya=や yu=ゆ yo=よ ra=ら ri=り ru=る re=れ ro=ろ la=ら li=り lu=る le=れ lo=ろ wa=わ wo=を");
  add("kya=きゃ kyu=きゅ kyo=きょ gya=ぎゃ gyu=ぎゅ gyo=ぎょ sha=しゃ shu=しゅ sho=しょ sya=しゃ syu=しゅ syo=しょ ja=じゃ ju=じゅ jo=じょ jya=じゃ jyu=じゅ jyo=じょ zya=じゃ zyu=じゅ zyo=じょ cha=ちゃ chu=ちゅ cho=ちょ tya=ちゃ tyu=ちゅ tyo=ちょ nya=にゃ nyu=にゅ nyo=にょ hya=ひゃ hyu=ひゅ hyo=ひょ bya=びゃ byu=びゅ byo=びょ pya=ぴゃ pyu=ぴゅ pyo=ぴょ mya=みゃ myu=みゅ myo=みょ rya=りゃ ryu=りゅ ryo=りょ fa=ふぁ fi=ふぃ fe=ふぇ fo=ふぉ -=ー");
  return m;
})();
function toKana(src) {
  const s = src.toLowerCase().replace(/\s/g, "");
  const V = "aiueo";
  let out = "", i = 0;
  while (i < s.length) {
    const c = s[i], n = s[i + 1] || "";
    if (!/[a-z\-']/.test(c)) { out += c; i++; continue; }
    if (c === "'") { i++; continue; }
    if (c === "n") {
      if (n === "n") { const a = s[i + 2] || ""; out += "ん"; i += (!a || (!V.includes(a) && a !== "y")) ? 2 : 1; continue; }
      if (!n || (!V.includes(n) && n !== "y")) { out += n ? "ん" : "n"; i++; continue; }
    }
    if (c === n && !V.includes(c) && /[a-z]/.test(c)) { out += "っ"; i++; continue; }
    if (s.startsWith("tch", i)) { out += "っ"; i++; continue; }
    let hit = false;
    for (const ln of [3, 2, 1]) {
      const ch = s.substr(i, ln);
      if (KT[ch]) { out += KT[ch]; i += ln; hit = true; break; }
    }
    if (!hit) { out += c; i++; }
  }
  return out;
}

// ---------------------------------------------------------------- session & chrome
async function loadMe() {
  const d = await api("/api/me");
  S.user = d.user;
  S.stats = d.stats;
  S.study = d.study;
  S.lang = (S.user && S.user.lang) || store.get("lang") || "en";
  renderChrome();
  if (S.user && !S.ws) connectWS();
}

function renderChrome() {
  document.documentElement.lang = S.lang;
  const route = (location.hash.slice(2) || "").split("/")[0];
  const due = S.study ? S.study.learning + S.study.review + S.study.missed : 0;
  const items = [
    ["", "♞", t("play")],
    ["study", "🗂", t("study"), due ? `<span class="badge">${due}</span>` : ""],
    ["leaderboard", "🏆", t("leaderboard")],
  ];
  if (S.user) items.push([`u/${encodeURIComponent(S.user.username)}`, "👤", t("profile")], ["settings", "⚙", t("settings")]);
  else items.push(["login", "🔑", t("login")]);
  $("#nav").innerHTML = items.map(([h, ico, lbl, extra]) => {
    const active = (h.split("/")[0] === route || (h === "" && route === "battle")) ? "active" : "";
    return `<a href="#/${h}" class="${active}"><span class="ico">${ico}</span><span class="lbl">${lbl}</span>${extra || ""}</a>`;
  }).join("");
  $("#online").textContent = S.stats ? `${S.stats.online} ${t("online")} · ${S.stats.playing} ${t("playing")}` : "";
  $("#langswitch").innerHTML = ["en", "sv"].map((l) => `<button data-lang="${l}" class="${l === S.lang ? "on" : ""}">${l === "en" ? "EN" : "SV"}</button>`).join("");
  $("#langswitch").onclick = async (e) => {
    const l = e.target.dataset.lang;
    if (!l || l === S.lang) return;
    S.lang = l;
    store.set("lang", l);
    if (S.user) S.user = await api("/api/settings", { lang: l });
    renderChrome();
    route_();
  };
}

// ---------------------------------------------------------------- websocket
function connectWS() {
  const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
  S.ws = ws;
  ws.onopen = () => { S.wsRetry = 0; ws.send(JSON.stringify({ type: "ping" })); };
  ws.onmessage = (e) => onWS(JSON.parse(e.data));
  ws.onclose = () => {
    S.ws = null;
    if (!S.user) return;
    S.wsRetry = Math.min(S.wsRetry + 1, 6);
    setTimeout(connectWS, 500 * 2 ** S.wsRetry);
  };
}
function send(msg) {
  if (S.ws && S.ws.readyState === 1) S.ws.send(JSON.stringify(msg));
  else toast("Connecting…");
}
setInterval(() => { if (S.ws && S.ws.readyState === 1) send({ type: "ping" }); }, 20000);

function onWS(m) {
  switch (m.type) {
    case "hello":
      if (m.in_match) send({ type: "resume" });
      break;
    case "pong":
      S.stats = m.stats;
      $("#online").textContent = `${S.stats.online} ${t("online")} · ${S.stats.playing} ${t("playing")}`;
      break;
    case "queued":
      showQueue(m.tc);
      break;
    case "unqueued":
      S.queue = null;
      modal("");
      break;
    case "match_start":
      onMatchStart(m);
      break;
    case "question":
      if (S.match && S.match.id === m.match_id) { S.match.q = m.q; S.match.data = m.data; renderQuestion(); }
      break;
    case "feedback":
      if (S.match && S.match.id === m.match_id) onFeedback(m);
      break;
    case "scores":
      if (S.match && S.match.id === m.match_id) { S.match.you = m.you; S.match.opponent = m.opponent; renderBars(); }
      break;
    case "match_end":
      onMatchEnd(m);
      break;
    case "error":
      toast(m.msg, 3500);
      break;
  }
}

// ---------------------------------------------------------------- router
window.addEventListener("hashchange", () => route_());
function route_() {
  renderChrome();
  const [r, arg] = location.hash.slice(2).split("/");
  if (S.match && !S.match.ended && r !== "battle") { location.hash = "#/battle"; return; }
  const views = { "": viewHome, login: viewLogin, register: viewRegister, study: viewStudy, leaderboard: viewLeaderboard,
    u: viewProfile, m: viewMatch, c: viewChallenge, settings: viewSettings, battle: viewBattle };
  (views[r] || viewHome)(arg && decodeURIComponent(arg));
  window.scrollTo(0, 0);
}
const app = () => $("#app");

// ---------------------------------------------------------------- home / play
async function viewHome() {
  const u = S.user;
  const tcCards = Object.entries(TCS).map(([k, v]) => {
    const r = u ? u.ratings[k] : null;
    return `<div class="tc-card ${S.selTc === k ? "sel" : ""}" data-tc="${k}">
      <div class="tc-ico">${v.ico}</div>
      <div class="tc-name">${t(k)}</div>
      <div class="tc-time">${v.secs / 60} ${t("min")}</div>
      ${r ? `<div class="tc-rating">${r.rating}<small>${r.games} ${t("games")}</small></div>` : ""}
    </div>`;
  }).join("");
  const how = `<div class="panel"><h3>${t("how_title")}</h3><ul class="how">
      <li>${t("how1")}</li><li>${t("how2")}</li><li>${t("how3")}</li><li>${t("how4")}</li></ul></div>`;
  const st = S.study;
  const studyPanel = u ? `<div class="panel"><h3>${t("study_panel")}</h3>
      <div class="counts" style="justify-content:flex-start">
        <span class="c-new">${st.new}<small>${t("new")}</small></span>
        <span class="c-learn">${st.learning}<small>${t("learning")}</small></span>
        <span class="c-rev">${st.review}<small>${t("review")}</small></span>
        <span class="c-missed">${st.missed}<small>${t("missed")}</small></span>
      </div>
      <a href="#/study" class="btn primary" style="display:block;text-align:center">${t("study_now")}</a>
      <p class="muted" style="font-size:13px;margin:10px 0 0">${t("streak_note")}</p></div>` : "";
  app().innerHTML = `
    <div class="hero"><div class="hero-text"><h1>${t("hero_title")}</h1><p>${t("hero_sub")}</p></div></div>
    <div class="grid cols-main">
      <div class="grid">
        <div class="panel">
          <div class="tc-grid">${tcCards}</div>
          <div class="play-actions">
            ${u ? `<button class="btn primary big" id="b-play">${t("play_rated")} · ${t(S.selTc)}</button>
            <div class="two"><button class="btn" id="b-bot">🤖 ${t("play_bot")}</button>
            <button class="btn" id="b-chal">🤝 ${t("challenge")}</button></div>`
            : `<p class="muted" style="margin:0 0 6px">${t("login_needed")}</p>
            <div class="two"><a class="btn primary" href="#/register" style="text-align:center">${t("register")}</a>
            <a class="btn" href="#/login" style="text-align:center">${t("login")}</a></div>`}
          </div>
        </div>
        ${u ? `<div class="panel flush"><div style="padding:16px 18px 4px"><h3>${t("recent")}</h3></div><div id="recent"></div></div>` : how}
      </div>
      <div class="grid" style="align-content:start">${studyPanel}${u ? how : ""}</div>
    </div>`;
  app().querySelectorAll(".tc-card").forEach((el) => el.onclick = () => { S.selTc = el.dataset.tc; viewHome(); });
  if (!u) return;
  $("#b-play").onclick = () => send({ type: "queue", tc: S.selTc });
  $("#b-bot").onclick = () => send({ type: "play_bot", tc: S.selTc });
  $("#b-chal").onclick = () => showChallengeCreate();
  try {
    const p = await api(`/api/users/${encodeURIComponent(u.username)}`);
    const el = $("#recent");
    if (el) el.innerHTML = matchTable(p.matches.slice(0, 8));
  } catch { /* ignore */ }
}

function matchTable(ms) {
  if (!ms.length) return `<div class="empty">${t("no_games")}</div>`;
  return `<table><thead><tr><th>${t("opponent")}</th><th>${t("tc")}</th><th>${t("result")}</th><th>${t("score")}</th><th>${t("rating")}</th><th>${t("date")}</th></tr></thead><tbody>
    ${ms.map((m) => `<tr class="link" data-href="#/m/${m.id}">
      <td>${m.bot ? "🤖 " : ""}${esc(m.opponent)} <span class="muted">(${m.opp_rating})</span></td>
      <td>${TCS[m.tc].ico} ${t(m.tc)} <span class="level-chip ${m.level}">${m.level}</span></td>
      <td class="${m.outcome}">${t(m.outcome)}</td>
      <td>${m.my_score} – ${m.opp_score}</td>
      <td>${m.rated ? `${m.rating_after} ${delta(m.rating_before, m.rating_after)}` : `<span class="muted">${t("unrated")}</span>`}</td>
      <td class="muted">${fmtDate(m.ended_at)}</td></tr>`).join("")}</tbody></table>`;
}
document.addEventListener("click", (e) => {
  const tr = e.target.closest("tr[data-href]");
  if (tr) location.hash = tr.dataset.href;
});

function showQueue(tc) {
  S.queue = { tc, since: Date.now() };
  const box = modal(`<div class="spinner"></div><h2>${t("searching")}</h2>
    <p class="muted">${TCS[tc].ico} ${t(tc)} · ${t("rating")} ${S.user.ratings[tc].rating}</p>
    <p id="q-elapsed" class="muted" style="font-variant-numeric:tabular-nums">0:00</p>
    <div id="q-bot" style="display:none;margin-bottom:12px"><p>${t("nobody")}</p>
      <button class="btn primary" id="q-botbtn">🤖 ${t("play_bot")}</button></div>
    <button class="btn ghost" id="q-cancel">${t("cancel")}</button>`);
  $("#q-cancel", box).onclick = () => { send({ type: "cancel_queue" }); S.queue = null; modal(""); };
  $("#q-botbtn", box).onclick = () => { send({ type: "play_bot", tc }); };
  clearInterval(showQueue._i);
  showQueue._i = setInterval(() => {
    if (!S.queue) return clearInterval(showQueue._i);
    const s = Math.floor((Date.now() - S.queue.since) / 1000);
    const el = $("#q-elapsed");
    if (!el) return clearInterval(showQueue._i);
    el.textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
    if (s >= 12) $("#q-bot").style.display = "block";
  }, 500);
}

function showChallengeCreate() {
  const box = modal(`<h2>${t("challenge_title")}</h2>
    <div class="tabs" style="justify-content:center">${Object.keys(TCS).map((k) => `<button data-tc="${k}" class="${k === S.selTc ? "on" : ""}">${TCS[k].ico} ${t(k)}</button>`).join("")}</div>
    <label class="row" style="justify-content:center;margin-bottom:14px"><input type="checkbox" id="ch-rated" checked> ${t("rated_game")}</label>
    <div id="ch-out"></div>
    <div class="actions"><button class="btn primary" id="ch-create">${t("create_link")}</button>
    <button class="btn ghost" id="ch-close">${t("close")}</button></div>`);
  let tc = S.selTc;
  box.querySelectorAll(".tabs button").forEach((b) => b.onclick = () => {
    tc = b.dataset.tc;
    box.querySelectorAll(".tabs button").forEach((x) => x.classList.toggle("on", x === b));
  });
  $("#ch-close", box).onclick = () => modal("");
  $("#ch-create", box).onclick = async () => {
    const { code } = await api("/api/challenge", { tc, rated: $("#ch-rated").checked });
    const link = `${location.origin}/#/c/${code}`;
    $("#ch-out").innerHTML = `<p>${t("challenge_link")}</p><div class="copybox"><input readonly value="${esc(link)}" id="ch-link"><button class="btn small" id="ch-copy">${t("copy")}</button></div>
      <div class="spinner"></div><p class="muted">${t("waiting_friend")}</p>`;
    $("#ch-create").style.display = "none";
    $("#ch-copy").onclick = () => {
      const inp = $("#ch-link");
      inp.select();
      (navigator.clipboard ? navigator.clipboard.writeText(link) : Promise.reject()).catch(() => document.execCommand("copy"));
      toast(t("copied"));
    };
  };
}

async function viewChallenge(code) {
  app().innerHTML = `<div class="auth panel" id="chal"><div class="spinner"></div></div>`;
  try {
    const c = await api(`/api/challenge/${encodeURIComponent(code)}`);
    $("#chal").innerHTML = `<div style="text-align:center">
      <div class="avatar" style="margin:0 auto 10px;width:64px;height:64px;font-size:28px">${initial(c.from)}</div>
      <h2>${esc(c.from)} <span class="muted">(${c.rating})</span></h2>
      <p>${t("challenged_you")}</p>
      <p style="font-size:18px;font-weight:700">${TCS[c.tc].ico} ${t(c.tc)} · ${c.rated ? t("rated") : t("unrated")}</p>
      ${c.online ? "" : `<p class="err">${t("offline_chal")}</p>`}
      ${S.user ? `<button class="btn primary big" id="ch-accept">${t("accept")}</button>`
        : `<a class="btn primary big" href="#/login" id="ch-login" style="display:block">${t("login_to_accept")}</a>`}</div>`;
    if (S.user) $("#ch-accept").onclick = () => send({ type: "accept_challenge", code });
    else S.afterLogin = `#/c/${code}`;
  } catch (e) {
    $("#chal").innerHTML = `<p class="err" style="text-align:center">${esc(e.message)}</p><a href="#/" class="btn" style="display:block;text-align:center">${t("play")}</a>`;
  }
}

// ---------------------------------------------------------------- battle
function onMatchStart(m) {
  S.queue = null;
  modal("");
  const offset = m.server_now * 1000 - Date.now();
  const keep = S.match && S.match.id === m.match_id ? S.match : {};
  S.match = Object.assign(keep, {
    id: m.match_id, tc: m.tc, duration: m.duration, rated: m.rated, level: m.level, tier: m.tier,
    offset, startsAt: m.starts_at * 1000, endsAt: m.ends_at * 1000, you: m.you, opponent: m.opponent, ended: false,
  });
  if (location.hash !== "#/battle") location.hash = "#/battle";
  else viewBattle();
}
const serverNow = () => Date.now() + (S.match ? S.match.offset : 0);

function viewBattle() {
  const m = S.match;
  if (!m) { location.hash = "#/"; return; }
  app().innerHTML = `<div class="battle">
    <div>
      <div class="pbar" id="bar-opp"></div>
      <div class="progress opp"><div id="prog-opp" style="width:0"></div></div>
      <div style="height:10px"></div>
      <div class="board" id="board"><div id="qarea" style="display:flex;flex-direction:column;flex:1"></div><div id="fb"></div></div>
      <div style="height:10px"></div>
      <div class="progress"><div id="prog-me" style="width:0"></div></div>
      <div class="pbar" id="bar-me"></div>
    </div>
    <div>
      <div class="clock" id="clock">0:00</div>
      <div class="side-stats" id="sidestats"></div>
      <div class="panel" style="margin-top:14px">
        <div class="row"><span>${TCS[m.tc].ico} <b>${t(m.tc)}</b></span><span class="spacer"></span>
        <span class="level-chip ${m.level}">${m.level}</span>
        <span class="level-chip">${m.rated ? t("rated") : t("unrated")}</span></div>
        <p class="muted" style="font-size:13px;margin:12px 0 0">+10 ${t("correct").toLowerCase()} · −5 ${t("wrong").toLowerCase()}</p>
        <p class="muted" style="font-size:13px;margin:6px 0 0">${t("keys")}: <kbd>1</kbd>–<kbd>4</kbd> · <kbd>Enter</kbd></p>
      </div>
    </div></div>`;
  renderBars();
  if (m.data && serverNow() >= m.startsAt) renderQuestion();
  if (m.lastfb) renderFeedback(m.lastfb);
  clearInterval(viewBattle._i);
  viewBattle._i = setInterval(tickBattle, 100);
  tickBattle();
}

function tickBattle() {
  const m = S.match;
  const clock = $("#clock");
  if (!m || !clock) return clearInterval(viewBattle._i);
  const now = serverNow();
  const board = $("#board");
  if (now < m.startsAt && !m.ended) {
    const n = Math.ceil((m.startsAt - now) / 1000);
    let cd = $("#countdown");
    if (!cd) { board.insertAdjacentHTML("beforeend", `<div class="countdown" id="countdown"></div>`); cd = $("#countdown"); }
    cd.innerHTML = `<div>${n}<small>${t("get_ready")} · vs ${esc(m.opponent.name)}</small></div>`;
    clock.classList.add("idle");
    clock.textContent = fmtClock(m.duration * 1000);
    return;
  }
  const cd = $("#countdown");
  if (cd) cd.remove();
  clock.classList.remove("idle");
  const left = Math.max(0, m.endsAt - now);
  clock.textContent = fmtClock(left);
  clock.classList.toggle("low", left < 10000);
}
const fmtClock = (ms) => { const s = Math.ceil(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; };

function renderBars() {
  const m = S.match;
  if (!m || !$("#bar-me")) return;
  const bar = (p, me) => `<div class="avatar ${me ? "me" : p.bot ? "bot" : ""}">${p.bot ? "🤖" : initial(p.name)}</div>
    <div class="pname">${esc(p.name)}${me ? ` <small>(${t("you")})</small>` : ""} <small>${p.rating}</small></div>
    <div class="pscore"><span class="okmark">✓ ${p.correct}</span><span class="nomark">✗ ${p.wrong}</span><span class="pts">${p.score}</span></div>`;
  $("#bar-me").innerHTML = bar(m.you, true);
  $("#bar-opp").innerHTML = bar(m.opponent, false);
  const max = Math.max(10, m.you.correct, m.opponent.correct) * 1.15;
  $("#prog-me").style.width = `${(m.you.correct / max) * 100}%`;
  $("#prog-opp").style.width = `${(m.opponent.correct / max) * 100}%`;
  const n = m.you.correct + m.you.wrong;
  $("#sidestats").innerHTML = `<div class="s"><div class="v">${m.you.score}</div><div class="l">${t("score")}</div></div>
    <div class="s"><div class="v">${n ? Math.round((m.you.correct / n) * 100) : 0}%</div><div class="l">${t("accuracy")}</div></div>`;
}

function renderQuestion() {
  const m = S.match;
  const qa = $("#qarea");
  if (!m || !qa || !m.data) return;
  const d = m.data;
  m.answering = false;
  const typeLbl = { meaning: t("t_meaning"), cloze: t("t_cloze"), reading: t("t_reading"), translate: t("t_translate") }[d.type];
  let prompt = "";
  if (d.type === "meaning") prompt = t("q_meaning");
  if (d.type === "cloze") prompt = t("q_cloze");
  if (d.type === "translate") prompt = t("q_translate");
  if (d.type === "reading") prompt = `${t("q_reading")} <span class="jp">${esc(d.word)}</span> ${t("q_reading2")}`;
  let body;
  if (d.type === "reading") {
    body = `<div style="margin-top:auto"><div class="reading-input"><input id="rin" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="taberu / たべる">
      <button class="btn primary" id="rsub">${t("submit")}</button></div><div class="kana-preview" id="kprev"></div></div>`;
  } else {
    const long = d.type === "translate";
    const jpOpt = d.type === "cloze";
    body = `<div class="options ${long ? "long" : ""}">${d.options.map((o, i) =>
      `<button class="opt ${jpOpt ? "jp-opt" : ""}" data-i="${i}"><span class="k">${i + 1}</span><span>${esc(o)}</span></button>`).join("")}</div>`;
  }
  qa.innerHTML = `<div class="qmeta"><span class="qtype">${t("question")} ${m.q + 1} · ${typeLbl}</span><span class="spacer"></span><span class="level-chip ${d.level}">${d.level}</span></div>
    ${sentenceHTML(d.sentence, d.tier)}
    ${d.hint ? `<div class="hint">“${esc(d.hint)}”</div>` : ""}
    <div class="qprompt">${prompt}</div>${body}`;
  if (d.type === "reading") {
    const inp = $("#rin");
    inp.focus();
    inp.oninput = () => { $("#kprev").textContent = inp.value ? "→ " + toKana(inp.value) : ""; };
    const go = () => { if (inp.value.trim()) answer(inp.value.trim()); };
    inp.onkeydown = (e) => { if (e.key === "Enter") go(); };
    $("#rsub").onclick = go;
  } else {
    qa.querySelectorAll(".opt").forEach((b) => b.onclick = () => answer(+b.dataset.i));
  }
}
document.addEventListener("keydown", (e) => {
  if (!S.match || S.match.ended || !$("#qarea")) return;
  if (e.target.tagName === "INPUT") return;
  const n = parseInt(e.key, 10);
  if (n >= 1 && n <= 4 && S.match.data && S.match.data.options) {
    const b = $(`.opt[data-i="${n - 1}"]`);
    if (b) b.click();
  }
});

function answer(given) {
  const m = S.match;
  if (!m || m.answering || m.ended) return;
  m.answering = true;
  m.lastGiven = given;
  if (typeof given === "number") {
    const b = $(`.opt[data-i="${given}"]`);
    if (b) b.style.outline = "2px solid #fff";
  }
  send({ type: "answer", match_id: m.id, q: m.q, answer: given });
}

function onFeedback(f) {
  const m = S.match;
  f.given = m.lastGiven;
  f.givenText = typeof f.given === "number" && m.data && m.data.options ? m.data.options[f.given] : f.given;
  m.lastfb = f;
  renderFeedback(f);
  const board = $("#board");
  if (board) {
    board.classList.remove("flash-ok", "flash-no");
    void board.offsetWidth;
    board.classList.add(f.ok ? "flash-ok" : "flash-no");
  }
}
function renderFeedback(f) {
  const el = $("#fb");
  if (!el) return;
  const c = f.card;
  el.innerHTML = `<div class="lastfb ${f.ok ? "ok" : "no"}"><span class="mark">${f.ok ? "✓" : "✗"}</span>
    <div class="fbtxt">${f.ok ? "" : `<span class="nomark">${esc(f.givenText)}</span> → `}<b>${esc(f.correct_text)}</b><br>
    <span class="jp">${wordFuriHTML(c.word_furi)}</span> <span class="muted">${esc(c.reading)} · ${esc(c.meaning)}</span><br>
    <span class="muted">${esc(c.translation)}</span></div></div>`;
}

function onMatchEnd(e) {
  const m = S.match;
  if (m && m.id === e.match_id) m.ended = true;
  clearInterval(viewBattle._i);
  const clock = $("#clock");
  if (clock) { clock.textContent = "0:00"; clock.classList.add("idle"); clock.classList.remove("low"); }
  const qa = $("#qarea");
  if (qa) qa.innerHTML = "";
  const ratingLine = e.rated
    ? `<div class="rating-change">${t("rating")}: <b>${e.rating_after}</b> ${delta(e.rating_before, e.rating_after)}</div>`
    : `<div class="rating-change muted">${t("unrated")}</div>`;
  const box = modal(`<div class="big-outcome ${e.outcome}">${t(e.outcome)}</div>
    <div class="muted">${TCS[e.tc].ico} ${t(e.tc)}</div>
    <div class="score-compare">
      <div class="side"><div class="n">${esc(e.you.name)}</div><div class="p">${e.you.score}</div><div class="a">${e.you.correct} ✓ · ${e.you.wrong} ✗ · ${e.accuracy}%</div></div>
      <div class="muted">vs</div>
      <div class="side"><div class="n">${esc(e.opponent.name)}</div><div class="p">${e.opponent.score}</div><div class="a">${e.opponent.correct} ✓ · ${e.opponent.wrong} ✗ · ${e.opp_accuracy}%</div></div>
    </div>${ratingLine}
    ${e.missed_added ? `<p class="c-missed" style="margin-top:0">+${e.missed_added} ${t("missed_added")}</p>` : ""}
    <div class="actions">
      <button class="btn primary" id="e-again">${t("rematch")}</button>
      <div class="play-actions" style="margin:0"><div class="two">
      <button class="btn" id="e-review">${t("review_match")}</button>
      <button class="btn" id="e-study">${t("study_missed")}</button></div></div>
      <button class="btn ghost" id="e-close">${t("close")}</button></div>`);
  const leave = (hash) => { S.match = null; modal(""); location.hash = hash; };
  $("#e-again", box).onclick = () => { S.selTc = e.tc; S.match = null; modal(""); location.hash = "#/"; setTimeout(() => send(m && m.opponent.bot ? { type: "play_bot", tc: e.tc } : { type: "queue", tc: e.tc }), 50); };
  $("#e-review", box).onclick = () => leave(`#/m/${e.match_id}`);
  $("#e-study", box).onclick = () => leave("#/study");
  $("#e-close", box).onclick = () => leave("#/");
  loadMe().catch(() => {});
}

// ---------------------------------------------------------------- study
async function viewStudy() {
  if (!S.user) return viewLogin();
  app().innerHTML = `<div class="study-wrap"><div id="study"><div class="spinner"></div></div>
    <div class="panel" style="margin-top:18px"><h3>${t("deck_progress")}</h3><div id="lvbars" class="level-bars"></div></div></div>`;
  loadStudyCard();
  api("/api/study/stats").then((s) => {
    const el = $("#lvbars");
    if (!el) return;
    el.innerHTML = Object.entries(s.by_level).map(([lv, v]) => `<div class="lbar">
      <div class="top"><span><span class="level-chip ${lv}">${lv}</span></span><span>${v.seen}/${v.total} ${t("seen")} · ${v.mature} ${t("mature")}</span></div>
      <div class="track"><div class="mat" style="width:${(v.mature / v.total) * 100}%"></div><div class="seen" style="width:${((v.seen - v.mature) / v.total) * 100}%"></div></div></div>`).join("");
  }).catch(() => {});
}

async function loadStudyCard() {
  const d = await api("/api/study/next");
  const el = $("#study");
  if (!el) return;
  S.study = d.counts;
  renderChrome();
  const c = d.counts;
  const counts = `<div class="counts"><span class="c-new">${c.new}<small>${t("new")}</small></span>
    <span class="c-learn">${c.learning}<small>${t("learning")}</small></span>
    <span class="c-rev">${c.review}<small>${t("review")}</small></span>
    ${c.missed ? `<span class="c-missed">${c.missed}<small>${t("missed")}</small></span>` : ""}</div>`;
  if (!d.card) {
    el.innerHTML = `${counts}<div class="study-card" style="text-align:center;justify-content:center">
      <div style="font-size:48px">🎉</div><h2>${t("done_title")}</h2><p class="muted">${t("done_sub")}</p>
      ${c.next_due ? `<p class="muted">${t("next_due")}: ${fmtIvl(Math.max(0, c.next_due - Date.now() / 1000))}</p>` : ""}
      <a href="#/" class="btn primary" style="align-self:center">${t("play")}</a></div>`;
    return;
  }
  const card = d.card;
  const kindLbl = { new: t("new"), learning: t("learning"), relearning: t("learning"), review: t("review"), missed: t("missed") }[d.kind];
  const kindCls = { new: "c-new", learning: "c-learn", relearning: "c-learn", review: "c-rev", missed: "c-missed" }[d.kind];
  el.innerHTML = `${counts}<div class="study-card">
    <div class="kind"><span class="level-chip ${card.level}">${card.level}</span> <b class="${kindCls}" style="font-size:13px;margin-left:6px">${kindLbl}</b></div>
    <div id="front">${sentenceHTML(card.sentence, d.tier)}</div>
    <div class="qprompt">${t("study_prompt")}</div>
    <div id="back"></div>
    <div style="margin-top:auto" id="sbtns"><button class="btn primary big" id="show">${t("show_answer")} <kbd>Space</kbd></button></div>
  </div>`;
  const reveal = () => {
    $("#front").innerHTML = sentenceHTML(card.sentence, "full");
    $("#back").innerHTML = `<div class="answer-block">
      <div class="answer-word">${wordFuriHTML(card.word_furi)}</div>
      <div class="answer-reading">${esc(card.reading)}</div>
      <div class="answer-meaning">${esc(card.meaning)}</div>
      <div class="answer-tr">${esc(card.translation)}</div></div>`;
    const iv = d.intervals;
    $("#sbtns").innerHTML = `<div class="grade-row">
      ${[[1, "again"], [2, "hard"], [3, "good"], [4, "easy"]].map(([g, k]) => `<button class="grade g${g}" data-g="${g}">${t(k)}<small>${fmtIvl(iv[g])} · ${g}</small></button>`).join("")}</div>`;
    $("#sbtns").querySelectorAll(".grade").forEach((b) => b.onclick = () => grade(+b.dataset.g));
    S.studyState = "back";
  };
  const grade = async (g) => {
    if (S.studyState !== "back") return;
    S.studyState = "busy";
    await api("/api/study/answer", { card_id: card.id, grade: g });
    loadStudyCard();
  };
  S.studyState = "front";
  S.studyReveal = reveal;
  S.studyGrade = grade;
  $("#show").onclick = reveal;
}
document.addEventListener("keydown", (e) => {
  if (!$("#study") || e.target.tagName === "INPUT") return;
  if (S.studyState === "front" && (e.key === " " || e.key === "Enter")) { e.preventDefault(); S.studyReveal(); }
  else if (S.studyState === "back") {
    if (e.key === " " || e.key === "Enter") { e.preventDefault(); S.studyGrade(3); }
    const n = parseInt(e.key, 10);
    if (n >= 1 && n <= 4) S.studyGrade(n);
  }
});

// ---------------------------------------------------------------- leaderboard
async function viewLeaderboard(tc) {
  tc = TCS[tc] ? tc : S.selTc;
  app().innerHTML = `<h1>🏆 ${t("leaderboard")}</h1>
    <div class="tabs">${Object.keys(TCS).map((k) => `<button data-tc="${k}" class="${k === tc ? "on" : ""}">${TCS[k].ico} ${t(k)}</button>`).join("")}</div>
    <div class="panel flush" id="lb"><div class="spinner"></div></div>`;
  app().querySelectorAll(".tabs button").forEach((b) => b.onclick = () => { location.hash = `#/leaderboard/${b.dataset.tc}`; });
  const rows = await api(`/api/leaderboard?tc=${tc}`);
  $("#lb").innerHTML = rows.length ? `<table><thead><tr><th>#</th><th>${t("player")}</th><th>${t("rating")}</th><th>${t("games")}</th><th>${t("wld")}</th></tr></thead><tbody>
    ${rows.map((r, i) => `<tr class="link" data-href="#/u/${encodeURIComponent(r.username)}"><td>${i < 3 ? ["🥇", "🥈", "🥉"][i] : i + 1}</td>
      <td><b>${esc(r.username)}</b>${S.user && S.user.username === r.username ? ` <span class="muted">(${t("you")})</span>` : ""}</td>
      <td><b>${r.rating}</b></td><td>${r.games}</td><td><span class="win">${r.wins}</span> / <span class="loss">${r.losses}</span> / <span class="draw">${r.draws}</span></td></tr>`).join("")}
    </tbody></table>` : `<div class="empty">${t("leader_empty")}</div>`;
}

// ---------------------------------------------------------------- profile
async function viewProfile(name) {
  app().innerHTML = `<div class="spinner"></div>`;
  let p;
  try { p = await api(`/api/users/${encodeURIComponent(name)}`); } catch (e) { app().innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  let tab = S.selTc;
  app().innerHTML = `<div class="prof-head"><div class="avatar me">${initial(p.username)}</div>
      <div><h1 style="margin:0">${esc(p.username)}</h1><div class="muted">${t("joined")} ${fmtDate(p.joined)} · ${p.studied} ${t("seen")}</div></div></div>
    <div class="rating-cards">${Object.keys(TCS).map((k) => { const r = p.ratings[k]; return `<div class="rc">
      <div class="muted">${TCS[k].ico} ${t(k)}</div><div class="v">${r.rating}</div>
      <div class="wld">${r.games} ${t("games")} · <span class="win">${r.wins}</span> / <span class="loss">${r.losses}</span> / <span class="draw">${r.draws}</span></div></div>`; }).join("")}</div>
    <div class="panel" style="margin-bottom:18px"><div class="row"><h3 style="margin:0">${t("rating_history")}</h3><span class="spacer"></span>
      <div class="tabs" style="margin:0" id="ptabs">${Object.keys(TCS).map((k) => `<button data-tc="${k}">${t(k)}</button>`).join("")}</div></div>
      <div class="chart" id="chart"></div></div>
    <div class="panel flush"><div style="padding:16px 18px 4px"><h3>${t("match_history")}</h3></div>${matchTable(p.matches)}</div>`;
  const draw = () => {
    $("#ptabs").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.tc === tab));
    $("#chart").innerHTML = ratingChart(p.history[tab]);
  };
  $("#ptabs").querySelectorAll("button").forEach((b) => b.onclick = () => { tab = b.dataset.tc; draw(); });
  draw();
}

function ratingChart(hist) {
  const pts = [800, ...hist.map((h) => h[1])];
  if (pts.length < 2) return `<div class="empty">${t("no_games")}</div>`;
  const W = 800, H = 220, P = 34;
  const lo = Math.min(...pts) - 20, hi = Math.max(...pts) + 20;
  const x = (i) => P + (i / (pts.length - 1)) * (W - P - 10);
  const y = (v) => H - 24 - ((v - lo) / (hi - lo)) * (H - 44);
  const line = pts.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
  const grid = [lo + 20, (lo + hi) / 2, hi - 20].map((v) => `<line x1="${P}" x2="${W - 10}" y1="${y(v)}" y2="${y(v)}" stroke="#45423e"/>
    <text x="${P - 6}" y="${y(v) + 4}" fill="#989795" font-size="11" text-anchor="end">${Math.round(v)}</text>`).join("");
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${grid}
    <path d="${line} L${x(pts.length - 1)},${H - 24} L${x(0)},${H - 24} Z" fill="#81b64c22"/>
    <path d="${line}" fill="none" stroke="#81b64c" stroke-width="2.5" vector-effect="non-scaling-stroke"/>
    <circle cx="${x(pts.length - 1)}" cy="${y(pts[pts.length - 1])}" r="4" fill="#81b64c"/></svg>`;
}

// ---------------------------------------------------------------- match replay
async function viewMatch(id) {
  app().innerHTML = `<div class="spinner"></div>`;
  let d;
  try { d = await api(`/api/matches/${encodeURIComponent(id)}`); } catch (e) { app().innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  const win = d.result === "p1" ? d.p1.name : d.result === "p2" ? d.p2.name : null;
  const side = (p, isWin) => `<div class="side"><div class="n">${esc(p.name)} ${isWin ? "👑" : ""}</div><div class="p">${p.score}</div>
    <div class="a">${p.correct} ✓ · ${p.wrong} ✗ ${d.rated ? `· ${p.after} ${delta(p.before, p.after)}` : ""}</div></div>`;
  const ans = (a) => a ? `<span class="${a.ok ? "okmark" : "nomark"}">${a.ok ? "✓" : "✗"}</span> ${esc(a.given)} <span class="muted">${(a.ms / 1000).toFixed(1)}${t("ms")}</span>` : `<span class="muted">${t("no_answer")}</span>`;
  const typeLbl = { meaning: t("t_meaning"), cloze: t("t_cloze"), reading: t("t_reading"), translate: t("t_translate") };
  app().innerHTML = `<h1>${TCS[d.tc].ico} ${t(d.tc)} <span class="level-chip ${d.level}">${d.level}</span> <span class="level-chip">${d.rated ? t("rated") : t("unrated")}</span></h1>
    <div class="panel" style="margin-bottom:18px"><div class="score-compare" style="margin:0">${side(d.p1, win === d.p1.name)}
      <div class="muted">${win ? "" : t("draw")}<br>${fmtDate(d.ended_at)}</div>${side(d.p2, win === d.p2.name)}</div></div>
    <div class="panel flush"><table class="replay-q"><thead><tr><th>#</th><th>${t("question")}</th><th>${esc(d.p1.name)}</th><th>${esc(d.p2.name)}</th></tr></thead><tbody>
    ${d.questions.map((q) => `<tr><td class="muted">${q.i + 1}</td>
      <td><div class="muted" style="font-size:12px;font-weight:700">${typeLbl[q.type].toUpperCase()} · ${esc(q.card.word)} (${esc(q.card.reading)}) — ${esc(q.card.meaning)}</div>
        ${sentenceHTML(q.card.sentence, "full", "").replace('class="sentence', 'style="font-size:17px;text-align:left;line-height:1.9" class="sentence')}
        <div class="muted" style="font-size:13px">${esc(q.card.translation)}</div></td>
      <td>${ans(q.p1)}</td><td>${ans(q.p2)}</td></tr>`).join("")}</tbody></table></div>`;
}

// ---------------------------------------------------------------- auth & settings
function authView(mode) {
  const isReg = mode === "register";
  app().innerHTML = `<div class="auth panel"><h1>${isReg ? t("register") : t("login")}</h1>
    <form id="af"><div class="field"><label>${t("username")}</label><input name="username" autocomplete="username" required></div>
    <div class="field"><label>${t("password")}</label><input name="password" type="password" autocomplete="${isReg ? "new-password" : "current-password"}" required></div>
    <div class="err" id="aerr"></div>
    <button class="btn primary big">${isReg ? t("register") : t("login")}</button></form>
    <p class="muted" style="text-align:center">${isReg ? t("have_account") : t("no_account")}
    <a href="#/${isReg ? "login" : "register"}" style="color:var(--green);font-weight:700">${isReg ? t("login") : t("register")}</a></p></div>`;
  $("#af").onsubmit = async (e) => {
    e.preventDefault();
    const f = new FormData(e.target);
    try {
      await api(`/api/${isReg ? "register" : "login"}`, { username: f.get("username"), password: f.get("password") });
      if (isReg && store.get("lang")) await api("/api/settings", { lang: store.get("lang") });
      await loadMe();
      location.hash = S.afterLogin || "#/";
      S.afterLogin = null;
    } catch (err) { $("#aerr").textContent = err.message; }
  };
}
const viewLogin = () => authView("login");
const viewRegister = () => authView("register");

function viewSettings() {
  if (!S.user) return viewLogin();
  app().innerHTML = `<div class="auth panel"><h1>⚙ ${t("settings")}</h1>
    <div class="field"><label>${t("lang_label")}</label><select id="s-lang"><option value="en">English</option><option value="sv">Svenska</option></select></div>
    <div class="field"><label>${t("new_per_day")}</label><input id="s-new" type="number" min="0" max="100" value="${S.user.new_per_day}"></div>
    <button class="btn primary big" id="s-save">${t("save")}</button>
    <div style="height:14px"></div><button class="btn ghost" id="s-out" style="width:100%">${t("logout")}</button></div>`;
  $("#s-lang").value = S.user.lang;
  $("#s-save").onclick = async () => {
    S.user = await api("/api/settings", { lang: $("#s-lang").value, new_per_day: +$("#s-new").value });
    S.lang = S.user.lang;
    await loadMe();
    viewSettings();
    toast(t("saved"));
  };
  $("#s-out").onclick = async () => {
    await api("/api/logout", {});
    S.user = null;
    if (S.ws) S.ws.close();
    await loadMe();
    location.hash = "#/";
  };
}

// ---------------------------------------------------------------- boot
loadMe().then(route_).catch((e) => { app().innerHTML = `<div class="empty">Server unreachable: ${esc(e.message)}</div>`; });
