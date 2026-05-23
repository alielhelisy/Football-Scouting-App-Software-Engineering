# Football Scouting App

Software Engineering final project built with Flask and Microsoft SQL Server.

**Student 1:** Ali Elhelisy | **ID:** 220303928  
**Student 2:** Mazen Mohamed | **ID:** 220303940

## Overview

Football Scouting App is a multi-user web application for football scouts. Scouts can create player profiles, organize players by tactical position, write scouting reports, search players, and review report history. Admin users can manage accounts and view data across scouts.

## Main Features

- Register, login, logout, and account deletion.
- Login accepts username or email.
- Scout accounts can manage their own players and reports.
- Admin accounts can add users, delete users, and change user roles.
- The main protected admin account is the username `admin`.
- Tactical dashboard grouped by the project positions.
- Player CRUD: add, edit, delete, profile view.
- Report creation with the project rating scale.
- Search by position, name, and club.
- Dark themed pages with separated CSS files.
- Unit tests for business logic.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python + Flask |
| Database | Microsoft SQL Server |
| Database Driver | pyodbc + ODBC Driver 17 for SQL Server |
| Frontend | Jinja2 templates, HTML, CSS |
| Testing | pytest |

## Project Structure

```text
scouting_app/
|-- app.py
|-- app_instance.py
|-- db.py
|-- migrate.py
|-- models.py
|-- schema.sql
|-- utils.py
|-- routes/
|   |-- __init__.py
|   |-- admin.py
|   |-- auth.py
|   |-- players.py
|   |-- reports.py
|   `-- search.py
|-- templates/
|   |-- base.html
|   |-- login.html
|   |-- register.html
|   |-- dashboard.html
|   |-- account_info.html
|   |-- admin_accounts.html
|   |-- admin_add_account.html
|   |-- add_player.html
|   |-- edit_player.html
|   |-- player_detail.html
|   |-- players_by_position.html
|   |-- create_report.html
|   |-- edit_comment.html
|   `-- search.html
|-- static/
|   `-- css/
|       |-- 01-base.css
|       |-- 02-dashboard-legacy.css
|       |-- 03-common-tables.css
|       |-- 04-position-players.css
|       |-- 05-search-legacy.css
|       |-- 06-player-pages.css
|       |-- 07-add-player.css
|       |-- 08-dashboard-board.css
|       |-- 09-add-player-refinements.css
|       |-- 10-dashboard-home.css
|       |-- 11-account.css
|       |-- 12-reports.css
|       |-- 13-search.css
|       |-- 14-admin-accounts.css
|       `-- 15-auth.css
`-- tests/
    `-- test_logic.py
```

## Dashboard Positions

| Key | Display |
|---|---|
| CB | CB |
| FB | FB (Walker) |
| FB_CANCELO | FB (Cancelo) |
| FB_DELPH | FB (Delph) |
| 6ER | 6er |
| 8ER | 8er |
| WIDE | Wide player |
| CF | CF |

## Rating Scale

| Rating | Meaning |
|---|---|
| 1 | Very good performer and very suitable for our system. |
| 2 | Promising performer and very suitable for our system. |
| 2.5 | Very suitable player and could become a promising performer if he changes position. |
| 3 | Very suitable player. |
| 3.5 | Has one desired quality and might become very suitable if he changes position. |
| 4 | Not very suitable but has one or more desired qualities. |
| 4.5 | Might have a desired quality if he changes position. |
| 5 | Not suitable, no desired qualities, and no prospect of changing position. |

## Database Tables

### users

```text
id
username
name
surname
email
password_hash
role
```

### players

```text
id
user_id
name
gender
team
position
other_position
first_name
last_name
nationality
birthday
height
weight
foot
```

### reports

```text
id
player_id
rating
minutes_played
goals_scored
received_cards
rated_position
comments
created_at
```

## Run the App

From the project folder:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Run Tests

```bash
python -m pytest
```

Current test result: `38 passed`.

## SQL Server Settings

| Setting | Value |
|---|---|
| Server | localhost\SQLEXPRESS |
| Database | ScoutingApp |
| Driver | ODBC Driver 17 for SQL Server |
| Authentication | Windows Authentication |

## Notes

- Tables are created automatically by the app when missing.
- `schema.sql` can be used to recreate the database manually.
- CSS is loaded from separate files in `static/css/` through `templates/base.html`.
- Business logic is kept in `models.py` and covered by unit tests.
- Cache and local editor folders such as `__pycache__/`, `.pytest_cache/`, and `.vscode/` are ignored by Git.
