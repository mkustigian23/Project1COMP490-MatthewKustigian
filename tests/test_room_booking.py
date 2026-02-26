import pytest
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from room_booking_client import login, get_available_rooms, book_room


@pytest.fixture(scope="module")
def setup():
    load_dotenv()
    server_url = os.getenv("SERVER_URL")
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    if not all([server_url, email, password]):
        pytest.fail("Missing SERVER_URL, EMAIL or PASSWORD in .env")

    token = login()
    assert token is not None and isinstance(token, str), "Login failed - no token returned"

    yield server_url, token


def test_login(setup):
    server_url, token = setup
    assert token is not None and isinstance(token, str), "Token should be a non-empty string"


def test_get_available_rooms(setup):
    server_url, token = setup
    rooms = get_available_rooms(server_url, token)
    assert isinstance(rooms, list), "Available rooms should be a list"
    assert len(rooms) > 0, "At least one room should be available"
    assert "id" in rooms[0], "Each room should have an 'id'"
    assert "room_name" in rooms[0], "Each room should have a 'room_name'"


def test_book_and_conflict(setup):
    server_url, token = setup

    rooms = get_available_rooms(server_url, token)
    assert len(rooms) > 0, "No available rooms found"
    room_id = rooms[0]["id"]

    # Use a much safer future window
    now = datetime.utcnow()  # or datetime.now() — UTC often helps with server timezone
    start_time = (now + timedelta(minutes=60)).strftime("%Y-%m-%d %I:%M %p")  # 1 hour ahead
    end_time = (now + timedelta(minutes=75)).strftime("%Y-%m-%d %I:%M %p")

    # Optional: print for debugging in CI
    print(f"Booking room {room_id} from {start_time} to {end_time}")

    # First booking
    booking = book_room(server_url, token, room_id, start_time, end_time)

    # Check success message (this matches your server's actual response)
    assert isinstance(booking, dict)
    assert "message" in booking
    assert "successfully" in booking["message"].lower()

    # Second booking → must fail
    with pytest.raises(Exception) as exc:
        book_room(server_url, token, room_id, start_time, end_time)

    # Optional: make the assertion more specific
    error_text = str(exc.value)
    assert "400" in error_text, f"Expected 400 conflict error, got: {error_text}"