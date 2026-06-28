import sqlite3
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

DB_NAME = "istanbul.db"
STATIC_IMAGE_ROOT = Path(__file__).resolve().parent / "static" / "images"
AVAILABLE_LANGUAGES = ["English", "Italian", "Spanish", "Portuguese", "German"]
LANGUAGE_IDS = {name: index for index, name in enumerate(AVAILABLE_LANGUAGES, start=1)}
FALLBACK_IMAGES = [
    "images/sultanahmet-3.svg",
    "images/sultanahmet-2.svg",
    "images/sultanahmet-5.svg",
    "images/pera-2.svg",
    "images/pera-3.svg",
]


def db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def canonical_language_name(language):
    clean_language = (language or "").strip()
    aliases = {
        "portugese": "Portuguese",
        "portuguese": "Portuguese",
    }
    return aliases.get(clean_language.lower(), clean_language)


def language_id_for(language):
    return LANGUAGE_IDS.get(canonical_language_name(language))


def ensure_language_schema(conn):
    # Normalize legacy language rows to the fixed IDs used by form values.
    # INSERT/UPDATE OR IGNORE keeps this migration safe to run on every start.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS Languages (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS TourLanguages (tour_id INTEGER NOT NULL, language_id INTEGER NOT NULL, PRIMARY KEY (tour_id, language_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS UserLanguages (user_id INTEGER NOT NULL, language_id INTEGER NOT NULL, PRIMARY KEY (user_id, language_id))"
    )

    rows = conn.execute("SELECT id, name FROM Languages").fetchall()
    for row in rows:
        name = canonical_language_name(row["name"])
        if name in LANGUAGE_IDS:
            fixed_id = LANGUAGE_IDS[name]
            conn.execute(
                "UPDATE OR IGNORE TourLanguages SET language_id = ? WHERE language_id = ?",
                (fixed_id, row["id"]),
            )
            conn.execute(
                "UPDATE OR IGNORE UserLanguages SET language_id = ? WHERE language_id = ?",
                (fixed_id, row["id"]),
            )

    conn.execute("DELETE FROM TourLanguages WHERE language_id NOT BETWEEN 1 AND 5")
    conn.execute("DELETE FROM UserLanguages WHERE language_id NOT BETWEEN 1 AND 5")
    conn.execute(
        "DELETE FROM TourLanguages WHERE rowid NOT IN (SELECT MIN(rowid) FROM TourLanguages GROUP BY tour_id, language_id)"
    )
    conn.execute(
        "DELETE FROM UserLanguages WHERE rowid NOT IN (SELECT MIN(rowid) FROM UserLanguages GROUP BY user_id, language_id)"
    )
    conn.execute("DELETE FROM Languages")
    for name, language_id in LANGUAGE_IDS.items():
        conn.execute(
            "INSERT INTO Languages (id, name) VALUES (?, ?)", (language_id, name)
        )


def split_time_language(label):
    time_part, separator, language_part = (label or "").partition(" - ")
    return format_departure_time(time_part.strip()), (
        canonical_language_name(language_part.strip()) if separator else ""
    )


def createTour(
    name,
    description,
    max_participants,
    meeting_point,
    guide_ids,
    languageIds,
    tour_type,
    duration_minutes=120,
):
    ensure_tour_schema()
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Tours (name, description, max_participants, meeting_point, type, duration_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                max_participants,
                meeting_point,
                tour_type,
                duration_minutes,
            ),
        )
        tour_id = cursor.lastrowid

        for guide_id in guide_ids:
            cursor.execute(
                "INSERT INTO TourGuides (id_guide, id_tour) VALUES (?, ?)",
                (guide_id, tour_id),
            )

        for language in languageIds:
            language_id = language_id_for(language)
            if language_id:
                cursor.execute(
                    "INSERT INTO TourLanguages (tour_id, language_id) VALUES (?, ?)",
                    (tour_id, language_id),
                )
        return tour_id


