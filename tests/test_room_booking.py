import pytest
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from room_booking_client import login, get_available_rooms, book_room

@pytest.fixture(scope="session")  # session = reuse token across all tests
def auth_token():
    """Get a valid auth token for API calls."""
    token = login()  # assuming your current login() takes no args
    if not token:
        pytest.fail("Login failed - check SERVER_URL, EMAIL, PASSWORD in secrets/env")
    assert isinstance(token, str)
    assert len(token) > 20  # rough check
    return token


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


def test_get_available_rooms(auth_token):
    rooms = get_available_rooms()  # assuming no args needed now

    assert isinstance(rooms, list), "get_available_rooms should return a list"
    assert len(rooms) >= 0, "Should not crash or return None"

    if len(rooms) == 0:
        pytest.skip("No rooms available right now – skipping detailed checks")

    # Only run if we have rooms
    for room in rooms:
        assert 'id' in room
        assert 'room_name' in room or 'name' in room
        assert isinstance(room.get('capacity', 0), int)


def test_book_and_conflict(setup):
    server_url, token = setup

    rooms = get_available_rooms(server_url, token)

    assert isinstance(rooms, list)

    if not rooms:
        pytest.skip("No available rooms to book – skipping test")
    assert len(rooms) > 0, "No available rooms found"
    room_id = rooms[0]["id"]

    # Use a much safer future window
    now = datetime.utcnow()  # or datetime.now()
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

    # make the assertion more specific
    error_text = str(exc.value)
    assert "400" in error_text, f"Expected 400 conflict error, got: {error_text}"