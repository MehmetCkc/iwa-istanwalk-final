from datetime import date, datetime
from pathlib import Path

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)

from admin_data import admin_dashboard_data
from config import secret_key
from db_tour import (AVAILABLE_LANGUAGES, add_reservation,
                     booking_slot_payload, cancel_upcoming_booking,
                     collect_editor_departures, collect_editor_guide_ids,
                     collect_editor_languages, collect_editor_stops,
                     createTour, delete_unbooked_tour, departure_datetime,
                     departures_have_overlap, empty_tour_form,
                     first_available_slot, gallery_images_for,
                     get_dataset_guide_tours, get_dataset_tour,
                     get_homepage_tours, guide_has_tour_overlap, guide_info_for,
                     guide_owns_tour, guide_profile_sections,
                     guide_review_sections, guide_spoken_languages,
                     guide_tours_for, pending_tour_completions_for_guide,
                     profile_tour_sections, remaining_capacity,
                     save_review_for_tour, save_tour_completion,
                     save_tour_departures, save_tour_images, save_tour_stops,
                     time_input_value, tour_calendar_days, tour_categories,
                     tour_has_reservations, update_tour_record,
                     user_has_completed_booking, user_has_overlap,
                     user_has_reviewed_tour,
                     user_has_upcoming_booking_for_tour,
                     validate_tour_editor_form)
from db_user import (checkLogin, createUser, ensure_admin_account,
                     getUserByEmail, getUserById, save_profile_picture,
                     save_user_languages, updateUserPassword,
                     updateUserProfile, user_from_db_row)

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key()
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

login_manager = LoginManager()
login_manager.init_app(app)
ensure_admin_account()


@app.errorhandler(404)
def page_not_found(error):
    image_path = Path(app.static_folder) / "images" / "404.jpg"
    return render_template("404.html", has_404_image=image_path.is_file()), 404


@app.context_processor
def template_helpers():
    return {"time_input_value": time_input_value}


def current_guide_tours():
    if not current_user.is_authenticated or not current_user.isGuide():
        return []
    return get_dataset_guide_tours(current_user.id)


def booking_action_for_tour(tour_id):
    # The same detail page exposes a different primary action for owners,
    # participants, and visitors.
    if current_user.is_authenticated and current_user.isAdmin():
        return {"type": "admin_view"}

    if current_user.is_authenticated and current_user.isGuide():
        tour = get_dataset_tour(tour_id)
        if tour and guide_owns_tour(tour, current_user.id):
            if tour.get("has_reservations"):
                return {"type": "locked"}
            return {"type": "modify"}
        return {"type": "guide_view"}

    if not current_user.is_authenticated or not current_user.isCustomer():
        return {"type": "reserve"}

    _, previous_tours = profile_tour_sections(current_user.id)
    if any(item["tour"]["id"] == tour_id for item in previous_tours):
        if user_has_reviewed_tour(current_user.id, tour_id):
            return {"type": "reviewed"}
        return {"type": "review"}
    return {"type": "reserve"}


@app.route("/")
def home():
    return render_template(
        "index.html",
        tours=get_homepage_tours(),
        categories=tour_categories(),
        today=date.today(),
    )


@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.isAdmin():
        abort(403)
    return render_template("admin.html", **admin_dashboard_data())


@app.route("/who_we_are")
def who_we_are():
    return render_template("who_we_are.html")


@app.route("/signup_guide", methods=["GET", "POST"])
def signup_guide():
    if request.method == "POST":
        name = request.form.get("first_name", "").strip()
        surname = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        selected_languages = request.form.getlist("languages")
        if (
            not name
            or not surname
            or not email
            or not password
            or not selected_languages
        ):
            flash("Complete every field and choose at least one language.", "error")
        elif getUserByEmail(email) is not None:
            flash("That email is already registered.", "error")
        else:
            createUser(name, surname, email, "guide", None, password)
            db_user = getUserByEmail(email)
            save_user_languages(db_user["id"], selected_languages)
            login_user(user_from_db_row(db_user))
            return redirect(url_for("guide_tours"))
    return render_template("signup_guide.html", languages=AVAILABLE_LANGUAGES)


@app.route("/signup_user", methods=["GET", "POST"])
def signup_user():
    if request.method == "POST":
        name = request.form.get("first_name", "").strip()
        surname = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not name or not surname or not email or not password:
            flash("Complete every field to create a participant account.", "error")
        elif getUserByEmail(email) is not None:
            flash("That email is already registered.", "error")
        else:
            createUser(name, surname, email, "member", None, password)
            login_user(user_from_db_row(getUserByEmail(email)))
            return redirect(url_for("home"))
    return render_template("signup_user.html")