def ensure_tour_schema():
    with db_connection() as conn:
        cursor = conn.cursor()
        ensure_language_schema(conn)
        cursor.execute("PRAGMA table_info(Tours)")
        columns = {column[1] for column in cursor.fetchall()}
        if "type" not in columns:
            cursor.execute("ALTER TABLE Tours ADD COLUMN type TEXT")
        if "duration_minutes" not in columns:
            cursor.execute(
                "ALTER TABLE Tours ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 120"
            )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS TourDepartures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tour_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                language TEXT,
                FOREIGN KEY(tour_id) REFERENCES Tours(id)
            )
            """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS TourCompletions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tour_id INTEGER NOT NULL,
                guide_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                attendance INTEGER NOT NULL,
                proof_image TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tour_id, guide_id, date, time),
                FOREIGN KEY(tour_id) REFERENCES Tours(id),
                FOREIGN KEY(guide_id) REFERENCES Users(id)
            )
            """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS TourImages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tour_id INTEGER NOT NULL,
                image TEXT NOT NULL,
                image_order INTEGER NOT NULL,
                FOREIGN KEY(tour_id) REFERENCES Tours(id)
            )
            """)
        normalize_stored_departure_times(conn)


def ensure_booking_schema():
    ensure_tour_schema()
    with db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tour_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                people_count INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(tour_id) REFERENCES Tours(id),
                FOREIGN KEY(user_id) REFERENCES Users(id)
            )
            """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ReservationParticipants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY(reservation_id) REFERENCES Reservations(id)
            )
            """)


def format_departure_time(raw_time):
    clean_time = (raw_time or "").strip()
    for pattern in ("%H:%M", "%I:%M %p"):
        try:
            parsed = datetime.strptime(clean_time, pattern)
            return parsed.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            continue
    return clean_time


def time_input_value(raw_time):
    clean_time = split_time_language(raw_time)[0]
    for pattern in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(clean_time, pattern).strftime("%H:%M")
        except ValueError:
            continue
    return ""


def is_valid_departure_time(raw_time):
    clean_time = (raw_time or "").strip()
    for pattern in ("%H:%M", "%I:%M %p"):
        try:
            datetime.strptime(clean_time, pattern)
            return True
        except ValueError:
            continue
    return False


def normalize_stored_departure_times(conn):
    # Early versions stored "time - language" in one column. Split those
    # values while retaining compatibility with already-normalized records.
    for table in ("TourDepartures", "TourCompletions", "Reservations"):
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()
        if not exists:
            continue
        rows = conn.execute(f"SELECT id, time FROM {table}").fetchall()
        for row in rows:
            time_label, language = split_time_language(row["time"])
            conn.execute(
                f"UPDATE OR IGNORE {table} SET time = ? WHERE id = ?",
                (time_label, row["id"]),
            )
            if table == "TourDepartures" and language:
                conn.execute(
                    "UPDATE TourDepartures SET language = ? WHERE id = ?",
                    (language, row["id"]),
                )


def departure_start_time(label):
    start_label = label.split(" - ", 1)[0].strip()
    for pattern in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(start_label, pattern).time()
        except ValueError:
            continue
    return time(10, 0)


def departure_datetime(date_value, time_label):
    return datetime.combine(
        datetime.fromisoformat(date_value).date(), departure_start_time(time_label)
    )


def tour_departure_interval(date_value, time_label, duration_minutes=120):
    start = departure_datetime(date_value, time_label)
    return start, start + timedelta(minutes=duration_minutes)


def intervals_overlap(first_start, first_end, second_start, second_end):
    return first_start < second_end and second_start < first_end


def clean_static_path(path):
    if not path:
        return None
    return path.removeprefix("/static/")


def get_tour_languages(conn, tour_id):
    rows = conn.execute(
        """
        SELECT DISTINCT Languages.name
        FROM TourLanguages
        JOIN Languages ON Languages.id = TourLanguages.language_id
        WHERE TourLanguages.tour_id = ?
        ORDER BY Languages.id
        """,
        (tour_id,),
    ).fetchall()
    return [row["name"] for row in rows]


def get_tour_guides(conn, tour_id):
    rows = conn.execute(
        """
        SELECT Users.id, Users.name, Users.surname, Users.email, Users.profile_picture
        FROM TourGuides
        JOIN Users ON Users.id = TourGuides.id_guide
        WHERE TourGuides.id_tour = ?
        ORDER BY Users.id
        """,
        (tour_id,),
    ).fetchall()
    guides = []
    for row in rows:
        review = conn.execute(
            "SELECT AVG(point) AS rating FROM GuideReviews WHERE guide_id = ?",
            (row["id"],),
        ).fetchone()
        rating = review["rating"] if review and review["rating"] is not None else 4.9
        guides.append(
            {
                "id": str(row["id"]),
                "user_id": row["id"],
                "name": row["name"],
                "surname": row["surname"],
                "email": row["email"],
                "rating": f"{rating:.1f}",
                "specialty": "Local Guide",
                "photo": clean_static_path(row["profile_picture"])
                or "images/Untitled-1-removebg-preview.png",
            }
        )
    return guides


def get_tour_stops(conn, tour_id):
    rows = conn.execute(
        """
        SELECT name, description, image
        FROM Stops
        WHERE tour_id = ?
        ORDER BY "order", id
        """,
        (tour_id,),
    ).fetchall()
    stops = [
        {
            "name": row["name"],
            "description": row["description"],
            "image": row["image"] or FALLBACK_IMAGES[index % len(FALLBACK_IMAGES)],
        }
        for index, row in enumerate(rows)
    ]
    defaults = [
        {
            "name": "Galata Tower",
            "description": "The neighborhood's vertical anchor and a perfect place to start.",
            "image": "images/pera-2.svg",
        },
        {
            "name": "Serdar-i Ekrem",
            "description": "A lane of design shops, apartments, and small-city rhythm.",
            "image": "images/pera-3.svg",
        },
        {
            "name": "Karakoy Square",
            "description": "A meeting point between ferries, banks, cafes, and warehouses.",
            "image": "images/sultanahmet-5.svg",
        },
        {
            "name": "Spice Bazaar",
            "description": "A sensory explosion of colors and aromas in the heart of the city.",
            "image": "images/sultanahmet-2.svg",
        },
    ]
    while len(stops) < 4:
        stops.append(defaults[len(stops)].copy())
    return stops


def get_tour_departures(conn, tour_id, languages):
    ensure_tour_schema()
    rows = conn.execute(
        """
        SELECT date, time, language
        FROM TourDepartures
        WHERE tour_id = ?
        ORDER BY date, time
        """,
        (tour_id,),
    ).fetchall()
    departures = []
    for row in rows:
        time_label, legacy_language = split_time_language(row["time"])
        departures.append(
            {
                "date": row["date"],
                "time": time_label,
                "language": canonical_language_name(row["language"] or legacy_language),
            }
        )
    if departures:
        return departures

    today = date.today()
    fallback_languages = languages or ["English"]
    fallback_times = ["10:00 AM", "02:00 PM", "04:30 PM"]
    return [
        {
            "date": (today + timedelta(days=offset)).isoformat(),
            "time": fallback_times[index % len(fallback_times)],
            "language": language,
        }
        for index, (offset, language) in enumerate(
            zip((0, 2, 4, 6), fallback_languages * 4)
        )
    ][:4]


def row_to_tour(conn, row):
    languages = get_tour_languages(conn, row["id"])
    guides = get_tour_guides(conn, row["id"])
    stops = get_tour_stops(conn, row["id"])
    departures = get_tour_departures(conn, row["id"], languages)
    promo_images = get_tour_images(conn, row["id"])
    times = []
    for departure in departures:
        if departure["time"] not in times:
            times.append(departure["time"])
    upcoming_departures = [
        departure
        for departure in departures
        if departure_datetime(departure["date"], departure["time"]) >= datetime.now()
    ]
    next_departure = min(
        upcoming_departures,
        key=lambda departure: departure_datetime(departure["date"], departure["time"]),
        default=None,
    )
    tour = {
        "id": row["id"],
        "name": row["name"],
        "category": row["type"],
        "description": row["description"],
        "meeting_point": row["meeting_point"],
        "max_participants": row["max_participants"],
        "duration_minutes": (
            row["duration_minutes"] if "duration_minutes" in row.keys() else 120
        ),
        "has_reservations": tour_has_reservations(row["id"]),
        "booked_total": booked_total_for_tour(row["id"]),
        "hero_image": promo_images[0],
        "card_image": promo_images[0],
        "gallery_images": promo_images,
        "guides": guides,
        "languages": languages,
        "times": times,
        "next_date_label": (
            datetime.fromisoformat(next_departure["date"]).strftime("%d %b")
            if next_departure
            else "No dates"
        ),
        "departures": departures,
        "reservation_people": reservation_people_for_tour(row["id"]),
        "stops": stops,
    }
    tour["reservation_summary"] = reservation_summary_for_tour(tour)
    return tour


def has_upcoming_departures(tour, now=None):
    now = now or datetime.now()
    return any(
        departure_datetime(departure["date"], departure["time"]) >= now
        for departure in tour.get("departures", [])
    )


def get_dataset_tours():
    ensure_tour_schema()
    with db_connection() as conn:
        rows = conn.execute("SELECT * FROM Tours ORDER BY id").fetchall()
        tours = [row_to_tour(conn, row) for row in rows]
        return [tour for tour in tours if has_upcoming_departures(tour)]


def get_tour_departures_from_rows(departures, languages):
    if departures:
        return departures

    today = date.today()
    fallback_languages = languages or ["English"]
    fallback_times = ["10:00 AM", "02:00 PM", "04:30 PM"]
    return [
        {
            "date": (today + timedelta(days=offset)).isoformat(),
            "time": fallback_times[index % len(fallback_times)],
            "language": language,
        }
        for index, (offset, language) in enumerate(
            zip((0, 2, 4, 6), fallback_languages * 4)
        )
    ][:4]


def get_homepage_tours():
    """Return only the fields needed by the index cards and filters."""
    ensure_booking_schema()
    now = datetime.now()
    with db_connection() as conn:
        tour_rows = conn.execute("SELECT * FROM Tours ORDER BY id").fetchall()
        language_rows = conn.execute(
            """
            SELECT TourLanguages.tour_id, Languages.name
            FROM TourLanguages
            JOIN Languages ON Languages.id = TourLanguages.language_id
            ORDER BY Languages.id
            """
        ).fetchall()
        guide_rows = conn.execute(
            """
            SELECT id_tour, COUNT(*) AS guide_count
            FROM TourGuides
            GROUP BY id_tour
            """
        ).fetchall()
        image_rows = conn.execute(
            """
            SELECT tour_id, image
            FROM TourImages
            ORDER BY tour_id, image_order, id
            """
        ).fetchall()
        departure_rows = conn.execute(
            """
            SELECT tour_id, date, time, language
            FROM TourDepartures
            ORDER BY tour_id, date, time
            """
        ).fetchall()
        booking_rows = conn.execute(
            """
            SELECT tour_id, COALESCE(SUM(people_count), 0) AS booked
            FROM Reservations
            GROUP BY tour_id
            """
        ).fetchall()

    languages_by_tour = defaultdict(list)
    for row in language_rows:
        languages_by_tour[row["tour_id"]].append(row["name"])

    guide_count_by_tour = {row["id_tour"]: row["guide_count"] for row in guide_rows}
    booked_by_tour = {row["tour_id"]: row["booked"] for row in booking_rows}

    images_by_tour = defaultdict(list)
    for row in image_rows:
        if row["image"]:
            images_by_tour[row["tour_id"]].append(row["image"])

    departures_by_tour = defaultdict(list)
    for row in departure_rows:
        time_label, legacy_language = split_time_language(row["time"])
        departures_by_tour[row["tour_id"]].append(
            {
                "date": row["date"],
                "time": time_label,
                "language": canonical_language_name(row["language"] or legacy_language),
            }
        )

    tours = []
    for row in tour_rows:
        tour_id = row["id"]
        languages = languages_by_tour[tour_id]
        departures = get_tour_departures_from_rows(departures_by_tour[tour_id], languages)
        upcoming_departures = [
            departure
            for departure in departures
            if departure_datetime(departure["date"], departure["time"]) >= now
        ]
        if not upcoming_departures:
            continue

        next_departure = min(
            upcoming_departures,
            key=lambda departure: departure_datetime(departure["date"], departure["time"]),
        )
        promo_images = images_by_tour[tour_id] + FALLBACK_IMAGES
        guide_count = guide_count_by_tour.get(tour_id, 0)
        tours.append(
            {
                "id": tour_id,
                "name": row["name"],
                "category": row["type"],
                "description": row["description"],
                "max_participants": row["max_participants"],
                "duration_minutes": row["duration_minutes"] if "duration_minutes" in row.keys() else 120,
                "booked_total": booked_by_tour.get(tour_id, 0),
                "card_image": promo_images[0],
                "languages": languages,
                "guides": [None] * guide_count,
                "next_date_label": datetime.fromisoformat(next_departure["date"]).strftime("%d %b"),
                "departures": departures,
            }
        )
    return tours


def get_dataset_tour(tour_id):
    ensure_tour_schema()
    with db_connection() as conn:
        row = conn.execute("SELECT * FROM Tours WHERE id = ?", (tour_id,)).fetchone()
        if row is None:
            return None
        return row_to_tour(conn, row)


def get_dataset_guide_tours(guide_id):
    ensure_tour_schema()
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT Tours.*
            FROM Tours
            JOIN TourGuides ON TourGuides.id_tour = Tours.id
            WHERE TourGuides.id_guide = ?
            ORDER BY Tours.id
            """,
            (guide_id,),
        ).fetchall()
        return [row_to_tour(conn, row) for row in rows]


