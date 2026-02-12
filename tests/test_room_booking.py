import pytest
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from roomBookingClient import login, get_available_rooms, book_room

@pytest.fixture(scope="module")
def setup():
    load_dotenv()
    server_url = os.getenv("SERVER_URL")
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    token = login(server_url, email, password)
    yield server_url, token

def test_login(setup):
    server_url, token = setup
    assert token is not None and isinstance(token, str)

def test_get_available_rooms(setup):
    server_url, token = setup
    rooms = get_available_rooms(server_url, token)
    assert isinstance(rooms, list)
    assert len(rooms) > 0  # Assuming the server has at least one room; adjust if needed

def test_book_and_conflict(setup):
    server_url, token = setup
    # Get available rooms
    rooms = get_available_rooms(server_url, token)
    assert len(rooms) > 0
    room_id = rooms[0]["id"]  # Assume structure has 'id'

    # 15-min reservation (future time)
    now = datetime.now()
    start_time = (now + timedelta(minutes=5)).strftime("%Y-%m-%d %I:%M %p")
    end_time = (now + timedelta(minutes=20)).strftime("%Y-%m-%d %I:%M %p")

    # First booking should succeed
    booking = book_room(server_url, token, room_id, start_time, end_time)
    assert "id" in booking  # Assume successful response has 'id'

    # Second booking same time/room should fail
    with pytest.raises(Exception):  # Assuming raises HTTP error
        book_room(server_url, token, room_id, start_time, end_time)