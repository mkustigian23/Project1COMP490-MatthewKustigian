"""
create_test_db.py
-----------------
Creates a local SQLite database whose schema matches the real
db.sqlite3 provided for Sprint 4 (and the Django models in
jsantore/Room_booking_serve):

  member_customuser      — users / login accounts
  booking_meetingroom    — the rooms admin can manage
  booking_bookinghistory — reservations linking users to rooms

Usage:
    python create_test_db.py              # writes db.sqlite3
    python create_test_db.py mydb.sqlite3
    python create_test_db.py test_ci.sqlite3
"""

import sqlite3
import sys

SCHEMA = """
CREATE TABLE IF NOT EXISTS member_customuser (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    password     TEXT    NOT NULL DEFAULT '',
    last_login   TEXT,
    email        TEXT    NOT NULL DEFAULT '',
    is_active    INTEGER NOT NULL DEFAULT 1,
    is_staff     INTEGER NOT NULL DEFAULT 0,
    is_superuser INTEGER NOT NULL DEFAULT 0,
    username     TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS booking_meetingroom (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name TEXT    NOT NULL,
    capacity  INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS booking_bookinghistory (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time      TEXT    NOT NULL,
    end_time        TEXT    NOT NULL,
    no_of_persons   INTEGER NOT NULL DEFAULT 1,
    booked_by_id    INTEGER NOT NULL
                    REFERENCES member_customuser(id) ON DELETE CASCADE,
    meeting_room_id INTEGER NOT NULL
                    REFERENCES booking_meetingroom(id) ON DELETE CASCADE
);
"""

SEED = """
INSERT INTO member_customuser (username, email) VALUES
    ('alice',   'alice@example.com'),
    ('bob',     'bob@example.com'),
    ('charlie', 'charlie@example.com'),
    ('diana',   'diana@example.com');

INSERT INTO booking_meetingroom (room_name, capacity, is_active) VALUES
    ('Board Room',       10, 1),
    ('Conference A',      6, 1),
    ('Huddle Space',      3, 1),
    ('Executive Suite',  20, 1);

INSERT INTO booking_bookinghistory
    (meeting_room_id, booked_by_id, start_time, end_time, no_of_persons) VALUES
    (1, 1, '2026-03-20 09:00:00', '2026-03-20 10:00:00', 3),
    (1, 2, '2026-03-21 14:00:00', '2026-03-21 15:00:00', 5),
    (2, 3, '2026-03-20 11:00:00', '2026-03-20 12:00:00', 2),
    (3, 1, '2026-03-22 10:00:00', '2026-03-22 11:00:00', 1),
    (3, 4, '2026-03-23 13:00:00', '2026-03-23 14:00:00', 2),
    (4, 2, '2026-03-20 15:00:00', '2026-03-20 16:00:00', 8);
"""


def create_db(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executescript(SEED)
    conn.commit()
    conn.close()
    print(f"Sample database created at: {path}")
    print("Rooms : Board Room, Conference A, Huddle Space, Executive Suite")
    print("Users : alice, bob, charlie, diana")
    print("Run   : python tui_app.py", path)


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "db.sqlite3"
    create_db(output)