def guide_owns_tour(tour, guide_id):
    return any(guide.get("user_id") == guide_id for guide in tour.get("guides", []))


def tour_has_reservations(tour_id):
    ensure_booking_schema()
    with db_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM Reservations WHERE tour_id = ?",
            (tour_id,),
        ).fetchone()
    return row["count"] > 0


def delete_unbooked_tour(tour_id):
    """Delete a tour and its child records only when it has no bookings."""
    ensure_booking_schema()
    with db_connection() as conn:
        if conn.execute(
            "SELECT 1 FROM Reservations WHERE tour_id = ? LIMIT 1", (tour_id,)
        ).fetchone():
            return False

        # Legacy tables do not declare cascading deletes.
        child_keys = {
            "Stops": "tour_id",
            "TourImages": "tour_id",
            "TourDepartures": "tour_id",
            "TourCompletions": "tour_id",
            "TourLanguages": "tour_id",
            "TourGuides": "id_tour",
            "GuideReviews": "tour_id",
        }
        for table, key in child_keys.items():
            conn.execute(f"DELETE FROM {table} WHERE {key} = ?", (tour_id,))
        return conn.execute("DELETE FROM Tours WHERE id = ?", (tour_id,)).rowcount == 1


def booked_total_for_tour(tour_id):
    ensure_booking_schema()
    with db_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(people_count), 0) AS booked FROM Reservations WHERE tour_id = ?",
            (tour_id,),
        ).fetchone()
    return row["booked"] if row else 0