@app.route("/add_tour", methods=["GET", "POST"])
@login_required
def add_tour():
    if not current_user.isGuide():
        abort(403)
    guide_languages = guide_spoken_languages(current_user.id)

    if request.method == "POST":
        validation_errors = validate_tour_editor_form(request.form)
        if validation_errors:
            flash(validation_errors[0], "error")
            return redirect(url_for("add_tour"))
        guide_ids, missing_guide_emails = collect_editor_guide_ids(
            request.form, current_user.id
        )
        if missing_guide_emails:
            flash(f"Guide email not found: {', '.join(missing_guide_emails)}", "error")
            return redirect(url_for("add_tour"))
        selected_languages = collect_editor_languages(request.form)
        if not selected_languages or any(
            language not in guide_languages for language in selected_languages
        ):
            flash("Choose only languages from your guide profile.", "error")
            return redirect(url_for("add_tour"))
        departures = collect_editor_departures(request.form)
        if not departures:
            flash("Add a departure time and language.", "error")
            return redirect(url_for("add_tour"))
        duration_minutes = int(request.form.get("duration_minutes") or 120)
        if departures_have_overlap(departures, duration_minutes):
            flash("Tour departure times overlap each other.", "error")
            return redirect(url_for("add_tour"))
        if any(
            guide_has_tour_overlap(guide_id, departures, duration_minutes)
            for guide_id in guide_ids
        ):
            flash(
                "One of the assigned guides already has another tour in this date and time.",
                "error",
            )
            return redirect(url_for("add_tour"))

        next_id = createTour(
            request.form.get("name"),
            request.form.get("description"),
            request.form.get("max_participants"),
            request.form.get("meeting_point"),
            guide_ids,
            selected_languages,
            request.form.get("category"),
            duration_minutes,
        )
        save_tour_departures(next_id, departures)
        save_tour_stops(
            next_id,
            collect_editor_stops(
                request.form, request.files, empty_tour_form()["stops"]
            ),
        )
        save_tour_images(next_id, request.files, empty_tour_form()["gallery_images"])
        return redirect(url_for("guide_tours"))

    empty_form = empty_tour_form()
    return render_template(
        "add_tour.html",
        form_tour=empty_form,
        gallery_images=empty_form["gallery_images"],
        calendar_days=tour_calendar_days({"times": []}),
        categories=tour_categories(),
        languages=guide_languages,
    )


@app.route("/guide_tours")
@login_required
def guide_tours():
    if not current_user.isGuide():
        abort(403)
    return render_template(
        "guide_tours.html",
        tours=current_guide_tours(),
        pending_completions=pending_tour_completions_for_guide(current_user.id),
    )


@app.route("/edit_tour/<int:tour_id>", methods=["GET", "POST"])
@login_required
def edit_tour(tour_id):
    if not current_user.isGuide():
        abort(403)
    tour = get_dataset_tour(tour_id)
    if tour is None:
        abort(404)
    if not guide_owns_tour(tour, current_user.id):
        abort(403)
    if tour_has_reservations(tour_id):
        flash(
            "This tour already has reservations and can no longer be modified.", "error"
        )
        return redirect(url_for("guide_tours"))
    guide_languages = guide_spoken_languages(current_user.id)

    if request.method == "POST":
        validation_errors = validate_tour_editor_form(request.form)
        if validation_errors:
            flash(validation_errors[0], "error")
            return redirect(url_for("edit_tour", tour_id=tour_id))
        _, missing_guide_emails = collect_editor_guide_ids(
            request.form, current_user.id
        )
        if missing_guide_emails:
            flash(f"Guide email not found: {', '.join(missing_guide_emails)}", "error")
            return redirect(url_for("edit_tour", tour_id=tour_id))
        selected_languages = collect_editor_languages(request.form)
        if not selected_languages or any(
            language not in guide_languages for language in selected_languages
        ):
            flash("Choose only languages from your guide profile.", "error")
            return redirect(url_for("edit_tour", tour_id=tour_id))
        departures = collect_editor_departures(request.form)
        if not departures:
            flash("Add a departure time and language.", "error")
            return redirect(url_for("edit_tour", tour_id=tour_id))
        duration_minutes = int(
            request.form.get("duration_minutes") or tour.get("duration_minutes") or 120
        )
        if departures_have_overlap(departures, duration_minutes):
            flash("Tour departure times overlap each other.", "error")
            return redirect(url_for("edit_tour", tour_id=tour_id))
        guide_ids, _ = collect_editor_guide_ids(request.form, current_user.id)
        if any(
            guide_has_tour_overlap(
                guide_id, departures, duration_minutes, excluded_tour_id=tour_id
            )
            for guide_id in guide_ids
        ):
            flash(
                "One of the assigned guides already has another tour in this date and time.",
                "error",
            )
            return redirect(url_for("edit_tour", tour_id=tour_id))
        update_tour_record(tour_id, request.form, request.files, tour, current_user.id)
        return redirect(url_for("guide_tours"))

    return render_template(
        "edit_tour.html",
        tour=tour,
        form_tour=tour,
        gallery_images=gallery_images_for(tour),
        calendar_days=tour_calendar_days(tour),
        categories=tour_categories(),
        languages=guide_languages,
    )


