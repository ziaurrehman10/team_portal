# AI & Data Science — Team Portal

A tiny Streamlit app for a 3-person team to track and compare each
other's **projects** and **coursework/grades** in one place.

## Features
- **Team Dashboard** — public view, side-by-side cards for all 3 members showing their projects (with status badges) and coursework/grades. No login needed to view.
- **Slot claiming** — 3 fixed member slots. Each person claims their own slot once with a username + password (sidebar → "Claim a slot").
- **My Profile** — after logging in, edit your display name/bio and add, edit, or delete your own projects and coursework entries.
- Data is stored locally in a SQLite file (`portal.db`), created automatically on first run.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open the local URL it prints (usually http://localhost:8501).

## First-time setup (all 3 members)
1. Open the app.
2. In the sidebar, go to the **"Claim a slot"** tab.
3. Pick an unclaimed slot (Member 1/2/3), enter your name, a username, and a password.
4. Switch to **"Log in"** and sign in.
5. Go to the **"My Profile"** tab to add your projects and coursework.

## Deploying for free (recommended: Streamlit Community Cloud)
1. Push this folder to a **public or private GitHub repo**.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **"New app"**, select your repo/branch, and set the main file to `app.py`.
4. Click **Deploy**. You'll get a shareable URL like `https://your-app.streamlit.app`.
5. Send that link to your 2 teammates so they can each claim their slot.

## Alternative: Hugging Face Spaces
1. Create a new Space → SDK: **Streamlit**.
2. Upload `app.py` and `requirements.txt` (or connect the GitHub repo).
3. The Space builds and gives you a public URL automatically.

## ⚠️ Important note on data persistence
`portal.db` is a plain file next to `app.py`. On Streamlit Community
Cloud and HF Spaces, this file persists while the app instance stays
"awake," but it **can be reset** if the app sleeps for a long time,
gets redeployed, or the underlying container restarts. For a course
project this is normally fine, but if you want guaranteed permanent
storage, consider:
- Periodically exporting data (see `export_data()` you can add, or just
  keep re-adding entries — coursework/projects are quick to re-enter), or
- Swapping SQLite for a small hosted database (e.g. a free tier on
  Supabase, Turso, or Google Sheets via API) — ask if you'd like help
  wiring one of these in.

## Project structure
```
team-portal/
├── app.py              # the entire app (UI + DB logic)
├── requirements.txt    # just streamlit
└── README.md
```