def guide_tours_for(guide_id):
    if str(guide_id).isdigit():
        return [
            tour
            for tour in get_dataset_guide_tours(int(guide_id))
            if has_upcoming_departures(tour)
        ]
    return []


def booked_people_count(tour_id, date_value, time_label):
    ensure_booking_schema()
    with db_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(people_count), 0) AS booked
            FROM Reservations
            WHERE tour_id = ? AND date = ? AND time = ?
            """,
            (tour_id, date_value, time_label),
        ).fetchone()
    return row["booked"] if row else 0


def get_tour_images(conn, tour_id):
    ensure_tour_schema()
    rows = conn.execute(
        """
        SELECT image
        FROM TourImages
        WHERE tour_id = ?
        ORDER BY image_order, id
        """,
        (tour_id,),
    ).fetchall()
    images = [row["image"] for row in rows if row["image"]]
    images.extend(FALLBACK_IMAGES)
    return images[:5]


def reservation_participant_names(conn, reservation_id):
    rows = conn.execute(
        """
        SELECT name
        FROM ReservationParticipants
        WHERE reservation_id = ?
        ORDER BY id
        """,
        (reservation_id,),
    ).fetchall()
    return [row["name"] for row in rows]


def reservation_people_for_tour(tour_id):
    ensure_booking_schema()
    people = []
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT Reservations.id, Reservations.date, Reservations.time,
                   Users.name, Users.surname
            FROM Reservations
            JOIN Users ON Users.id = Reservations.user_id
            WHERE Reservations.tour_id = ?
            ORDER BY Reservations.date, Reservations.time, Reservations.id
            """,
            (tour_id,),
        ).fetchall()

        for row in rows:
            people.append(
                {
                    "name": f"{row['name']} {row['surname']}",
                    "date": row["date"],
                    "time": row["time"],
                }
            )
            for participant_name in reservation_participant_names(conn, row["id"]):
                people.append(
                    {
                        "name": participant_name,
                        "date": row["date"],
                        "time": row["time"],
                    }
                )
    return people


def reservation_summary_for_tour(tour):
    ensure_booking_schema()
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT Reservations.id, Reservations.date, Reservations.time, Reservations.people_count,
                   Users.name, Users.surname, Users.email
            FROM Reservations
            JOIN Users ON Users.id = Reservations.user_id
            WHERE Reservations.tour_id = ?
            ORDER BY Reservations.date, Reservations.time, Users.surname
            """,
            (tour["id"],),
        ).fetchall()

        grouped = {}
        for row in rows:
            # Group reservations by exact departure so guides can see each time slot separately.
            key = (row["date"], row["time"])
            grouped.setdefault(key, {"expected": 0, "reservations": []})
            grouped[key]["expected"] += row["people_count"]
            participant_names = reservation_participant_names(conn, row["id"])
            grouped[key]["reservations"].append(
                {
                    "name": f"{row['name']} {row['surname']}",
                    "email": row["email"],
                    "people_count": row["people_count"],
                    "participants": participant_names,
                }
            )

    summaries = []
    for departure in tour.get("departures", []):
        key = (departure["date"], departure["time"])
        starts_at = departure_datetime(departure["date"], departure["time"])
        data = grouped.get(key, {"expected": 0, "reservations": []})
        attendees = []
        for reservation in data["reservations"]:
            attendees.append(reservation["name"])
            attendees.extend(reservation["participants"])
        summaries.append(
            {
                "date": starts_at.date(),
                "time": departure["time"],
                "language": departure.get("language") or "",
                "expected": data["expected"],
                "reservations": data["reservations"],
                "attendees": attendees,
            }
        )
    return summaries


def remaining_capacity(tour, date_value, time_label):
    return max(
        0,
        int(tour.get("max_participants") or 0)
        - booked_people_count(tour["id"], date_value, time_label),
    )


def user_has_overlap(user_id, date_value, time_label, duration_minutes=120):
    ensure_booking_schema()
    new_start, new_end = tour_departure_interval(
        date_value, time_label, duration_minutes
    )
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT Reservations.date, Reservations.time, Tours.duration_minutes
            FROM Reservations
            JOIN Tours ON Tours.id = Reservations.tour_id
            WHERE Reservations.user_id = ? AND Reservations.date = ?
            """,
            (user_id, date_value),
        ).fetchall()
    for row in rows:
        existing_start, existing_end = tour_departure_interval(
            row["date"], row["time"], row["duration_minutes"]
        )
        if new_start < existing_end and existing_start < new_end:
            return True
    return False