@app.route("/cancel_tour/<int:tour_id>", methods=["POST"])
@login_required
def cancel_tour(tour_id):
    if not current_user.isGuide():
        abort(403)
    tour = get_dataset_tour(tour_id)
    if tour is None:
        abort(404)
    if not guide_owns_tour(tour, current_user.id):
        abort(403)
    if delete_unbooked_tour(tour_id):
        flash("Tour cancelled.", "success")
    else:
        flash("Tours with bookings cannot be cancelled.", "error")
    return redirect(url_for("guide_tours"))


@app.route("/my_bookings")
@login_required
def my_bookings():
    if not current_user.isCustomer():
        abort(403)
    upcoming_tours, previous_tours = profile_tour_sections(current_user.id)
    return render_template(
        "my_bookings.html", upcoming_tours=upcoming_tours, previous_tours=previous_tours
    )


@app.route("/cancel_booking/<int:tour_id>", methods=["POST"])
@login_required
def cancel_booking(tour_id):
    if not current_user.isCustomer():
        abort(403)
    if get_dataset_tour(tour_id) is None:
        abort(404)
    if not cancel_upcoming_booking(current_user.id, tour_id):
        flash("Bookings cannot be cancelled within 24 hours of the tour.", "error")
    return redirect(url_for("my_bookings"))


@app.route("/book_tour/<int:tour_id>", methods=["POST"])
@login_required
def book_tour(tour_id):
    if not current_user.isCustomer():
        abort(403)
    tour = get_dataset_tour(tour_id)
    if tour is None:
        abort(404)

    date_value = request.form.get("date", "")
    time_label = request.form.get("time", "")
    try:
        people_count = int(request.form.get("people_count", "1"))
    except ValueError:
        people_count = 1
    participant_names = [
        name.strip()
        for name in request.form.getlist("participant_names[]")
        if name.strip()
    ]

    # Never trust a posted date/time: only accept a departure currently stored
    # for this tour before checking capacity and schedule conflicts.
    valid_slots = {
        (departure["date"], departure["time"])
        for departure in tour.get("departures", [])
    }
    if (date_value, time_label) not in valid_slots:
        session["booking_error"] = "Choose an available tour time."
        return redirect(url_for("tour_details", tour_id=tour_id))

    if departure_datetime(date_value, time_label) < datetime.now():
        session["booking_error"] = "Choose an upcoming tour time."
        return redirect(url_for("tour_details", tour_id=tour_id))

    if people_count < 1 or people_count > 4:
        session["booking_error"] = (
            "You can reserve for yourself and up to 3 friends (4 people total)."
        )
        return redirect(url_for("tour_details", tour_id=tour_id))

    if len(participant_names) != max(0, people_count - 1):
        session["booking_error"] = "Enter the other participants' names."
        return redirect(url_for("tour_details", tour_id=tour_id))

    remaining = remaining_capacity(tour, date_value, time_label)
    if people_count > remaining:
        session["booking_error"] = f"Only {remaining} place(s) are left for that time."
        return redirect(url_for("tour_details", tour_id=tour_id))

    if user_has_overlap(
        current_user.id, date_value, time_label, tour.get("duration_minutes", 120)
    ):
        session["booking_error"] = (
            "You already have another booking that overlaps this tour."
        )
        return redirect(url_for("tour_details", tour_id=tour_id))

    add_reservation(
        tour_id,
        current_user.id,
        date_value,
        time_label,
        people_count,
        participant_names,
    )
    return redirect(url_for("my_bookings"))


@app.route("/complete_tour/<int:tour_id>", methods=["POST"])
@login_required
def complete_tour(tour_id):
    if not current_user.isGuide():
        abort(403)
    tour = get_dataset_tour(tour_id)
    if tour is None or not guide_owns_tour(tour, current_user.id):
        abort(404)
    try:
        attendance = max(0, int(request.form.get("attendance", "0")))
    except ValueError:
        attendance = 0
    save_tour_completion(
        tour_id,
        current_user.id,
        request.form.get("date", ""),
        request.form.get("time", ""),
        attendance,
        request.files.get("proof_image"),
    )
    return redirect(url_for("guide_tours"))


