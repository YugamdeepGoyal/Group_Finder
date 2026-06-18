# Forgemate — Builders Directory (Flask app)

A real, working version of the Forgemate mockup: Flask backend, SQLite database,
session-based login, and full CRUD for projects, join requests, and profiles.

## 1. Requirements

- Python 3.9+

## 2. Setup

Open a terminal in this folder, then:

```bash
# (optional but recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
# if your system blocks global pip installs, use:
# pip install -r requirements.txt --break-system-packages
```

## 3. Run it

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

The first time it runs, it will automatically create `forgemate.db` (a SQLite
file right in this folder) and seed it with 6 demo users and 6 demo projects.
Delete `forgemate.db` any time you want a fresh start.

## 4. Log in

Use any of these demo accounts (password for all: `forgemate123`):

| Username | Role |
|---|---|
| alexkim | Full-Stack / Smart Contract Lead |
| mayarodriguez | React Developer |
| jamessato | ML Engineer |
| lenapark | Lead UX Designer |
| saraahmed | Solidity Developer |
| kevinpatel | Systems / Indexing Engineer |

Or click "Sign up" to create your own account.

## 5. What you can do

- Browse the directory with search, status, hackathon, and skill filters
- Click into a project to see its roster, open roles, and apply to join
- Post a new project with custom roles
- Approve or decline join requests in your Inbox (badge shows pending count)
- Edit your profile and manage your skills

## Notes

- This is a local/demo app: CSRF protection (Flask-WTF) was intentionally left
  out to keep things simple. Add it before exposing this beyond localhost.
- `SECRET_KEY` in `app.py` is a placeholder — change it before any real deployment.