def guide_has_tour_overlap(
    guide_id, departures, duration_minutes=120, excluded_tour_id=None
):
    for new_departure in departures:
        new_start, new_end = tour_departure_interval(
            new_departure["date"], new_departure["time"], duration_minutes
        )
        for tour in get_dataset_guide_tours(guide_id):
            if excluded_tour_id is not None and tour["id"] == excluded_tour_id:
                continue
            for existing_departure in tour.get("departures", []):
                if existing_departure["date"] != new_departure["date"]:
                    continue
                existing_start, existing_end = tour_departure_interval(
                    existing_departure["date"],
                    existing_departure["time"],
                    tour.get("duration_minutes", 120),
                )
                if intervals_overlap(new_start, new_end, existing_start, existing_end):
                    return True
    return False


def departures_have_overlap(departures, duration_minutes=120):
    intervals = []
    for departure in departures:
        start, end = tour_departure_interval(
            departure["date"], departure["time"], duration_minutes
        )
        intervals.append((start, end))

    for index, (start, end) in enumerate(intervals):
        for existing_start, existing_end in intervals[:index]:
            if intervals_overlap(start, end, existing_start, existing_end):
                return True
    return False


def first_available_slot(tour):
    for departure in tour.get("departures", []):
        if departure_datetime(departure["date"], departure["time"]) < datetime.now():
            continue
        if remaining_capacity(tour, departure["date"], departure["time"]) > 0:
            return departure
    return None


def booking_slot_payload(tour):
    return {
        f"{departure['date']}|{departure['time']}": min(
            4, remaining_capacity(tour, departure["date"], departure["time"])
        )
        for departure in tour.get("departures", [])
    }


def profile_tour_sections(user_id):
    ensure_booking_schema()
    now = datetime.now()
    upcoming = []
    previous = []
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, tour_id, date, time, people_count
            FROM Reservations
            WHERE user_id = ?
            ORDER BY date, time
            """,
            (user_id,),
        ).fetchall()

    for row in rows:
        tour = get_dataset_tour(row["tour_id"])
        if tour is None:
            continue
        starts_at = departure_datetime(row["date"], row["time"])
        can_cancel = starts_at - now > timedelta(hours=24)
        item = {
            "reservation_id": row["id"],
            "tour": tour,
            "date": starts_at.date(),
            "time": row["time"],
            "people_count": row["people_count"],
            "participants": reservation_participant_names(conn, row["id"]),
            "can_cancel": can_cancel,
            "reviewed": user_has_reviewed_tour(user_id, row["tour_id"]),
            "status": "Reserved" if starts_at >= now else "Completed",
        }
        if starts_at >= now:
            upcoming.append(item)
        else:
            previous.append(item)
    return upcoming, previous


def user_has_upcoming_booking_for_tour(user_id, tour_id):
    upcoming_tours, _ = profile_tour_sections(user_id)
    return any(item["tour"]["id"] == tour_id for item in upcoming_tours)


def cancel_upcoming_booking(user_id, tour_id):
    ensure_booking_schema()
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, date, time
            FROM Reservations
            WHERE user_id = ? AND tour_id = ?
            ORDER BY date, time
            """,
            (user_id, tour_id),
        ).fetchall()
        now = datetime.now()
        cancellable = next(
            (
                row
                for row in rows
                if departure_datetime(row["date"], row["time"]) - now
                > timedelta(hours=24)
            ),
            None,
        )
        if not cancellable:
            return False
        conn.execute("DELETE FROM Reservations WHERE id = ?", (cancellable["id"],))
        return True


