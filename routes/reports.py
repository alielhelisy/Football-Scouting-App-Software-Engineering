from flask import render_template, request, redirect, url_for, session, flash
from app_instance import app
from db import get_db
from utils import login_required, is_admin, get_player_or_404
from models import (
    validate_stars, validate_non_negative_int, validate_cards, validate_position,
    POSITIONS, CARD_OPTIONS, RATING_OPTIONS, RATING_DESCRIPTIONS,
)

def _display_rating(value):
    rating = float(value)
    return int(rating) if rating == int(rating) else rating


def _rating_class(value):
    rating = float(value)
    if rating <= 2:
        return "rating-high"
    if rating <= 3.5:
        return "rating-mid"
    return "rating-low"


def _position_class(position):
    if position in ("6ER", "8ER"):
        return "mid"
    if position in ("WIDE", "CF"):
        return "att"
    if position == "GK":
        return "gk"
    return "def"


@app.route("/reports")
@login_required
def reports_list():
    query = (request.args.get("q") or "").strip()
    selected_position = (request.args.get("position") or "").strip().upper()
    selected_rating = (request.args.get("rating") or "").strip()
    sort = request.args.get("sort", "recent")

    rating_value = None
    if selected_rating:
        try:
            rating_value = validate_stars(selected_rating)
        except ValueError:
            selected_rating = ""

    where = []
    params = []
    if not is_admin():
        where.append("p.user_id = ?")
        params.append(session["user_id"])

    if query:
        like = f"%{query.lower()}%"
        where.append(
            "(LOWER(p.name) LIKE ? OR LOWER(COALESCE(p.team, '')) LIKE ? "
            "OR LOWER(u.username) LIKE ? OR LOWER(COALESCE(r.comments, '')) LIKE ?)"
        )
        params.extend([like, like, like, like])

    if selected_position in POSITIONS:
        where.append("r.rated_position = ?")
        params.append(selected_position)
    else:
        selected_position = ""

    if rating_value is not None:
        where.append("r.rating = ?")
        params.append(rating_value)

    allowed_sorts = {"recent", "oldest", "rating-best", "rating-worst"}
    if sort not in allowed_sorts:
        sort = "recent"
    order_by = {
        "recent": "r.created_at DESC, r.id DESC",
        "oldest": "r.created_at ASC, r.id ASC",
        "rating-best": "r.rating ASC, r.created_at DESC",
        "rating-worst": "r.rating DESC, r.created_at DESC",
    }[sort]

    sql = (
        "SELECT r.id, r.player_id, r.rating, r.minutes_played, r.goals_scored, "
        "r.received_cards, r.rated_position, r.comments, r.created_at, "
        "p.name AS player_name, p.team AS club, u.username AS scout_name "
        "FROM reports r "
        "JOIN players p ON p.id = r.player_id "
        "JOIN users u ON u.id = p.user_id "
    )
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "ORDER BY " + order_by

    rows = get_db().execute(sql, tuple(params)).fetchall()
    reports = []
    for row in rows:
        position = row["rated_position"]
        reports.append({
            "id": row["id"],
            "player_id": row["player_id"],
            "player_name": row["player_name"],
            "club": row["club"] or "-",
            "scout_name": row["scout_name"],
            "rating": _display_rating(row["rating"]),
            "rating_class": _rating_class(row["rating"]),
            "minutes_played": row["minutes_played"],
            "goals_scored": row["goals_scored"],
            "received_cards": row["received_cards"] or "None",
            "card_class": (row["received_cards"] or "None").lower(),
            "position": position,
            "position_display": POSITIONS.get(position, position),
            "position_class": _position_class(position),
            "comments": row["comments"] or "-",
            "date": (row["created_at"] or "")[:10],
        })

    return render_template(
        "reports_list.html",
        reports=reports,
        positions=POSITIONS,
        rating_options=RATING_OPTIONS,
        query=query,
        selected_position=selected_position,
        selected_rating=selected_rating,
        sort=sort,
        admin=is_admin(),
    )

