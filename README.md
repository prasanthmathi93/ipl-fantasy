# IPL Fantasy League

A mobile-friendly fantasy cricket web app for private leagues with friends and
family. Create a league, share the invite code, pick your XI from IPL squads,
and battle on the leaderboard all tournament long.

**Stack:** Python (Flask) + SQLite, server-rendered pages, hand-written
mobile-first CSS. No app-store install needed — everyone plays from their
phone browser.

## Features

- **Accounts** — register with name/email/password (hashed with Werkzeug);
  the first registered user becomes the admin.
- **Private leagues** — create a league, get a 6-character invite code;
  friends join from their phones with the code.
- **Team builder** — pick 11 players from IPL squads with all rules
  enforced server-side:
  - 100-credit budget, max 7 players from one IPL team
  - Role quotas: WK 1–4, BAT 3–6, AR 1–4, BOWL 3–6
  - Captain (2× points) and vice-captain (1.5×), must be distinct
  - Teams lock at a configurable deadline (default: first match of the
    tournament); locked leagues reject changes.
- **Live data** — CricketData.org (CricAPI v1) feed for fixtures, squads and
  scorecards, with aggressive caching (see Quota budget below).
- **Scoring engine** — IPL fantasy-style points: runs, boundaries, milestones,
  strike-rate bands, wickets, hauls, maidens, economy bands, catches,
  stumpings, run-outs, duck penalty.
- **Admin panel** (`/admin`, admin users only):
  - one-click refresh of squads & schedule from the API,
  - score sync for live/completed matches,
  - **manual score entry / override** per match (the fallback if the API is
    unreachable or its data looks wrong),
  - set the team-lock deadline per league,
  - **health check** (`/admin/health`, JSON): verifies the API key works
    right after deploy, shows today's quota usage and cache freshness.
- **Views** — dashboard, per-league leaderboard, fixtures (live/upcoming/
  completed), "my team" with season points, per-player points breakdown per
  match.

## Quickstart (local)

```bash
cd ipl-fantasy
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Optional (recommended):
export SECRET_KEY="a-long-random-string"
export CRICKETDATA_API_KEY="your-key-from-cricketdata.org"

python run.py
# open http://localhost:5000
```

On first boot the app seeds **sample IPL 2026 data**: 10 teams × 12 players,
4 completed matches with full scorecards, 6 upcoming fixtures — so you can
register, create a league, join via code, build a team and see the leaderboard
immediately. IPL 2027 squads/schedule aren't published yet (season expected
~Mar–May 2027); when they are, hit **Refresh squads & schedule** in the admin
panel to pull the real data from the API.

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SECRET_KEY` | yes (prod) | `dev-secret-change-me` | Flask session signing. Generate a random one per deploy. |
| `CRICKETDATA_API_KEY` | for live data | _(empty)_ | Your CricketData.org API key. Paste it into your host's env settings — never commit it. The app works without it (sample data + manual entry). |
| `DATABASE_URL` | no | `sqlite:///fantasy.db` | SQLAlchemy URL. Use Postgres in production (see below). |
| `DAILY_API_CAP` | no | `95` | Hard safety cap under the 100 hits/day free tier. |
| `PORT` | no | `5000` | Dev server port (`run.py`); hosts like Render set this themselves. |

## CricketData API quota budget (free tier = 100 hits/day)

Every real HTTP call is logged to the DB and refused once the daily cap is
hit (the app keeps working on cached/manual data). Caching is aggressive:

| Operation | Cost | Trigger |
|---|---|---|
| Schedule refresh (`/matches`, paginated) | ~1–6 hits | Admin button only; 24h cache → 0 hits when fresh |
| Squad refresh (`/match_squad`) | ~1 hit/match (≤8) | Admin button only; 7d cache → 0 hits when fresh |
| Live score sync (`/match_scorecard`) | 1 hit/match, only inside the match window (start → +4h) | Admin button only |
| Final scorecard | 1 hit/match | Same as above (6h cache) |
| Health check (`/currentMatches`) | 1 hit | Deploy-time / on demand |

Busy-day worst case ≈ 23 hits — comfortably under the cap. **Caveat:**
player-level scorecards/squads may require a paid CricAPI plan (their docs
gate these behind fantasy-enabled matches/credits). The app treats any
scorecard failure as *"API scorecards unavailable — use manual entry"*, so a
free key + the admin manual-entry page is a fully working setup.

## Deploy to Render (free)

1. Push this folder to a GitHub repo.
2. In Render: **New → Blueprint**, point it at the repo (`render.yaml` is
   included). Or create a **Web Service** manually:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn 'run:app' --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
3. In the service's **Environment** tab, add:
   - `CRICKETDATA_API_KEY` = your key from cricketdata.org
   - `DATABASE_URL` = a Postgres URL (**important:** Render's free filesystem
     is ephemeral — SQLite would reset on every restart; Render offers free
     Postgres)
   - `SECRET_KEY` is auto-generated by `render.yaml`; set one manually if you
     skip the Blueprint.
4. Open the app, register (you become admin), then visit `/admin/health` to
   confirm the API key is valid.

**Railway / Fly.io:** same idea — `Dockerfile` is included. Set the env vars
above (`SECRET_KEY`, `CRICKETDATA_API_KEY`, `DATABASE_URL`) and expose the
`$PORT` the platform assigns.

## Scoring rules (summary)

Batting: +1/run, +1 per four, +2 per six; 30+ runs +4 / 50 +8 / 100 +16
(highest only); duck −2 (BAT/WK/AR); strike-rate bonus/penalty in bands
(≥170 +6 … <50 −6, min 10 balls). Bowling: +25/wicket; 3w +4 / 4w +8 /
5w +16 (highest only); +12/maiden; economy bands (<5 +6 … >12 −6, min
2 overs). Fielding: catch +8, stumping +12, direct run-out +12, assisted +6.
Captain ×2, vice-captain ×1.5. Full table with per-event breakdowns is shown
on each match page.

## Project layout

```
ipl-fantasy/
├── app/
│   ├── __init__.py      # Flask app factory, blueprint registration
│   ├── models.py        # SQLAlchemy models (User, League, Player, …)
│   ├── auth.py          # register / login / logout
│   ├── leagues.py       # create / join / dashboard / league home
│   ├── teams.py         # team builder + server-side validation
│   ├── matches.py       # landing, fixtures, match detail
│   ├── scoring.py       # fantasy points engine (pure functions)
│   ├── data_api.py      # CricAPI client, quota guard, caching, health check
│   ├── admin.py         # admin panel, manual score entry
│   ├── templates/       # 14 mobile-first Jinja templates
│   └── static/          # style.css + app.js (vanilla)
├── seed/sample_data.py  # IPL 2026 sample season (idempotent seed)
├── config.py            # env-var config
├── run.py               # dev entry point
├── requirements.txt
├── Dockerfile
├── render.yaml
└── README.md
```

## Verified working

43 automated end-to-end checks pass (`/tmp/itest.py` run during development):
register/login/logout, first-user-is-admin, league create + invite-code format,
case-insensitive join, bad-code rejection, member/non-member access control,
valid team save, all validation branches (11 players, 100 credits, 7-per-team,
role quotas, C/VC rules, locked-league rejection), standings math, fixtures /
match-detail / my-team rendering, admin 403 for non-admins, manual score entry
with recompute, and the API layer exercised with mocked HTTP (quota logging,
cache hits, cap refusal, health-check branches, no key leakage). The live
CricAPI was **not** called from the build machine (no network route) — confirm
your key with `/admin/health` after deploy.
