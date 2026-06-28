import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "istanbul.db"

LANGUAGE_IDS = {
    "English": 1,
    "Italian": 2,
    "Spanish": 3,
    "Portugese": 4,
    "German": 5,
}


def day(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


TOURS = [
    {
        "name": "Old City Dawn Gazette Walk",
        "description": "A first-light route through Sultanahmet, quiet courtyards, old street corners, and the stories behind Istanbul's imperial heart.",
        "max_participants": 14,
        "meeting_point": "Sultanahmet tram stop, beside the fountain",
        "type": "Walking Tour",
        "duration": 95,
        "guides": [9, 16],
        "languages": ["English", "Italian", "Spanish"],
        "images": [
            "images/siyah-beyaz.jpeg",
            "images/Suleymaniye.jpeg",
            "images/haydarpasa.jpg",
            "images/galata.jpeg",
            "images/Ortakoy.jpeg",
        ],
        "departures": [
            (-2, "8:10 AM", "English"),
            (1, "9:00 AM", "English"),
            (3, "9:30 AM", "Italian"),
            (6, "10:00 AM", "Spanish"),
        ],
        "stops": [
            (
                "Sultanahmet Square",
                "Start among the stones, monuments, and morning vendors of the old city.",
                "images/siyah-beyaz.jpeg",
            ),
            (
                "Hagia Sophia Corner",
                "Read the skyline from a quieter angle and unpack the layers around the square.",
                "images/Suleymaniye.jpeg",
            ),
            (
                "Cistern Streets",
                "Follow narrow streets toward hidden traces of water, trade, and daily life.",
                "images/karakalem.jpg",
            ),
            (
                "Grand Bazaar Gate",
                "Finish at the edge of the bazaar with route tips for independent exploring.",
                "images/taksim.jpeg",
            ),
        ],
        "reservations": [
            (21, -2, "8:10 AM", 2, ["Nina Lane"]),
            (1, 1, "9:00 AM", 1, []),
            (2, 3, "9:30 AM", 3, ["Marco Rossi", "Lena Weiss"]),
        ],
        "reviews": [
            (
                1,
                9,
                5,
                "Utku made the old city feel alive without rushing us through the obvious stops.",
            ),
            (
                2,
                16,
                5,
                "Selin was warm, precise, and brilliant with the small details.",
            ),
        ],
    },
    {
        "name": "Galata Lanes and Ferry Light",
        "description": "A compact hill-and-harbor walk from Galata's back streets to ferry views, music corners, and working waterfront details.",
        "max_participants": 10,
        "meeting_point": "Galata Tower ticket office",
        "type": "Walking Tour",
        "duration": 135,
        "guides": [11],
        "languages": ["English", "German", "Italian"],
        "images": [
            "images/galata.jpeg",
            "images/galata1.jpeg",
            "images/pera-2.svg",
            "images/pera-3.svg",
            "images/haydarpasa.jpg",
        ],
        "departures": [
            (2, "1:00 PM", "German"),
            (5, "4:00 PM", "English"),
            (8, "11:00 AM", "Italian"),
        ],
        "stops": [
            (
                "Galata Tower",
                "Use the tower as a compass for trade routes, slopes, and old neighborhood borders.",
                "images/galata.jpeg",
            ),
            (
                "Serdar-i Ekrem Street",
                "Walk the side streets where apartment facades, shops, and studios overlap.",
                "images/galata1.jpeg",
            ),
            (
                "Karakoy Steps",
                "Descend toward the harbor and look at how the city changes block by block.",
                "images/haydarpasa.jpg",
            ),
            (
                "Ferry Edge",
                "Close with practical ferry tips and a view back toward the historic peninsula.",
                "images/Ortakoy.jpeg",
            ),
        ],
        "reservations": [
            (4, 2, "1:00 PM", 2, ["Sara Klein"]),
        ],
        "reviews": [
            (
                4,
                11,
                4,
                "Great route and a perfect balance of history, architecture, and everyday Istanbul.",
            ),
        ],
    },
    {
        "name": "Kadikoy Market Bites",
        "description": "A food-focused route through Kadikoy market counters, pickle shops, coffee stops, ferry habits, and neighborhood rhythms.",
        "max_participants": 16,
        "meeting_point": "Kadikoy ferry terminal clock",
        "type": "Food Tour",
        "duration": 210,
        "guides": [17, 18],
        "languages": ["English", "Portugese", "German", "Italian"],
        "images": [
            "images/tour_uploads/tour-main-48402ee7d5084fd8be9a8a3d0aa2dcd2.jpg",
            "images/tour_uploads/tour-gallery-10df2810202146a28aa0650664da364a.jpg",
            "images/tour_uploads/tour-gallery-de9da68b956b4912b166086a7b9ecdf5.jpg",
            "images/tour_uploads/stop-d2c6ab5143fc4906a23c08de8ce14485.jpg",
            "images/tour_uploads/stop-7381a6c2f53549b78346deff831c1ade.jpg",
        ],
        "departures": [
            (1, "12:00 PM", "English"),
            (4, "12:30 PM", "Portugese"),
            (7, "2:00 PM", "German"),
        ],
        "stops": [
            (
                "Ferry Arrival",
                "Begin with the ferry crowd and the first smell of the market streets.",
                "images/haydarpasa.jpg",
            ),
            (
                "Pickle Counter",
                "Taste sharp, salty, bright snacks and learn how locals build a quick market lunch.",
                "images/tour_uploads/stop-d2c6ab5143fc4906a23c08de8ce14485.jpg",
            ),
            (
                "Bakery Window",
                "Compare breads, pastries, and neighborhood breakfast rituals.",
                "images/tour_uploads/stop-7381a6c2f53549b78346deff831c1ade.jpg",
            ),
            (
                "Coffee Corner",
                "End with Turkish coffee, route notes, and places to return after the walk.",
                "images/tour_uploads/tour-gallery-de9da68b956b4912b166086a7b9ecdf5.jpg",
            ),
        ],
        "reservations": [
            (13, 1, "12:00 PM", 4, ["Nora Hill", "Theo Hill", "Iris Hill"]),
            (14, 4, "12:30 PM", 1, []),
        ],
        "reviews": [
            (
                13,
                17,
                5,
                "Bora knew every counter and made the whole market feel welcoming.",
            ),
            (14, 18, 5, "Lina's food stories were the highlight of our Istanbul week."),
        ],
    },
    {
        "name": "Pera After Dark",
        "description": "An evening walk through Pera passages, music streets, late bakeries, embassy-era architecture, and night-time city lore.",
        "max_participants": 12,
        "meeting_point": "Tunnel funicular exit",
        "type": "Night Walk",
        "duration": 180,
        "guides": [19],
        "languages": ["English", "Spanish", "German"],
        "images": [
            "images/taksim.jpeg",
            "images/pera-3.svg",
            "images/pera-2.svg",
            "images/galata1.jpeg",
            "images/karakalem.jpg",
        ],
        "departures": [
            (2, "7:00 PM", "Spanish"),
            (5, "8:00 PM", "English"),
            (9, "7:30 PM", "German"),
        ],
        "stops": [
            (
                "Tunnel Square",
                "Set the scene at one of the city's classic evening crossroads.",
                "images/pera-2.svg",
            ),
            (
                "Passage Lights",
                "Move through old arcades, theaters, and shopfronts after daytime crowds fade.",
                "images/pera-3.svg",
            ),
            (
                "Istiklal Backstreet",
                "Step away from the avenue into quieter streets with sharper stories.",
                "images/taksim.jpeg",
            ),
            (
                "Late Bakery",
                "Finish with warm bread smells, night transport tips, and neighborhood context.",
                "images/karakalem.jpg",
            ),
        ],
        "reservations": [
            (15, 2, "7:00 PM", 2, ["Maya Reed"]),
            (21, 5, "8:00 PM", 1, []),
        ],
        "reviews": [
            (
                15,
                19,
                4,
                "Derya gave us a night walk that felt atmospheric but still very grounded.",
            ),
        ],
    },
    {
        "name": "Bosphorus Villages Slow Route",
        "description": "A longer scenic walk linking waterfront villages, mosque courtyards, ferry landings, tea stops, and Bosphorus viewpoints.",
        "max_participants": 18,
        "meeting_point": "Ortakoy Mosque courtyard entrance",
        "type": "Walking Tour",
        "duration": 360,
        "guides": [18, 20],
        "languages": ["English", "Italian", "Portugese"],
        "images": [
            "images/Ortakoy.jpeg",
            "images/Suleymaniye.jpeg",
            "images/haydarpasa.jpg",
            "images/galata.jpeg",
            "images/sultanahmet-5.svg",
        ],
        "departures": [
            (3, "10:30 AM", "English"),
            (6, "11:00 AM", "Italian"),
            (10, "10:00 AM", "Portugese"),
        ],
        "stops": [
            (
                "Ortakoy Square",
                "Start at the water with mosque, bridge, and neighborhood orientation.",
                "images/Ortakoy.jpeg",
            ),
            (
                "Kurucesme Edge",
                "Walk north along changing waterfront textures and old leisure spaces.",
                "images/haydarpasa.jpg",
            ),
            (
                "Arnavutkoy Houses",
                "Read the wooden houses, side streets, and Bosphorus village patterns.",
                "images/galata.jpeg",
            ),
            (
                "Tea Viewpoint",
                "End slowly with tea, ferry advice, and a wide water view.",
                "images/Suleymaniye.jpeg",
            ),
        ],
        "reservations": [
            (22, 3, "10:30 AM", 3, ["Ari Lane", "Cem Lane"]),
            (2, 6, "11:00 AM", 1, []),
        ],
        "reviews": [
            (
                22,
                20,
                5,
                "A generous long route with views, pauses, and real neighborhood texture.",
            ),
        ],
    },
    {
        "name": "Suleymaniye Rooftop Notebook",
        "description": "A mid-length walk through mosque terraces, university streets, hidden courtyards, and rooftop views over the Golden Horn.",
        "max_participants": 9,
        "meeting_point": "Vezneciler metro station exit 2",
        "type": "Walking Tour",
        "duration": 75,
        "guides": [20],
        "languages": ["English", "Italian"],
        "images": [
            "images/Suleymaniye.jpeg",
            "images/sultanahmet-2.svg",
            "images/sultanahmet-3.svg",
            "images/karakalem.jpg",
            "images/siyah-beyaz.jpeg",
        ],
        "departures": [
            (1, "3:00 PM", "Italian"),
            (4, "10:00 AM", "English"),
            (8, "3:30 PM", "English"),
        ],
        "stops": [
            (
                "Vezneciler",
                "Begin with a short orientation to the university quarter and hill route.",
                "images/siyah-beyaz.jpeg",
            ),
            (
                "Suleymaniye Courtyard",
                "Pause for the mosque complex, skyline, and Sinan's city logic.",
                "images/Suleymaniye.jpeg",
            ),
            (
                "Book Streets",
                "Walk through small shops and study corners around the old hill.",
                "images/karakalem.jpg",
            ),
            (
                "Golden Horn View",
                "Finish with a viewpoint and practical routes down the slope.",
                "images/sultanahmet-3.svg",
            ),
        ],
        "reservations": [
            (1, 4, "10:00 AM", 1, []),
        ],
        "reviews": [
            (
                1,
                20,
                5,
                "Short, clear, beautiful, and full of excellent city-reading tips.",
            ),
        ],
    },
    {
        "name": "Princes' Islands Full-Day Sketch",
        "description": "A full-day island route with ferry timing, quiet roads, old houses, pine paths, swimming coves, and slow lunch suggestions.",
        "max_participants": 20,
        "meeting_point": "Kabatas ferry pier ticket machines",
        "type": "Walking Tour",
        "duration": 540,
        "guides": [9, 11, 19],
        "languages": ["English", "Italian", "Spanish", "German"],
        "images": [
            "images/tour_uploads/tour-main-8d0933f3f8ec41a69c11c0418b639a3d.jpg",
            "images/tour_uploads/tour-main-0da1ca4ff1ba4d6b82a5985ccbce469f.jpg",
            "images/tour_uploads/tour-gallery-6b621df901324d02a7d5ed407b9c406b.jpg",
            "images/tour_uploads/stop-c886d128b5ec4cff9c77b2eef4f05391.jpg",
            "images/tour_uploads/stop-cd0e7e2ef6524afc824ad4ebd54bde57.jpg",
        ],
        "departures": [
            (7, "8:30 AM", "English"),
            (12, "8:30 AM", "German"),
            (15, "9:00 AM", "Spanish"),
        ],
        "stops": [
            (
                "Kabatas Pier",
                "Start with ferry logistics, island context, and the best side of the boat.",
                "images/haydarpasa.jpg",
            ),
            (
                "Island Landing",
                "Arrive into a slower pace and map the route before the crowds spread out.",
                "images/tour_uploads/tour-main-8d0933f3f8ec41a69c11c0418b639a3d.jpg",
            ),
            (
                "Pine Road",
                "Walk shaded roads and talk through island architecture and car-free rhythms.",
                "images/tour_uploads/stop-c886d128b5ec4cff9c77b2eef4f05391.jpg",
            ),
            (
                "Sea View Lunch",
                "Close with a long view, lunch suggestions, and return ferry planning.",
                "images/tour_uploads/stop-cd0e7e2ef6524afc824ad4ebd54bde57.jpg",
            ),
        ],
        "reservations": [
            (4, 7, "8:30 AM", 4, ["Rana Youssefi", "Can Youssefi", "Eli Youssefi"]),
            (13, 12, "8:30 AM", 2, ["June Carter"]),
        ],
        "reviews": [
            (4, 9, 5, "The full-day pace made the islands easy and memorable."),
            (13, 11, 4, "Excellent ferry planning and a beautiful route."),
            (15, 19, 5, "Derya's island stories were thoughtful and vivid."),
        ],
    },
    {
        "name": "Fener Balat Memory Walk",
        "description": "A completed archive walk through painted houses, church lanes, old schools, and Golden Horn viewpoints for testing guide history.",
        "max_participants": 12,
        "meeting_point": "Fener ferry landing",
        "type": "Walking Tour",
        "duration": 120,
        "guides": [9],
        "languages": ["English", "Italian"],
        "images": [
            "images/karakalem.jpg",
            "images/siyah-beyaz.jpeg",
            "images/galata1.jpeg",
            "images/Suleymaniye.jpeg",
            "images/taksim.jpeg",
        ],
        "departures": [
            (-8, "8:10 AM", "English"),
            (-5, "10:30 AM", "Italian"),
        ],
        "stops": [
            (
                "Fener Landing",
                "Start beside the Golden Horn with ferry context and neighborhood orientation.",
                "images/galata1.jpeg",
            ),
            (
                "Color Streets",
                "Walk the photographed lanes while separating real history from postcard shorthand.",
                "images/karakalem.jpg",
            ),
            (
                "Old School Wall",
                "Pause near old institutional buildings and talk about communities that shaped the hill.",
                "images/siyah-beyaz.jpeg",
            ),
            (
                "Balat Slope",
                "Finish with a view back toward the water and practical transit notes.",
                "images/Suleymaniye.jpeg",
            ),
        ],
        "reservations": [
            (4, -8, "8:10 AM", 2, ["Rana Youssefi"]),
            (2, -5, "10:30 AM", 3, ["Ece Akbulut", "Nils Hartmann"]),
        ],
        "reviews": [
            (
                4,
                9,
                5,
                "Utku's completed Balat route is exactly what I wanted to remember from the trip.",
            ),
        ],
    },
    {
        "name": "Golden Horn Archive Notes",
        "description": "A past-only Utku route along the Golden Horn, useful for checking multiple completed reports from the same tour.",
        "max_participants": 12,
        "meeting_point": "Eminonu bus stop by the waterfront",
        "type": "Walking Tour",
        "duration": 110,
        "guides": [9],
        "languages": ["English", "Italian"],
        "images": [
            "images/Suleymaniye.jpeg",
            "images/galata.jpeg",
            "images/siyah-beyaz.jpeg",
            "images/haydarpasa.jpg",
            "images/karakalem.jpg",
        ],
        "departures": [
            (-18, "9:15 AM", "English"),
            (-14, "2:45 PM", "Italian"),
        ],
        "stops": [
            (
                "Eminonu Edge",
                "Open with ferry noise, bridge views, and Golden Horn orientation.",
                "images/galata.jpeg",
            ),
            (
                "Market Cut",
                "Move through working streets and small trade stories near the water.",
                "images/siyah-beyaz.jpeg",
            ),
            (
                "Hill Turn",
                "Climb toward mosque views and changing neighborhood textures.",
                "images/Suleymaniye.jpeg",
            ),
            (
                "Waterfront Return",
                "Close by the shore with practical route notes for guests.",
                "images/haydarpasa.jpg",
            ),
        ],
        "reservations": [
            (1, -18, "9:15 AM", 4, ["Ada Yildiz", "Can Yildiz", "Nora Smith"]),
            (13, -14, "2:45 PM", 2, ["June Carter"]),
        ],
        "reviews": [
            (1, 9, 5, "A compact past route with strong views and clear storytelling."),
            (13, 9, 4, "Loved the slower Golden Horn rhythm and Utku's local notes."),
        ],
    },
    {
        "name": "Karakoy Morning Ledger",
        "description": "A completed Utku test walk through harbor streets, bakeries, stairways, and early city movement.",
        "max_participants": 10,
        "meeting_point": "Karakoy ferry terminal",
        "type": "Food Tour",
        "duration": 80,
        "guides": [9],
        "languages": ["English"],
        "images": [
            "images/galata1.jpeg",
            "images/galata.jpeg",
            "images/tour_uploads/tour-gallery-10df2810202146a28aa0650664da364a.jpg",
            "images/tour_uploads/stop-d2c6ab5143fc4906a23c08de8ce14485.jpg",
            "images/haydarpasa.jpg",
        ],
        "departures": [
            (-11, "8:40 AM", "English"),
        ],
        "stops": [
            (
                "Ferry Doors",
                "Begin where commuters and visitors spill into Karakoy.",
                "images/haydarpasa.jpg",
            ),
            (
                "Bakery Stop",
                "Talk breakfast habits and small counter culture.",
                "images/tour_uploads/stop-d2c6ab5143fc4906a23c08de8ce14485.jpg",
            ),
            (
                "Galata Steps",
                "Climb into side streets and compare morning rhythms.",
                "images/galata.jpeg",
            ),
            (
                "Harbor Corner",
                "Finish with coffee suggestions and tram/ferry options.",
                "images/galata1.jpeg",
            ),
        ],
        "reservations": [
            (14, -11, "8:40 AM", 1, []),
        ],
        "reviews": [
            (14, 9, 5, "Short, tasty, and perfectly timed for the morning."),
        ],
    },
    {
        "name": "Besiktas Matchday Memory",
        "description": "A completed Utku night walk around Besiktas streets, ferry corners, food windows, and matchday neighborhood energy.",
        "max_participants": 14,
        "meeting_point": "Besiktas ferry pier",
        "type": "Night Walk",
        "duration": 150,
        "guides": [9],
        "languages": ["English", "Spanish"],
        "images": [
            "images/Ortakoy.jpeg",
            "images/taksim.jpeg",
            "images/galata1.jpeg",
            "images/karakalem.jpg",
            "images/Suleymaniye.jpeg",
        ],
        "departures": [
            (-9, "7:20 PM", "Spanish"),
        ],
        "stops": [
            (
                "Pier Crowd",
                "Start with evening ferry flow and the neighborhood's first pulse.",
                "images/Ortakoy.jpeg",
            ),
            (
                "Food Street",
                "Pass quick bites and local pre-match habits.",
                "images/taksim.jpeg",
            ),
            (
                "Side Lanes",
                "Step away from noise into smaller streets and stories.",
                "images/karakalem.jpg",
            ),
            (
                "Water View",
                "Close with transport tips and a calmer Bosphorus view.",
                "images/galata1.jpeg",
            ),
        ],
        "reservations": [
            (15, -9, "7:20 PM", 3, ["Maya Reed", "Otto Reed"]),
        ],
        "reviews": [
            (15, 9, 4, "A fun evening route with just enough football atmosphere."),
        ],
    },
    {
        "name": "Uskudar Courtyard File",
        "description": "A completed Utku archive route through Uskudar courtyards, waterfront habits, and quiet mosque-side streets.",
        "max_participants": 11,
        "meeting_point": "Uskudar Marmaray exit",
        "type": "Walking Tour",
        "duration": 100,
        "guides": [9],
        "languages": ["English", "German"],
        "images": [
            "images/haydarpasa.jpg",
            "images/Suleymaniye.jpeg",
            "images/Ortakoy.jpeg",
            "images/siyah-beyaz.jpeg",
            "images/galata.jpeg",
        ],
        "departures": [
            (-6, "11:10 AM", "German"),
        ],
        "stops": [
            (
                "Marmaray Exit",
                "Orient guests between rail, ferry, and old waterfront routes.",
                "images/haydarpasa.jpg",
            ),
            (
                "Courtyard Pause",
                "Look at quiet mosque courtyards and daily rituals.",
                "images/Suleymaniye.jpeg",
            ),
            (
                "Market Bend",
                "Move through practical shopping streets and tea corners.",
                "images/siyah-beyaz.jpeg",
            ),
            (
                "Waterfront Finish",
                "End with ferry choices and a view across the city.",
                "images/Ortakoy.jpeg",
            ),
        ],
        "reservations": [
            (22, -6, "11:10 AM", 4, ["Ari Lane", "Cem Lane", "Nina Lane"]),
        ],
        "reviews": [
            (
                22,
                9,
                5,
                "Utku made Uskudar feel quiet, useful, and full of small details.",
            ),
        ],
    },
]


def clear_tour_data(conn):
    tables = [
        "ReservationParticipants",
        "Reservations",
        "TourCompletions",
        "GuideReviews",
        "TourImages",
        "TourDepartures",
        "Stops",
        "TourLanguages",
        "TourGuides",
        "Tours",
    ]
    for table in tables:
        conn.execute(f"DELETE FROM {table}")
    for table in tables:
        conn.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))


