# 🧮 Mathematics Quiz Challenge App

A full-featured Streamlit quiz game with Excel as its database.

## Setup

```bash
cd Mathematics_Quiz_App
pip install -r requirements.txt
streamlit run app.py
```

On first launch the app automatically creates `database/*.xlsx` and seeds
270 starter questions (6 categories × 3 difficulties × 15 questions) so
it's playable immediately. Admins can add/edit/delete questions afterward.

## Default Admin Login

- Username: `admin`
- Password: `admin123`

Override these via environment variables before launching:

```bash
export QUIZ_ADMIN_USERNAME="youradmin"
export QUIZ_ADMIN_PASSWORD="a-strong-password"
```

## Configuring the WhatsApp reward button

Edit `ADMIN_WHATSAPP_NUMBER` at the top of `pages/leaderboard.py` (digits
only, with country code, e.g. `"15551234567"`).

## Project Structure

```
Mathematics_Quiz_App/
├── app.py                   # Entry point: session state, sidebar, routing
├── database/                # Auto-created Excel "database" files
├── pages/                   # One module per screen (render() function each)
│   ├── login.py / register.py
│   ├── dashboard.py
│   ├── quiz.py               # Setup → active game (20s timer) → results
│   ├── performance.py        # "My Performance" analytics
│   ├── leaderboard.py
│   ├── profile.py
│   └── admin.py              # Admin login + question/user mgmt + analytics
├── utils/
│   ├── database_manager.py   # All Excel read/write logic
│   ├── authentication.py     # Password hashing, login/register validation
│   ├── scoring.py            # Percentage + performance-message helpers
│   ├── timer.py               # 20s countdown helpers (used with st.fragment)
│   ├── analytics.py          # Plotly chart builders for admin dashboard
│   └── question_generator.py # Starter question bank generator
└── requirements.txt
```

## Notes on design choices

- **Routing**: pages are plain Python modules with a `render()` function
  called from `app.py`'s own sidebar router — not Streamlit's native
  `pages/` auto-discovery — so that login/admin gating applies
  consistently to every screen and session state stays unified.
- **Timer**: implemented with a wall-clock timestamp in `session_state`,
  displayed via `st.fragment(run_every=1)` so it ticks down once per
  second without rerunning (and losing state in) the rest of the app.
- **Passwords**: stored as PBKDF2-HMAC-SHA256 hashes (salted), never
  plaintext.
- **Concurrency**: writes to each Excel file are guarded by an in-process
  lock — sufficient for a typical single-server Streamlit deployment.
