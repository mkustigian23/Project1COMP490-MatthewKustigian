"""
tests/test_database.py
======================
Sprint 4 unit tests for db/database.py.

Tests are intentionally isolated from the TUI and from the live server.
Each test creates its own temporary SQLite database so tests never
interfere with each other or with production data.

We test the FUNCTIONS, not just database state afterwards.

Schema used (mirrors the real db.sqlite3 from Sprint 4):
  booking_meetingroom    (id, room_name, capacity, is_active)
  booking_bookinghistory (id, start_time, end_time, no_of_persons,
                          booked_by_id, meeting_room_id)
  member_customuser      (id, username, email, ...)

Coverage map
------------
TestAddRoom
  test_add_room_returns_new_id          — add_room returns an int id
  test_add_room_data_persists           — correct values stored
  test_add_room_appears_in_get_all      — visible via get_all_rooms
  test_add_room_empty_name_raises       — ValueError on blank name
  test_add_room_zero_capacity_raises    — ValueError on capacity = 0
  test_add_room_negative_capacity_raises— ValueError on capacity < 0

TestRemoveRoom
  test_remove_returns_affected_usernames— returns list of usernames
  test_remove_no_bookings_returns_empty — empty list when no reservations
  test_remove_deletes_room              — room gone from get_room_by_id
  test_remove_clears_bookings           — bookings gone from get_bookings
  test_remove_nonexistent_raises        — ValueError on bad id
  test_remove_leaves_other_rooms        — sibling rooms unaffected

TestUpdateCapacity
  test_update_capacity_persists         — new value readable back
  test_update_capacity_zero_raises      — ValueError on 0
  test_update_capacity_negative_raises  — ValueError on negative
  test_update_nonexistent_room_raises   — ValueError on missing room
  test_update_other_fields_unchanged    — room_name/is_active untouched

TestSaveDeletionReport
  test_report_file_created              — file exists on disk
  test_report_contains_room_name        — room name in content
  test_report_contains_usernames        — affected names in content
  test_report_empty_usernames_message   — "No active reservations" note

TestServerConnectivity
  test_server_is_reachable              — live smoke-test (skips if down)
"""

import os
import sqlite3
import sys
import tempfile
import unittest

# Ensure project root is on the path so `db.database` imports cleanly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import (  # noqa: E402
    add_room,
    get_all_rooms,
    get_bookings_for_room,
    get_room_by_id,
    remove_room,
    save_deletion_report,
    update_room_capacity,
)