@app.route("/add_review/<int:tour_id>", methods=["GET", "POST"])
@login_required
def add_review(tour_id):
    if not current_user.isCustomer():
        abort(403)
    tour = get_dataset_tour(tour_id)
    if tour is None:
        abort(404)
    if user_has_reviewed_tour(current_user.id, tour_id):
        flash("You already reviewed this tour.", "error")
        return redirect(url_for("my_bookings"))
    if not user_has_completed_booking(current_user.id, tour_id):
        abort(403)
    if request.method == "POST":
        try:
            point = int(round(float(request.form.get("point", "5"))))
        except ValueError:
            point = 5
        point = max(1, min(5, point))
        save_review_for_tour(
            tour, current_user.id, point, request.form.get("review", "").strip()
        )
        return redirect(url_for("my_bookings"))
    return render_template("add_review.html", tour=tour)


@app.route("/tours/<int:tour_id>")
def tour_details(tour_id):
    tour = get_dataset_tour(tour_id)
    if tour is None:
        abort(404)
    default_slot = first_available_slot(tour)
    return render_template(
        "tour_details.html",
        tour=tour,
        gallery_images=gallery_images_for(tour),
        calendar_days=tour_calendar_days(tour),
        booking_action=booking_action_for_tour(tour_id),
        booking_error=session.pop("booking_error", None),
        booking_slots=booking_slot_payload(tour),
        default_slot=default_slot,
        default_people_limit=(
            min(4, remaining_capacity(tour, default_slot["date"], default_slot["time"]))
            if default_slot
            else 0
        ),
        has_upcoming_booking=(
            user_has_upcoming_booking_for_tour(current_user.id, tour_id)
            if current_user.is_authenticated and current_user.isCustomer()
            else False
        ),
    )


@app.route("/guides/<guide_id>")
def guide_info(guide_id):
    guide = guide_info_for(guide_id)
    if guide is None:
        abort(404)
    return render_template(
        "guide_info.html", guide=guide, guide_tours=guide_tours_for(guide_id)
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        user = checkLogin(request.form["email"], request.form["password"])
        if user:
            login_user(user_from_db_row(user))
            if user["type"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


@login_manager.user_loader
def load_user(user_id):
    db_user = getUserById(user_id)
    if db_user:
        return user_from_db_row(db_user)
    return None


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if current_user.isAdmin():
        return redirect(url_for("admin_dashboard"))
    edit_mode = request.args.get("edit") == "1"
    password_mode = request.args.get("password") == "1"
    error = None

    if request.method == "POST":
        edit_mode = True
        password_mode = request.form.get("password_mode") == "1"
        name = request.form.get("name", "").strip()
        surname = request.form.get("surname", "").strip()
        email = request.form.get("email", "").strip()
        location = request.form.get("location", "").strip()
        profile_picture = current_user.profile_picture
        uploaded_picture = request.files.get("profile_picture")
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not surname or not email:
            error = "First name, last name, and email are required."
        elif uploaded_picture and uploaded_picture.filename:
            profile_picture = save_profile_picture(uploaded_picture)
            if profile_picture is None:
                error = "Upload a valid image file for your profile picture."

        if error is None and (new_password or confirm_password or old_password):
            password_mode = True
            if not old_password or not new_password or not confirm_password:
                error = "Enter your old password and type the new password twice."
            elif new_password != confirm_password:
                error = "New passwords do not match."
            elif len(new_password) < 8:
                error = "New password must be at least 8 characters."
            elif not updateUserPassword(current_user.id, old_password, new_password):
                error = "Old password is incorrect."

        if error is None:
            updateUserProfile(
                current_user.id, name, surname, email, location, profile_picture
            )
            return redirect(url_for("profile"))

    upcoming_tours, previous_tours = profile_tour_sections(current_user.id)
    guide_current_tours = []
    guide_previous_tours = []
    guide_languages = []
    guide_reviews = []
    if current_user.isGuide():
        guide_current_tours, guide_previous_tours = guide_profile_sections(
            current_user.id
        )
        guide_languages = guide_spoken_languages(current_user.id)
        guide_reviews = guide_review_sections(current_user.id)
    return render_template(
        "profile.html",
        edit_mode=edit_mode,
        password_mode=password_mode,
        error=error,
        upcoming_tours=upcoming_tours,
        previous_tours=previous_tours,
        guide_current_tours=guide_current_tours,
        guide_previous_tours=guide_previous_tours,
        guide_languages=guide_languages,
        guide_reviews=guide_reviews,
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000)
