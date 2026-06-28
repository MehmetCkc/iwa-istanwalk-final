# ISTANWALK

ISTANWALK is a Flask and SQLite web application for managing Free Walking Tours in Istanbul. The platform supports guide accounts, participant accounts, public tour browsing, reservations, guide reporting after completed tours, and an optional administrator dashboard.
## Local setup

Create a virtual environment, install dependencies, and run the Flask app:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask run
```

Open the app at:

```text
http://127.0.0.1:5000/
```

The project expects the included SQLite database file `istanbul.db` to be present in the project root.

## Sample accounts

Administrator:

- `admin@example.com` / `admin123`

Guides:

- `utkusenturk@example.com` / `utku123`
- `ege@example.com` / `ege123`
- `selin@example.com` / `selin123`
- `bora@example.com` / `bora123`
- `lina@example.com` / `lina123`
- `derya@example.com` / `derya123`
- `mert@example.com` / `mert123`

Participants:

- `kenanyildiz@example.com` / `kenan123`
- `defneakbulut@example.com` / `defne123`
- `mehradyousefi@example.com` / `mehrad123`
- `ayla@example.com` / `ayla123`
- `mina@example.com` / `mina123`
- `jonas@example.com` / `jonas123`
- `nina@example.com` / `nina123`
- `ozan@example.com` / `ozan123`

## Deployment

```text
PythonAnywhere URL: mehmetckc.pythonanywhere.com
```
