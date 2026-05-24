from flask import render_template, request, redirect, url_for, session, flash
from app_instance import app
from db import get_db
from utils import hash_password, login_required, is_admin
from models import POSITIONS


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        name     = request.form.get("name", "").strip()
        surname  = request.form.get("surname", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        role     = "SCOUT"

        if not username or not name or not surname or not email or not password:
            flash("Username, name, surname, email, and password are required.", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        db = get_db()
        if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            flash("Username already taken.", "error")
            return render_template("register.html")
        if db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            flash("Email already used.", "error")
            return render_template("register.html")

        db.execute(
            "INSERT INTO users (username, name, surname, email, password_hash, role) VALUES (?, ?, ?, ?, ?, ?)",
            (username, name, surname, email, hash_password(password), role)
        )
        db.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_id = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?", (login_id, login_id)
        ).fetchone()
        if not user or user["password_hash"] != hash_password(password):
            flash("Invalid username/email or password.", "error")
            return render_template("login.html")
        session.clear()
        session["user_id"]  = user["id"]
        session["username"] = user["username"]
        session["role"]     = user["role"]
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/account/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_password or not new_password or not confirm_password:
            flash("All password fields are required.", "error")
            return render_template("change_password.html")
        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("change_password.html")
        if len(new_password) < 6:
            flash("New password must be at least 6 characters.", "error")
            return render_template("change_password.html")

        db = get_db()
        user = db.execute("SELECT password_hash FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        if not user or user["password_hash"] != hash_password(current_password):
            flash("Current password is incorrect.", "error")
            return render_template("change_password.html")

        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), session["user_id"])
        )
        db.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("account_info"))

    return render_template("change_password.html")



@app.route("/account")
@login_required
def account_info():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    if not user:
        flash("Account not found.", "error")
        return redirect(url_for("dashboard"))

    total_players = db.execute(
        "SELECT COUNT(*) AS count FROM players WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()["count"]

    total_reports = db.execute(
        "SELECT COUNT(*) AS count FROM reports r "
        "JOIN players p ON p.id = r.player_id WHERE p.user_id = ?",
        (session["user_id"],)
    ).fetchone()["count"]

    tab = request.args.get("tab", "activities")
    if tab not in ("activities", "players"):
        tab = "activities"

    activities = db.execute(
        "SELECT TOP 10 r.*, p.name AS player_name, p.position AS player_position, "
        "CASE WHEN p.birthday IS NULL THEN NULL "
        "     ELSE DATEDIFF(year, p.birthday, GETDATE()) - "
        "          CASE WHEN DATEADD(year, DATEDIFF(year, p.birthday, GETDATE()), p.birthday) > GETDATE() THEN 1 ELSE 0 END "
        "END AS player_age "
        "FROM reports r JOIN players p ON p.id = r.player_id "
        "WHERE p.user_id = ? ORDER BY r.created_at DESC",
        (session["user_id"],)
    ).fetchall()

    players = db.execute(
        "SELECT p.*, COUNT(r.id) AS report_count, "
        "CASE WHEN p.birthday IS NULL THEN NULL "
        "     ELSE DATEDIFF(year, p.birthday, GETDATE()) - "
        "          CASE WHEN DATEADD(year, DATEDIFF(year, p.birthday, GETDATE()), p.birthday) > GETDATE() THEN 1 ELSE 0 END "
        "END AS player_age "
        "FROM players p LEFT JOIN reports r ON r.player_id = p.id "
        "WHERE p.user_id = ? "
        "GROUP BY p.id, p.user_id, p.name, p.gender, p.team, p.position, p.other_position, "
        "         p.first_name, p.last_name, p.nationality, p.birthday, p.height, p.weight, p.foot "
        "ORDER BY p.position, p.name",
        (session["user_id"],)
    ).fetchall()

    return render_template(
        "account_info.html",
        user=user,
        total_players=total_players,
        total_reports=total_reports,
        activities=activities,
        players=players,
        tab=tab,
        positions=POSITIONS,
    )


@app.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    db = get_db()
    user_id = session["user_id"]
    user = db.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if user and user["username"].lower() == "admin":
        flash("The main admin account cannot be deleted.", "error")
        return redirect(url_for("account_info"))
    db.execute("DELETE FROM players WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    session.clear()
    flash("Your account has been deleted.", "success")
    return redirect(url_for("login"))