def insert_tour(conn, tour):
    cursor = conn.execute(
        """
        INSERT INTO Tours (name, description, max_participants, meeting_point, type, duration_minutes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            tour["name"],
            tour["description"],
            tour["max_participants"],
            tour["meeting_point"],
            tour["type"],
            tour["duration"],
        ),
    )
    tour_id = cursor.lastrowid

    for guide_id in tour["guides"]:
        conn.execute(
            "INSERT INTO TourGuides (id_guide, id_tour) VALUES (?, ?)",
            (guide_id, tour_id),
        )

    for language in tour["languages"]:
        conn.execute(
            "INSERT OR IGNORE INTO TourLanguages (tour_id, language_id) VALUES (?, ?)",
            (tour_id, LANGUAGE_IDS[language]),
        )

    for order, image in enumerate(tour["images"], start=1):
        conn.execute(
            "INSERT INTO TourImages (tour_id, image, image_order) VALUES (?, ?, ?)",
            (tour_id, image, order),
        )

    for order, (name, description, image) in enumerate(tour["stops"], start=1):
        conn.execute(
            'INSERT INTO Stops (name, description, image, "order", tour_id) VALUES (?, ?, ?, ?, ?)',
            (name, description, image, order, tour_id),
        )

    for offset, time_label, language in tour["departures"]:
        conn.execute(
            "INSERT INTO TourDepartures (tour_id, date, time, language) VALUES (?, ?, ?, ?)",
            (tour_id, day(offset), time_label, language),
        )

    for user_id, offset, time_label, people_count, participant_names in tour[
        "reservations"
    ]:
        cursor = conn.execute(
            """
            INSERT INTO Reservations (tour_id, user_id, date, time, people_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tour_id, user_id, day(offset), time_label, people_count),
        )
        reservation_id = cursor.lastrowid
        for participant_name in participant_names:
            conn.execute(
                "INSERT INTO ReservationParticipants (reservation_id, name) VALUES (?, ?)",
                (reservation_id, participant_name),
            )

    for user_id, guide_id, point, text in tour["reviews"]:
        conn.execute(
            """
            INSERT INTO GuideReviews (tour_id, user_id, guide_id, point, text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tour_id, user_id, guide_id, point, text),
        )


def main():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        clear_tour_data(conn)
        for tour in TOURS:
            insert_tour(conn, tour)
        conn.execute("PRAGMA foreign_keys = ON")

    print(f"Seeded {len(TOURS)} tours without changing users.")


if __name__ == "__main__":
    main()
