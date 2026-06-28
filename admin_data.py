import sqlite3

from db_tour import DB_NAME, ensure_booking_schema
from db_user import ensureUserProfileColumns


def admin_dashboard_data():
    """Return the operational records shown on the admin dashboard."""
    # Older databases may not have every table yet, so run the lightweight
    # schema guards before issuing dashboard joins.
    ensureUserProfileColumns()
    ensure_booking_schema()
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    members = conn.execute("""
        SELECT id, name, surname, email, location
        FROM Users
        WHERE type = 'member'
        ORDER BY name, surname
        """).fetchall()
    guides = conn.execute("""
        -- Correlated totals avoid multiplying rows when a guide has both
        -- several assigned tours and several completion reports.
        SELECT Users.id, Users.name, Users.surname, Users.email,
               (SELECT COUNT(DISTINCT id_tour) FROM TourGuides WHERE id_guide = Users.id) AS tour_count,
               (SELECT COUNT(*) FROM TourCompletions WHERE guide_id = Users.id) AS report_count,
               (SELECT COALESCE(SUM(attendance), 0) FROM TourCompletions WHERE guide_id = Users.id) AS total_attendance
        FROM Users
        WHERE Users.type = 'guide'
        ORDER BY Users.name, Users.surname
        """).fetchall()
    tours = conn.execute("""
        -- Keep booking and guide totals independent for the same reason.
        SELECT Tours.id, Tours.name, Tours.type, Tours.meeting_point, Tours.max_participants,
               (SELECT COUNT(DISTINCT id_guide) FROM TourGuides WHERE id_tour = Tours.id) AS guide_count,
               (SELECT COUNT(*) FROM Reservations WHERE tour_id = Tours.id) AS booking_count,
               (SELECT COALESCE(SUM(people_count), 0) FROM Reservations WHERE tour_id = Tours.id) AS people_booked
        FROM Tours
        ORDER BY Tours.id DESC
        """).fetchall()
    reports = conn.execute("""
        SELECT TourCompletions.id, TourCompletions.date, TourCompletions.time,
               TourCompletions.attendance, TourCompletions.proof_image,
               TourCompletions.created_at, Tours.id AS tour_id, Tours.name AS tour_name,
               Users.name || ' ' || Users.surname AS guide_name, Users.email AS guide_email
        FROM TourCompletions
        JOIN Tours ON Tours.id = TourCompletions.tour_id
        JOIN Users ON Users.id = TourCompletions.guide_id
        ORDER BY TourCompletions.created_at DESC, TourCompletions.id DESC
        """).fetchall()
    reservations_by_language = conn.execute("""
        SELECT COALESCE(TourDepartures.language, Languages.name, 'Not set') AS language,
               COUNT(Reservations.id) AS reservation_count,
               COALESCE(SUM(Reservations.people_count), 0) AS people_count
        FROM Reservations
        JOIN Tours ON Tours.id = Reservations.tour_id
        LEFT JOIN TourDepartures
               ON TourDepartures.tour_id = Reservations.tour_id
              AND TourDepartures.date = Reservations.date
              AND TourDepartures.time = Reservations.time
        LEFT JOIN TourLanguages ON TourLanguages.tour_id = Tours.id
        LEFT JOIN Languages ON Languages.id = TourLanguages.language_id
        GROUP BY language
        ORDER BY reservation_count DESC, language
        """).fetchall()
    reservation_count = conn.execute(
        "SELECT COUNT(*) AS count FROM Reservations"
    ).fetchone()["count"]
    conn.close()

    return {
        "members": members,
        "guides": guides,
        "tours": tours,
        "reports": reports,
        "reservations_by_language": reservations_by_language,
        "stats": {
            "tours": len(tours),
            "guides": len(guides),
            "users": len(members),
            "reservations": reservation_count,
            "reports": len(reports),
        },
    }
