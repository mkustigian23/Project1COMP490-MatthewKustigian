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

    token = login(server_url, email, password)
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

    # Get available rooms
    rooms = get_available_rooms(server_url, token)
    assert len(rooms) > 0, "No available rooms found"
    room_id = rooms[0]["id"]

    # Use a clearly future time
    now = datetime.now()
    start_time = (now + timedelta(minutes=30)).strftime("%Y-%m-%d %I:%M %p")
    end_time = (now + timedelta(minutes=45)).strftime("%Y-%m-%d %I:%M %p")

    # First booking should succeed
    booking = book_room(server_url, token, room_id, start_time, end_time)


    assert isinstance(booking, dict), "Booking response should be a dict"
    assert "message" in booking, "Booking should return a message"
    assert "successfully" in booking["message"].lower(), "Booking message should indicate success"

    # Second booking for SAME time + room should fail (conflict)
    with pytest.raises(Exception) as exc_info:
        book_room(server_url, token, room_id, start_time, end_time)

    #Check that the exception is a 400 or conflict-related
    assert "400" in str(exc_info.value) or "conflict" in str(exc_info.value).lower() or "already" in str(
        exc_info.value).lower(), \
        f"Expected conflict error, got: {exc_info.value}"