def user_has_completed_booking(user_id, tour_id):
    ensure_booking_schema()
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT date, time
            FROM Reservations
            WHERE user_id = ? AND tour_id = ?
            """,
            (user_id, tour_id),
        ).fetchall()
    return any(
        departure_datetime(row["date"], row["time"]) < datetime.now() for row in rows
    )


def user_has_reviewed_tour(user_id, tour_id):
    with db_connection() as conn:
        return (
            conn.execute(
                "SELECT 1 FROM GuideReviews WHERE user_id = ? AND tour_id = ? LIMIT 1",
                (user_id, tour_id),
            ).fetchone()
            is not None
        )


def add_reservation(
    tour_id, user_id, date_value, time_label, people_count, participant_names=None
):
    participant_names = participant_names or []
    with db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO Reservations (tour_id, user_id, date, time, people_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tour_id, user_id, date_value, time_label, people_count),
        )
        reservation_id = cursor.lastrowid
        for name in participant_names:
            conn.execute(
                "INSERT INTO ReservationParticipants (reservation_id, name) VALUES (?, ?)",
                (reservation_id, name),
            )
        return reservation_id


def guide_profile_sections(guide_id):
    now = datetime.now()
    current_tours = []
    previous_tours = []
    for tour in get_dataset_guide_tours(guide_id):
        summaries = reservation_summary_for_tour(tour)
        upcoming_departures = [
            departure
            for departure in tour.get("departures", [])
            if departure_datetime(departure["date"], departure["time"]) >= now
        ]
        if upcoming_departures:
            next_departure = min(
                upcoming_departures,
                key=lambda departure: departure_datetime(
                    departure["date"], departure["time"]
                ),
            )
            # The profile card stays compact: show only the next two departure summaries.
            upcoming_summaries = [
                summary
                for summary in summaries
                if datetime.combine(summary["date"], time.min)
                >= now.replace(hour=0, minute=0, second=0, microsecond=0)
            ][:2]
            current_tours.append(
                {
                    "tour": tour,
                    "date": datetime.fromisoformat(next_departure["date"]).date(),
                    "time": next_departure["time"],
                    "status": "Guiding",
                    "reservation_summary": upcoming_summaries,
                }
            )
        else:
            last_departure = max(
                tour.get("departures", []),
                key=lambda departure: departure_datetime(
                    departure["date"], departure["time"]
                ),
                default=None,
            )
            previous_summaries = [
                summary
                for summary in summaries
                if datetime.combine(summary["date"], time.min)
                < now.replace(hour=0, minute=0, second=0, microsecond=0)
            ][-2:]
            previous_tours.append(
                {
                    "tour": tour,
                    "date": (
                        datetime.fromisoformat(last_departure["date"]).date()
                        if last_departure
                        else date.today()
                    ),
                    "time": (
                        last_departure["time"] if last_departure else "No departures"
                    ),
                    "status": "Completed",
                    "reservation_summary": previous_summaries,
                }
            )
    return current_tours, previous_tours


def guide_spoken_languages(guide_id):
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT Languages.name
            FROM UserLanguages
            JOIN Languages ON Languages.id = UserLanguages.language_id
            WHERE UserLanguages.user_id = ?
            ORDER BY Languages.id
            """,
            (guide_id,),
        ).fetchall()
    return [row["name"] for row in rows]


def guide_review_sections(guide_id):
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT GuideReviews.point, GuideReviews.text, GuideReviews.date, Users.name, Users.surname, Tours.name AS tour_name
            FROM GuideReviews
            JOIN Users ON Users.id = GuideReviews.user_id
            JOIN Tours ON Tours.id = GuideReviews.tour_id
            WHERE GuideReviews.guide_id = ?
            ORDER BY GuideReviews.date DESC
            """,
            (guide_id,),
        ).fetchall()
    return [
        {
            "point": f"{row['point']:.1f}",
            "text": row["text"],
            "date": row["date"],
            "name": f"{row['name']} {row['surname']}",
            "tour_name": row["tour_name"],
        }
        for row in rows
    ]


def guide_info_for(guide_id):
    if not str(guide_id).isdigit():
        return None
    with db_connection() as conn:
        user = conn.execute(
            "SELECT * FROM Users WHERE id = ? AND type = 'guide'", (guide_id,)
        ).fetchone()
        if user is None:
            return None
        rating = conn.execute(
            "SELECT AVG(point) AS rating FROM GuideReviews WHERE guide_id = ?",
            (guide_id,),
        ).fetchone()
    reviews = guide_review_sections(guide_id)
    return {
        "id": str(user["id"]),
        "name": user["name"],
        "surname": user["surname"],
        "photo": clean_static_path(user["profile_picture"])
        or "images/Untitled-1-removebg-preview.png",
        "languages": guide_spoken_languages(guide_id) or ["English"],
        "review_point": (
            f"{rating['rating']:.1f}"
            if rating and rating["rating"] is not None
            else "4.9"
        ),
        "info": "Local Istanbul guide currently leading routes on Istanwalk.",
        "reviews": reviews
        or [
            {
                "name": "Istanwalk guest",
                "point": "4.9",
                "text": "A clear, friendly guide with strong local knowledge.",
            }
        ],
    }


def save_review_for_tour(tour, user_id, point, review_text):
    if not review_text or user_has_reviewed_tour(user_id, tour["id"]):
        return False
    with db_connection() as conn:
        for guide in tour.get("guides", []):
            conn.execute(
                """
                INSERT INTO GuideReviews (tour_id, user_id, guide_id, point, text)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tour["id"], user_id, guide["user_id"], point, review_text),
            )
    return True


def tour_calendar_days(tour):
    today = date.today()
    departures = tour.get("departures", [])
    if departures:
        by_date = {}
        for departure in departures:
            by_date.setdefault(departure["date"], []).append(departure["time"])
    else:
        by_date = {
            (today + timedelta(days=offset)).isoformat(): tour.get("times", [])
            for offset in (0, 2, 4, 6)
        }
    return [
        {
            "key": (today + timedelta(days=offset)).isoformat(),
            "day": (today + timedelta(days=offset)).strftime("%a"),
            "date": (today + timedelta(days=offset)).strftime("%d"),
            "month": (today + timedelta(days=offset)).strftime("%b").upper(),
            "week": offset // 7,
            "past": (today + timedelta(days=offset)) < today,
            "times": by_date.get((today + timedelta(days=offset)).isoformat(), []),
        }
        for offset in range(63)
    ]


def empty_tour_form():
    default_stop = {"name": "", "description": "", "image": "images/sultanahmet-3.svg"}
    return {
        "id": 0,
        "name": "",
        "category": "",
        "description": "",
        "meeting_point": "",
        "max_participants": 12,
        "duration_minutes": 120,
        "hero_image": "images/sultanahmet-3.svg",
        "card_image": "images/sultanahmet-3.svg",
        "gallery_images": ["images/sultanahmet-3.svg"] * 5,
        "times": [],
        "guides": [],
        "stops": [default_stop.copy() for _ in range(4)],
    }