@app.route("/reports/create", methods=["GET", "POST"])
@login_required
def create_report():
    db = get_db()
    if is_admin():
        players = db.execute(
            "SELECT p.*, u.username as scout_name FROM players p "
            "JOIN users u ON p.user_id = u.id ORDER BY p.name"
        ).fetchall()
    else:
        players = db.execute(
            "SELECT p.*, u.username as scout_name FROM players p "
            "JOIN users u ON p.user_id = u.id WHERE p.user_id = ? ORDER BY p.name",
            (session["user_id"],)
        ).fetchall()

    if request.method == "POST":
        player_id = request.form.get("player_id", "")
        try:
            player_id = int(player_id)
            rating    = validate_stars(request.form.get("rating"))
            minutes   = validate_non_negative_int(request.form.get("minutes_played", 0), "Minutes Played")
            goals     = validate_non_negative_int(request.form.get("goals_scored", 0), "Goals Scored")
            cards     = validate_cards(request.form.get("received_cards", "None"))
            rated_pos = validate_position(request.form.get("rated_position", ""))
        except ValueError as e:
            flash(str(e), "error")
            return render_template("create_report.html", players=players,
                                   positions=POSITIONS, card_options=CARD_OPTIONS,
                                   rating_options=RATING_OPTIONS,
                                   rating_descriptions=RATING_DESCRIPTIONS)

        player = get_player_or_404(player_id)
        if not player:
            flash("Player not found.", "error")
            return render_template("create_report.html", players=players,
                                   positions=POSITIONS, card_options=CARD_OPTIONS,
                                   rating_options=RATING_OPTIONS,
                                   rating_descriptions=RATING_DESCRIPTIONS)

        comments = request.form.get("comments", "").strip()
        db.execute(
            "INSERT INTO reports "
            "(player_id, rating, minutes_played, goals_scored, received_cards, rated_position, comments) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (player_id, rating, minutes, goals, cards, rated_pos, comments)
        )
        db.commit()
        flash("Report saved.", "success")
        return redirect(url_for("player_detail", player_id=player_id))

    return render_template("create_report.html", players=players,
                           positions=POSITIONS, card_options=CARD_OPTIONS,
                           rating_options=RATING_OPTIONS,
                           rating_descriptions=RATING_DESCRIPTIONS)



@app.route("/players/<int:player_id>/reports/<int:report_id>/edit", methods=["GET", "POST"])
@login_required
def edit_report(player_id, report_id):
    player = get_player_or_404(player_id)
    if not player:
        flash("Player not found.", "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    report = db.execute(
        "SELECT * FROM reports WHERE id = ? AND player_id = ?",
        (report_id, player_id)
    ).fetchone()
    if not report:
        flash("Report not found.", "error")
        return redirect(url_for("player_detail", player_id=player_id))

    if request.method == "POST":
        try:
            rating = validate_stars(request.form.get("rating"))
            minutes = validate_non_negative_int(request.form.get("minutes_played", 0), "Minutes Played")
            goals = validate_non_negative_int(request.form.get("goals_scored", 0), "Goals Scored")
            cards = validate_cards(request.form.get("received_cards", "None"))
            rated_pos = validate_position(request.form.get("rated_position", ""))
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "edit_report.html",
                player=player,
                report=report,
                positions=POSITIONS,
                card_options=CARD_OPTIONS,
                rating_options=RATING_OPTIONS,
                rating_descriptions=RATING_DESCRIPTIONS,
            )

        comments = request.form.get("comments", "").strip()
        db.execute(
            "UPDATE reports SET rating = ?, minutes_played = ?, goals_scored = ?, "
            "received_cards = ?, rated_position = ?, comments = ? "
            "WHERE id = ? AND player_id = ?",
            (rating, minutes, goals, cards, rated_pos, comments, report_id, player_id)
        )
        db.commit()
        flash("Report updated.", "success")
        return redirect(url_for("player_detail", player_id=player_id))

    return render_template(
        "edit_report.html",
        player=player,
        report=report,
        positions=POSITIONS,
        card_options=CARD_OPTIONS,
        rating_options=RATING_OPTIONS,
        rating_descriptions=RATING_DESCRIPTIONS,
    )
@app.route("/players/<int:player_id>/edit_comment", methods=["GET", "POST"])
@login_required
def edit_comment(player_id):
    player = get_player_or_404(player_id)
    if not player:
        flash("Player not found.", "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    latest = db.execute(
        "SELECT TOP 1 * FROM reports WHERE player_id = ? ORDER BY created_at DESC",
        (player_id,)
    ).fetchone()

    if not latest:
        flash("No report to edit yet.", "error")
        return redirect(url_for("players_by_position", pos_key=player["position"]))

    if request.method == "POST":
        new_comment = request.form.get("comment", "").strip()
        db.execute("UPDATE reports SET comments = ? WHERE id = ?", (new_comment, latest["id"]))
        db.commit()
        flash("Comment updated.", "success")
        return redirect(url_for("players_by_position", pos_key=player["position"]))

    return render_template("edit_comment.html", player=player, latest=latest,
                           pos_display=POSITIONS.get(player["position"], player["position"]))

