import sqlite3
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from werkzeug.security import check_password_hash, generate_password_hash

from db_tour import ensure_language_schema, language_id_for
from User import User

DB_NAME = "istanbul.db"
PROFILE_UPLOAD_FOLDER = (
    Path(__file__).resolve().parent / "static" / "images" / "profile_uploads"
)


def getUserById(id):
    ensureUserProfileColumns()
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE id=?", (id,))
    user = cursor.fetchone()
    conn.close()
    return user


def getUserByEmail(email):
    ensureUserProfileColumns()
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user


def createUser(name, surname, email, user_type, profile_picture, password):
    ensureUserProfileColumns()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO Users (name, surname, email, type, profile_picture, password) VALUES (?, ?, ?, ?, ?, ?)",
        (name, surname, email, user_type, profile_picture, hashed_password),
    )
    conn.commit()
    conn.close()


def ensure_admin_account(email="admin@example.com", password="admin123"):
    """Create the built-in administrator once, without replacing user changes."""
    ensureUserProfileColumns()
    conn = sqlite3.connect(DB_NAME)
    existing = conn.execute(
        "SELECT id FROM Users WHERE lower(email) = lower(?)", (email,)
    ).fetchone()
    if existing is None:
        conn.execute(
            "INSERT INTO Users (name, surname, email, type, profile_picture, password) VALUES (?, ?, ?, ?, ?, ?)",
            (
                "Admin",
                "Account",
                email,
                "admin",
                None,
                generate_password_hash(password),
            ),
        )
        conn.commit()
    conn.close()


def checkLogin(email, password):
    user = getUserByEmail(email)

    if user is None:
        return None
    else:
        stored_hash = user["password"]
        if check_password_hash(stored_hash, password):
            return user
    return None


def ensureUserProfileColumns():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(Users)")
    columns = {column[1] for column in cursor.fetchall()}
    if "location" not in columns:
        cursor.execute("ALTER TABLE Users ADD COLUMN location TEXT")
    conn.commit()
    conn.close()


def updateUserProfile(user_id, name, surname, email, location, profile_picture):
    ensureUserProfileColumns()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Users
        SET name = ?, surname = ?, email = ?, location = ?, profile_picture = ?
        WHERE id = ?
        """,
        (name, surname, email, location, profile_picture, user_id),
    )
    conn.commit()
    conn.close()


def updateUserPassword(user_id, old_password, new_password):
    user = getUserById(user_id)
    if user is None or not check_password_hash(user["password"], old_password):
        return False

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Users SET password = ? WHERE id = ?",
        (generate_password_hash(new_password), user_id),
    )
    conn.commit()
    conn.close()
    return True


def user_from_db_row(row):
    return User(
        id=row["id"],
        name=row["name"],
        surname=row["surname"],
        email=row["email"],
        user_type=row["type"],
        profile_picture=row["profile_picture"],
        location=row["location"],
    )


def save_user_languages(user_id, language_names):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    ensure_language_schema(conn)
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS UserLanguages (user_id INTEGER NOT NULL, language_id INTEGER NOT NULL, PRIMARY KEY (user_id, language_id))"
    )
    cursor.execute("DELETE FROM UserLanguages WHERE user_id = ?", (user_id,))
    for language in language_names:
        language_id = language_id_for(language)
        if language_id:
            cursor.execute(
                "INSERT OR IGNORE INTO UserLanguages (user_id, language_id) VALUES (?, ?)",
                (user_id, language_id),
            )
    conn.commit()
    conn.close()


def save_profile_picture(uploaded_file):
    if uploaded_file is None or uploaded_file.filename == "":
        return None

    try:
        image = Image.open(uploaded_file)
        image.verify()
        uploaded_file.stream.seek(0)
        image = Image.open(uploaded_file).convert("RGB")
    except (UnidentifiedImageError, OSError):
        return None

    width, height = image.size
    crop_size = min(width, height)
    left = (width - crop_size) // 2
    top = (height - crop_size) // 2
    image = image.crop((left, top, left + crop_size, top + crop_size))
    image = image.resize((420, 420))

    PROFILE_UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    filename = f"profile-{uuid4().hex}.jpg"
    destination = PROFILE_UPLOAD_FOLDER / filename
    image.save(destination, "JPEG", quality=86, optimize=True)
    return f"/static/images/profile_uploads/{filename}"