def collect_editor_departures(form_data):
    departures = []
    for key in sorted(form_data.keys()):
        if not key.startswith("time_"):
            continue
        date_key = key.removeprefix("time_").removesuffix("[]")
        language_values = form_data.getlist(f"language_{date_key}[]")
        for index, time_value in enumerate(form_data.getlist(key)[:1]):
            clean_time, legacy_language = split_time_language(time_value)
            if not clean_time:
                continue
            language = (
                canonical_language_name(language_values[index])
                if index < len(language_values)
                else legacy_language
            )
            departures.append(
                {
                    "date": date_key,
                    "time": format_departure_time(clean_time),
                    "language": language,
                }
            )
    return departures


def collect_editor_languages(form_data):
    languages = []
    for key in sorted(form_data.keys()):
        if not key.startswith("time_"):
            continue
        date_key = key.removeprefix("time_").removesuffix("[]")
        language_values = form_data.getlist(f"language_{date_key}[]")
        for index, time_value in enumerate(form_data.getlist(key)[:1]):
            clean_time, legacy_language = split_time_language(time_value)
            if not clean_time:
                continue
            language = (
                canonical_language_name(language_values[index])
                if index < len(language_values)
                else legacy_language
            )
            if (
                language
                and language in AVAILABLE_LANGUAGES
                and language not in languages
            ):
                languages.append(language)
    return languages


def validate_tour_editor_form(form_data):
    errors = []
    required_fields = {
        "name": "Tour name",
        "category": "Category",
        "meeting_point": "Meeting point",
        "max_participants": "Max participants",
        "duration_minutes": "Duration",
        "description": "Description",
    }
    for field, label in required_fields.items():
        if not str(form_data.get(field, "")).strip():
            errors.append(f"{label} is required.")

    try:
        if int(form_data.get("max_participants") or 0) < 1:
            errors.append("Max participants must be at least 1.")
    except ValueError:
        errors.append("Max participants must be a number.")

    try:
        if int(form_data.get("duration_minutes") or 0) < 1:
            errors.append("Duration must be at least 1 minute.")
    except ValueError:
        errors.append("Duration must be a number.")

    names = [name.strip() for name in form_data.getlist("stop_name[]")]
    descriptions = [
        description.strip() for description in form_data.getlist("stop_description[]")
    ]
    if (
        len(names) < 4
        or any(not name for name in names[:4])
        or len(descriptions) < 4
        or any(not description for description in descriptions[:4])
    ):
        errors.append("Fill every route stop name and description.")

    departures = collect_editor_departures(form_data)
    if not departures:
        errors.append("Add a departure time and language.")
    for departure in departures:
        if not is_valid_departure_time(departure["time"]):
            errors.append("Departure time must be in time format.")
            break
        if departure["language"] not in AVAILABLE_LANGUAGES:
            errors.append("Choose a valid departure language.")
            break

    return errors


def collect_editor_guide_ids(form_data, required_guide_id):
    guide_ids = [int(required_guide_id)]
    emails = form_data.getlist("guide_email[]")
    missing_emails = []
    with db_connection() as conn:
        for email in emails:
            clean_email = email.strip()
            if not clean_email:
                continue
            row = conn.execute(
                "SELECT id FROM Users WHERE type = 'guide' AND lower(email) = lower(?)",
                (clean_email,),
            ).fetchone()
            if row and row["id"] not in guide_ids:
                guide_ids.append(row["id"])
            elif not row:
                missing_emails.append(clean_email)
    return guide_ids, missing_emails


def save_tour_image(uploaded_file, prefix):
    if uploaded_file is None or uploaded_file.filename == "":
        return None
    try:
        image = Image.open(uploaded_file)
        image.verify()
        uploaded_file.stream.seek(0)
        image = Image.open(uploaded_file).convert("RGB")
    except (UnidentifiedImageError, OSError):
        return None

    upload_folder = STATIC_IMAGE_ROOT / "tour_uploads"
    upload_folder.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}-{uuid4().hex}.jpg"
    destination = upload_folder / filename
    image.save(destination, "JPEG", quality=88, optimize=True)
    return f"images/tour_uploads/{filename}"


def pending_tour_completions_for_guide(guide_id):
    ensure_tour_schema()
    now = datetime.now()
    pending = []
    for tour in get_dataset_guide_tours(guide_id):
        for departure in tour.get("departures", []):
            # Reports are per departure, not per tour, so past dates still appear when the tour continues later.
            if (
                departure_datetime(departure["date"], departure["time"])
                + timedelta(minutes=tour.get("duration_minutes", 120))
                > now
            ):
                continue
            if (
                booked_people_count(tour["id"], departure["date"], departure["time"])
                == 0
            ):
                continue
            with db_connection() as conn:
                row = conn.execute(
                    """
                    SELECT id
                    FROM TourCompletions
                    WHERE tour_id = ? AND guide_id = ? AND date = ? AND time = ?
                    """,
                    (tour["id"], guide_id, departure["date"], departure["time"]),
                ).fetchone()
            if row is None:
                pending.append(
                    {
                        "tour": tour,
                        "date": departure["date"],
                        "time": departure["time"],
                        "language": departure.get("language") or "",
                        "expected": booked_people_count(
                            tour["id"], departure["date"], departure["time"]
                        ),
                        "starts_at": departure_datetime(
                            departure["date"], departure["time"]
                        ),
                    }
                )
    return sorted(pending, key=lambda item: item["starts_at"])


def save_tour_completion(
    tour_id, guide_id, date_value, time_label, attendance, proof_file
):
    proof_image = (
        save_tour_image(proof_file, "tour-proof")
        if proof_file and proof_file.filename
        else None
    )
    ensure_tour_schema()
    with db_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO TourCompletions (tour_id, guide_id, date, time, attendance, proof_image)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tour_id, guide_id, date_value, time_label, attendance, proof_image),
        )


