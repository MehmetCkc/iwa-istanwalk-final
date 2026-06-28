# ISTANWALK

ISTANWALK is a Flask and SQLite web application for managing Free Walking Tours in Istanbul. The platform supports guide accounts, participant accounts, public tour browsing, reservations, guide reporting after completed tours, and an optional administrator dashboard.

## Requirements covered

- HTML5, CSS3, Flask, SQLite, and Flask-Login are used in one integrated application.
- Users register either as guides or participants. A guide cannot book tours, and a participant cannot create or manage tours.
- Guide registration collects first name, last name, unique email, password, and spoken languages from the required language list: English, Italian, Spanish, Portuguese, and German.
- Participant registration collects first name, last name, unique email, and password.
- Public users can browse all available tours and open full tour detail pages.
- Homepage filters support date, duration, and language.
- Guides can create tours with title, meeting point, duration, language, maximum participants, at least four stops, description, schedule entries, and five promotional images.
- While creating or editing an unreserved tour, guides can turn on the "Repeat weekly 1 month" switch to copy the selected date, time, and language to the same weekday for the next four weeks.
- Tour languages are restricted to languages spoken by the guide.
- Guides can edit or delete their own tours only while the tour has no reservations.
- Participants can reserve a specific tour date/time for 1 to 4 people, including up to 3 additional named participants.
- The system blocks bookings that exceed the remaining seats for the selected tour date/time.
- The system blocks overlapping participant reservations.
- Participants can cancel only when the selected tour starts more than 24 hours later.
- Participant profiles show reserved tours with date, time, meeting point, number of people, and additional participant names.
- Guide profiles show created tours, reservation lists, and expected participants per scheduled date.
- Guides can report completed booked tour dates by entering actual attendance and uploading a proof photo.
- The database includes sample guides, participants, tours, reservations, images, and reports for testing.
- The optional administrator account can view users, guides, tours, reports, totals, and reservations by language.

Note: tour availability is stored as concrete departure dates so participants can reserve an exact date/time. The guide editor supports weekly recurrence by generating the same weekday and time for one month.

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

## Testing checklist

1. Browse the homepage while logged out and open a tour detail page.
2. Use homepage filters for date, duration, and language.
3. Register a new participant and confirm duplicate emails are rejected.
4. Log in as a participant and reserve a tour date/time for 1 person.
5. Reserve another tour with additional participant names, up to 4 people total.
6. Try to reserve more places than remain for a selected date/time.
7. Try to reserve an overlapping tour from the same participant account.
8. Check the participant profile and My Bookings page for booking details.
9. Cancel a booking that starts more than 24 hours later.
10. Confirm a booking within 24 hours cannot be cancelled.
11. Log in as a guide and create a tour using only one of the guide's spoken languages.
12. Create one tour without weekly recurrence and confirm only the selected date/time appears.
13. Create one tour with the "Repeat weekly 1 month" switch and confirm the tour repeats on the same weekday for the next four weeks.
14. Edit or delete a guide-owned tour before it has reservations.
15. Confirm a tour with reservations is locked against essential edits.
16. Check the guide profile for reservations and expected participant counts.
17. Submit a post-tour report for a completed booked tour with attendance and proof photo.
18. Log in as administrator and review totals, guides, participants, tours, reports, and reservations by language.

## Deployment

The exam requires deployment on PythonAnywhere. Add the final deployed URL here before submission:

```text
PythonAnywhere URL: TODO
```

For PythonAnywhere, upload the source code, `requirements.txt`, static files, templates, and `istanbul.db`. Configure the WSGI file to import the Flask `app` object from `app.py`.