# ---------------------------------------------------------------------------
# Shared DB fixture — mirrors the real db.sqlite3 schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE member_customuser (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    password     TEXT    NOT NULL DEFAULT '',
    last_login   TEXT,
    email        TEXT    NOT NULL DEFAULT '',
    is_active    INTEGER NOT NULL DEFAULT 1,
    is_staff     INTEGER NOT NULL DEFAULT 0,
    is_superuser INTEGER NOT NULL DEFAULT 0,
    username     TEXT    NOT NULL DEFAULT ''
);
CREATE TABLE booking_meetingroom (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name TEXT    NOT NULL,
    capacity  INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE booking_bookinghistory (
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


def _make_db() -> str:
    """Create a temp DB with schema + minimal seed data. Return its path."""
    fd, path = tempfile.mkstemp(suffix=".sqlite3", prefix="test_sprint4_")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    conn.executemany(
        "INSERT INTO member_customuser (username, email) VALUES (?, ?)",
        [("alice", "a@t.com"), ("bob", "b@t.com"), ("charlie", "c@t.com")],
    )
    conn.executemany(
        "INSERT INTO booking_meetingroom (room_name, capacity) VALUES (?, ?)",
        [
            ("Board Room", 10),
            ("Small Huddle", 3),
            ("Lab", 6),
        ],
    )
    # Room 1: alice(id=1) + bob(id=2) booked
    # Room 2: charlie(id=3) booked
    # Room 3: no bookings
    conn.executemany(
        "INSERT INTO booking_bookinghistory"
        " (meeting_room_id, booked_by_id, start_time, end_time)"
        " VALUES (?, ?, ?, ?)",
        [
            (1, 1, "2026-03-20 09:00:00", "2026-03-20 10:00:00"),
            (1, 2, "2026-03-21 14:00:00", "2026-03-21 15:00:00"),
            (2, 3, "2026-03-20 11:00:00", "2026-03-20 12:00:00"),
        ],
    )
    conn.commit()
    conn.close()
    return path


# =============================================================================
# TestAddRoom
# =============================================================================
class TestAddRoom(unittest.TestCase):

    def setUp(self):
        self.db = _make_db()

    def tearDown(self):
        os.unlink(self.db)

    def test_add_room_returns_new_id(self):
        """add_room must return a positive integer id."""
        new_id = add_room(self.db, "New Room", 5)
        self.assertIsInstance(new_id, int)
        self.assertGreater(new_id, 0)

    def test_add_room_data_persists(self):
        """Values passed to add_room must be readable back via get_room_by_id."""
        new_id = add_room(self.db, "Training Room", 12)
        room = get_room_by_id(self.db, new_id)
        self.assertIsNotNone(room)
        self.assertEqual(room["room_name"], "Training Room")
        self.assertEqual(room["capacity"], 12)

    def test_add_room_appears_in_get_all(self):
        """A newly added room must appear in the list returned by get_all_rooms."""
        before = len(get_all_rooms(self.db))
        add_room(self.db, "Extra Room", 4)
        self.assertEqual(len(get_all_rooms(self.db)), before + 1)

    def test_add_room_empty_name_raises(self):
        """add_room must raise ValueError when name is blank."""
        with self.assertRaises(ValueError):
            add_room(self.db, "   ", 5)

    def test_add_room_zero_capacity_raises(self):
        """add_room must raise ValueError when capacity is 0."""
        with self.assertRaises(ValueError):
            add_room(self.db, "Room X", 0)

    def test_add_room_negative_capacity_raises(self):
        """add_room must raise ValueError when capacity is negative."""
        with self.assertRaises(ValueError):
            add_room(self.db, "Room Y", -3)


# =============================================================================
# TestRemoveRoom
# =============================================================================
class TestRemoveRoom(unittest.TestCase):

    def setUp(self):
        self.db = _make_db()

    def tearDown(self):
        os.unlink(self.db)

    def test_remove_returns_affected_usernames(self):
        """remove_room must return the list of usernames with cancelled bookings."""
        cancelled = remove_room(self.db, 1)
        self.assertIsInstance(cancelled, list)
        self.assertIn("alice", cancelled)
        self.assertIn("bob", cancelled)

    def test_remove_no_bookings_returns_empty(self):
        """Room 3 has no bookings — remove_room should return []."""
        self.assertEqual(remove_room(self.db, 3), [])

    def test_remove_deletes_room(self):
        """After remove_room, get_room_by_id must return None."""
        remove_room(self.db, 1)
        self.assertIsNone(get_room_by_id(self.db, 1))

    def test_remove_clears_bookings(self):
        """After remove_room, get_bookings_for_room must return []."""
        self.assertGreater(len(get_bookings_for_room(self.db, 1)), 0)
        remove_room(self.db, 1)
        self.assertEqual(get_bookings_for_room(self.db, 1), [])

    def test_remove_nonexistent_raises(self):
        """remove_room must raise ValueError for a non-existent room id."""
        with self.assertRaises(ValueError):
            remove_room(self.db, 9999)

    def test_remove_leaves_other_rooms(self):
        """Removing room 1 must leave rooms 2 and 3 intact."""
        remove_room(self.db, 1)
        ids = [r["id"] for r in get_all_rooms(self.db)]
        self.assertIn(2, ids)
        self.assertIn(3, ids)
        self.assertNotIn(1, ids)


# =============================================================================
# TestUpdateCapacity
# =============================================================================
class TestUpdateCapacity(unittest.TestCase):

    def setUp(self):
        self.db = _make_db()

    def tearDown(self):
        os.unlink(self.db)

    def test_update_capacity_persists(self):
        """New capacity value must be readable back after update_room_capacity."""
        update_room_capacity(self.db, 1, 25)
        self.assertEqual(get_room_by_id(self.db, 1)["capacity"], 25)

    def test_update_capacity_zero_raises(self):
        """update_room_capacity must raise ValueError for capacity=0."""
        with self.assertRaises(ValueError):
            update_room_capacity(self.db, 1, 0)

    def test_update_capacity_negative_raises(self):
        """update_room_capacity must raise ValueError for negative capacity."""
        with self.assertRaises(ValueError):
            update_room_capacity(self.db, 1, -5)

    def test_update_nonexistent_room_raises(self):
        """update_room_capacity must raise ValueError for a missing room."""
        with self.assertRaises(ValueError):
            update_room_capacity(self.db, 9999, 10)

    def test_update_other_fields_unchanged(self):
        """update_room_capacity must not alter room_name or is_active."""
        original = get_room_by_id(self.db, 1)
        update_room_capacity(self.db, 1, 50)
        updated = get_room_by_id(self.db, 1)
        self.assertEqual(updated["room_name"], original["room_name"])
        self.assertEqual(updated["is_active"],  original["is_active"])


# =============================================================================
# TestSaveDeletionReport
# =============================================================================
class TestSaveDeletionReport(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_report_file_created(self):
        """save_deletion_report must create a file on disk."""
        path = save_deletion_report(
            self.tmpdir, "Board Room", 1, ["alice", "bob"]
        )
        self.assertTrue(os.path.exists(path))

    def test_report_contains_room_name(self):
        """The room name must appear in the report file content."""
        path = save_deletion_report(self.tmpdir, "Test Room", 99, [])
        with open(path) as fh:
            self.assertIn("Test Room", fh.read())

    def test_report_contains_usernames(self):
        """Every affected username must appear in the report file."""
        path = save_deletion_report(
            self.tmpdir, "X", 1, ["alice", "charlie"]
        )
        with open(path) as fh:
            content = fh.read()
        self.assertIn("alice", content)
        self.assertIn("charlie", content)

    def test_report_empty_usernames_message(self):
        """When no usernames are provided the report must note it."""
        path = save_deletion_report(self.tmpdir, "Empty Room", 5, [])
        with open(path) as fh:
            self.assertIn("No active reservations", fh.read())


# =============================================================================
# TestServerConnectivity  (live — skips gracefully when server is down)
# =============================================================================
class TestServerConnectivity(unittest.TestCase):
    """
    Smoke-tests the deployed server.
    Set the SERVER_URL environment variable (or GitHub Secret) to your
    DigitalOcean droplet address, e.g. http://165.x.x.x:8000
    Falls back to http://localhost:8000 when not set.
    """

    SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000")

    def test_server_is_reachable(self):
        """GET /api/v1/meeting-rooms/available/ -> 200 or 401 (auth required)."""
        import urllib.error
        import urllib.request

        url = f"{self.SERVER_URL}/api/v1/meeting-rooms/available/"
        try:
            try:
                resp = urllib.request.urlopen(url, timeout=5)
                status = resp.status
            except urllib.error.HTTPError as exc:
                status = exc.code           # 401 means server is up
            self.assertIn(
                status, [200, 401,400, 403],
                msg=f"Unexpected HTTP {status} from {url}",
            )
        except (urllib.error.URLError, OSError) as exc:
            self.skipTest(
                f"Server not reachable at {self.SERVER_URL}: {exc}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
