"""
db/database.py
--------------
All SQLite logic for the Room Admin panel.
Zero UI imports — functions return plain Python dicts/lists so they
can be unit-tested without launching any GUI.

Schema (from the real db.sqlite3 provided for Sprint 4):
  booking_meetingroom    (id, room_name, capacity, is_active)
  booking_bookinghistory (id, start_time, end_time, no_of_persons,
                          booked_by_id, meeting_room_id)
  member_customuser      (id, username, email, ...)
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_connection(db_path: str) -> sqlite3.Connection:
    """Return a row_factory-enabled connection with FK enforcement on."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Room queries
# ---------------------------------------------------------------------------

def get_all_rooms(db_path: str) -> list:
    """Return every room as a list of dicts, ordered by id."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT id, room_name, capacity, is_active "
            "FROM booking_meetingroom ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def get_room_by_id(db_path: str, room_id: int) -> Optional[dict]:
    """Return one room dict, or None if not found."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT id, room_name, capacity, is_active "
            "FROM booking_meetingroom WHERE id = ?",
            (room_id,),
        ).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Room mutations
# ---------------------------------------------------------------------------

def add_room(db_path: str, name: str, capacity: int,
             amenities: str = "") -> int:
    """
    Insert a new room. Returns the new row's id.

    ``amenities`` is accepted for API compatibility but this database
    schema does not have an amenities column — the value is silently
    ignored.

    Raises ValueError for empty name or capacity < 1.
    """
    name = name.strip()
    if not name:
        raise ValueError("Room name cannot be empty.")
    if capacity < 1:
        raise ValueError("Capacity must be at least 1.")

    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO booking_meetingroom "
            "(room_name, capacity, is_active) VALUES (?, ?, 1)",
            (name, capacity),
        )
        conn.commit()
    return cur.lastrowid


def remove_room(db_path: str, room_id: int) -> list:
    """
    Delete a room and every booking that references it.

    Returns a list of distinct usernames whose reservations were
    wiped out.

    Raises ValueError if the room does not exist.
    """
    with get_connection(db_path) as conn:
        # Confirm the room exists
        if conn.execute(
            "SELECT 1 FROM booking_meetingroom WHERE id = ?",
            (room_id,),
        ).fetchone() is None:
            raise ValueError(f"Room {room_id} does not exist.")

        # Collect affected usernames before deleting
        rows = conn.execute(
            """
            SELECT DISTINCT cu.username
              FROM booking_bookinghistory b
              JOIN member_customuser cu ON cu.id = b.booked_by_id
             WHERE b.meeting_room_id = ?
            """,
            (room_id,),
        ).fetchall()
        usernames = [r["username"] for r in rows]

        # Delete bookings first (FK), then the room
        conn.execute(
            "DELETE FROM booking_bookinghistory WHERE meeting_room_id = ?",
            (room_id,),
        )
        conn.execute(
            "DELETE FROM booking_meetingroom WHERE id = ?",
            (room_id,),
        )
        conn.commit()

    return usernames


def update_room_capacity(db_path: str, room_id: int,
                         new_capacity: int) -> None:
    """
    Update the capacity of an existing room.

    Raises ValueError for capacity < 1 or unknown room_id.
    """
    if new_capacity < 1:
        raise ValueError("Capacity must be at least 1.")

    with get_connection(db_path) as conn:
        result = conn.execute(
            "UPDATE booking_meetingroom SET capacity = ? WHERE id = ?",
            (new_capacity, room_id),
        )
        conn.commit()
        if result.rowcount == 0:
            raise ValueError(f"Room {room_id} does not exist.")


# ---------------------------------------------------------------------------
# Booking helpers (read-only)
# ---------------------------------------------------------------------------

def get_bookings_for_room(db_path: str, room_id: int) -> list:
    """Return all bookings for a given room."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT b.id, cu.username, b.start_time, b.end_time,
                   b.no_of_persons
              FROM booking_bookinghistory b
              JOIN member_customuser cu ON cu.id = b.booked_by_id
             WHERE b.meeting_room_id = ?
             ORDER BY b.start_time
            """,
            (room_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def save_deletion_report(reports_dir: str, room_name: str,
                         room_id: int,
                         cancelled_usernames: list) -> str:
    """
    Write a plain-text cancellation report to *reports_dir*.
    Creates the directory if it doesn't exist.
    Returns the full path of the file written.
    """
    os.makedirs(reports_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"deletion_report_room{room_id}_{stamp}.txt"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, "w") as fh:
        fh.write("Room Deletion Report\n")
        fh.write("=" * 40 + "\n")
        fh.write(
            f"Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        fh.write(f"Room      : {room_name} (ID: {room_id})\n")
        fh.write(
            f"Cancelled reservations: {len(cancelled_usernames)}\n\n"
        )
        if cancelled_usernames:
            fh.write("Affected usernames:\n")
            for uname in cancelled_usernames:
                fh.write(f"  - {uname}\n")
        else:
            fh.write("No active reservations were cancelled.\n")

    return filepath
