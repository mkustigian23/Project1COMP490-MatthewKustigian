import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

def login(server_url, email, password):
    """
    Logs in and returns the access token.
    """
    endpoint = "/api/v1/member/login/"
    data = {"email": email, "password": password}
    response = requests.post(server_url + endpoint, json=data)
    response.raise_for_status()
    return response.json()["access"]

def get_available_rooms(server_url, token, start_time=None, end_time=None):
    """
    Retrieves available rooms, optionally for a time range.
    """
    endpoint = "/api/v1/meeting-rooms/available/"
    headers = {"Authorization": f"Bearer {token}"}
    params = {}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    response = requests.get(server_url + endpoint, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def book_room(server_url, token, room_id, start_time, end_time, no_of_persons=1):
    """
    Books a room for the given time range.
    """
    endpoint = f"/api/v1/meeting-rooms/{room_id}/book/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"start_time": start_time, "end_time": end_time, "no_of_persons": no_of_persons}
    response = requests.post(server_url + endpoint, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def get_my_bookings(server_url, token):
    """
    Retrieves the user's booking history.
    """
    endpoint = "/api/v1/meeting-rooms/my-bookings/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(server_url + endpoint, headers=headers)
    response.raise_for_status()
    return response.json()

def cancel_booking(server_url, token, booking_id):
    """
    Cancels a booking.
    """
    endpoint = f"/api/v1/meeting-rooms/{booking_id}/cancel-booking/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(server_url + endpoint, headers=headers)
    response.raise_for_status()
    return response.status_code == 204

def main():
    load_dotenv()
    server_url = os.getenv("SERVER_URL")
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    # Login
    token = login(server_url, email, password)
    print("Access Token:", token)

    # Get available rooms (without time range)
    available_rooms = get_available_rooms(server_url, token)
    print("Available Rooms:", available_rooms)

    # Pick first available room ID (assume at least one exists)
    if available_rooms:
        room_id = available_rooms[0]["id"]  # Adjust based on actual response structure
    else:
        raise ValueError("No available rooms")

    # Prepare 15-minute reservation times (future time)
    now = datetime.now()
    start_time = (now + timedelta(minutes=5)).strftime("%Y-%m-%d %I:%M %p")  # 5 min from now
    end_time = (now + timedelta(minutes=20)).strftime("%Y-%m-%d %I:%M %p")   # 15 min duration

    # Book room
    booking = book_room(server_url, token, room_id, start_time, end_time)
    print("Booking:", booking)
    booking_id = booking["id"]  # Assume response has 'id'

    # Get my bookings
    my_bookings = get_my_bookings(server_url, token)
    print("My Bookings:", my_bookings)

    # Cancel booking
    canceled = cancel_booking(server_url, token, booking_id)
    print("Canceled:", canceled)

if __name__ == "__main__":
    main()