def collect_editor_stops(form_data, files, fallback_stops):
    names = form_data.getlist("stop_name[]")
    descriptions = form_data.getlist("stop_description[]")
    images = files.getlist("stop_image[]")
    stops = []
    for index, name in enumerate(names):
        clean_name = name.strip()
        description = descriptions[index].strip() if index < len(descriptions) else ""
        if clean_name or description:
            fallback = (
                fallback_stops[index]
                if index < len(fallback_stops)
                else fallback_stops[-1]
            )
            uploaded_image = images[index] if index < len(images) else None
            stops.append(
                {
                    "name": clean_name,
                    "description": description,
                    "image": save_tour_image(uploaded_image, "stop")
                    or fallback["image"],
                }
            )
    if not stops:
        stops = fallback_stops

    while len(stops) < 4:
        fallback = (
            fallback_stops[len(stops)]
            if len(stops) < len(fallback_stops)
            else fallback_stops[-1]
        )
        stops.append(
            {
                "name": fallback.get("name", ""),
                "description": fallback.get("description", ""),
                "image": fallback.get("image", "images/sultanahmet-3.svg"),
            }
        )
    return stops


def gallery_images_for(tour):
    images = [tour.get("hero_image") or tour.get("card_image") or FALLBACK_IMAGES[0]]
    images.extend(tour.get("gallery_images", []))
    images.extend(FALLBACK_IMAGES)
    return images[:5]


def save_tour_images(tour_id, files, existing_images=None):
    existing_images = existing_images or FALLBACK_IMAGES
    main_image = (
        save_tour_image(files.get("main_image"), "tour-main")
        if files.get("main_image")
        else None
    )
    gallery_uploads = files.getlist("gallery_images[]")
    images = []

    for index in range(5):
        if index == 0:
            images.append(
                main_image or existing_images[0]
                if existing_images
                else FALLBACK_IMAGES[0]
            )
            continue
        upload = (
            gallery_uploads[index - 1] if index - 1 < len(gallery_uploads) else None
        )
        fallback = (
            existing_images[index]
            if index < len(existing_images)
            else FALLBACK_IMAGES[index % len(FALLBACK_IMAGES)]
        )
        images.append(save_tour_image(upload, "tour-gallery") or fallback)

    with db_connection() as conn:
        conn.execute("DELETE FROM TourImages WHERE tour_id = ?", (tour_id,))
        for index, image in enumerate(images):
            conn.execute(
                "INSERT INTO TourImages (tour_id, image, image_order) VALUES (?, ?, ?)",
                (tour_id, image, index),
            )


def tour_categories():
    return [
        "Walking Tour",
        "Food Tour",
        "Night Walk",
        "History",
        "Gastronomic",
        "Alternative",
    ]


def save_tour_departures(tour_id, departures):
    ensure_tour_schema()
    with db_connection() as conn:
        conn.execute("DELETE FROM TourDepartures WHERE tour_id = ?", (tour_id,))
        for departure in departures:
            time_label, legacy_language = split_time_language(departure["time"])
            language = canonical_language_name(
                departure.get("language") or legacy_language
            )
            conn.execute(
                "INSERT INTO TourDepartures (tour_id, date, time, language) VALUES (?, ?, ?, ?)",
                (
                    tour_id,
                    departure["date"],
                    format_departure_time(time_label),
                    language,
                ),
            )


def save_tour_stops(tour_id, stops):
    with db_connection() as conn:
        conn.execute("DELETE FROM Stops WHERE tour_id = ?", (tour_id,))
        for index, stop in enumerate(stops, start=1):
            conn.execute(
                'INSERT INTO Stops (name, description, image, "order", tour_id) VALUES (?, ?, ?, ?, ?)',
                (stop["name"], stop["description"], stop["image"], index, tour_id),
            )


def update_tour_record(tour_id, form_data, files, existing_tour, current_guide_id):
    stops = collect_editor_stops(form_data, files, existing_tour["stops"])
    languages = collect_editor_languages(form_data)
    departures = collect_editor_departures(form_data)
    with db_connection() as conn:
        conn.execute(
            """
            UPDATE Tours
            SET name = ?, description = ?, max_participants = ?, meeting_point = ?, type = ?, duration_minutes = ?
            WHERE id = ?
            """,
            (
                form_data.get("name", "").strip(),
                form_data.get("description", "").strip(),
                int(
                    form_data.get("max_participants")
                    or existing_tour["max_participants"]
                    or 12
                ),
                form_data.get("meeting_point", "").strip(),
                form_data.get("category", "").strip(),
                int(
                    form_data.get("duration_minutes")
                    or existing_tour.get("duration_minutes")
                    or 120
                ),
                tour_id,
            ),
        )
        conn.execute("DELETE FROM TourLanguages WHERE tour_id = ?", (tour_id,))
        for language in languages:
            language_id = language_id_for(language)
            if language_id:
                conn.execute(
                    "INSERT OR IGNORE INTO TourLanguages (tour_id, language_id) VALUES (?, ?)",
                    (tour_id, language_id),
                )
        conn.execute("DELETE FROM TourGuides WHERE id_tour = ?", (tour_id,))
        guide_ids, _ = collect_editor_guide_ids(form_data, current_guide_id)
        for guide_id in guide_ids:
            conn.execute(
                "INSERT INTO TourGuides (id_guide, id_tour) VALUES (?, ?)",
                (guide_id, tour_id),
            )
    save_tour_departures(tour_id, departures)
    save_tour_stops(tour_id, stops)
    save_tour_images(tour_id, files, gallery_images_for(existing_tour))
