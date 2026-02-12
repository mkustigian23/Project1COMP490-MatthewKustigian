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

    print("Status code:", response.status_code)
    print("Raw response text:", response.text)  # keep for now
    response.raise_for_status()

    json_data = response.json()
    print("Parsed JSON:", json_data)  # keep for now

    # FIXED: access the nested "token" → "access"
    access_token = json_data["token"]["access"]

    return access_token

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
    endpoint = f"/api/v1/meeting-rooms/{booking_id}/cancel-booking/"
    headers = {"Authorization": f"Bearer {token}"}

    print(f"Cancel attempt for booking ID: {booking_id}")
    print(f"Full URL: {server_url + endpoint}")

    response = requests.delete(server_url + endpoint, headers=headers)

    print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")

    if response.status_code == 204:
        return True
    else:
        # Don't raise yet – let us see the message
        print("Cancel failed with message above")
        response.raise_for_status()
        return False

def cancel_all_bookings(server_url, token):
    """
    Cancels all current bookings for the authenticated user.
    Returns a list of results: (booking_id, success, message/error)
    """
    results = []

    # Step 1: Get all my bookings
    my_bookings = get_my_bookings(server_url, token)

    if not my_bookings:
        print("No bookings to cancel.")
        return results

    print(f"Found {len(my_bookings)} booking(s) to cancel.")

    # Step 2: Cancel each one
    for booking in my_bookings:
        booking_id = booking.get('id')

        if not booking_id:
            results.append((None, False, "No ID found in booking data"))
            continue

        try:
            success = cancel_booking(server_url, token, booking_id)
            results.append((booking_id, success, "Canceled successfully"))
            print(f"Canceled booking {booking_id}: Success")
        except Exception as e:
            error_msg = str(e)
            results.append((booking_id, False, error_msg))
            print(f"Failed to cancel booking {booking_id}: {error_msg}")

    return results

def main():
    load_dotenv()
    server_url = os.getenv("SERVER_URL")
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    # Login
    token = login(server_url, email, password)
    print("Access Token:", token)

    my_bookings = get_my_bookings(server_url, token)
    print("Current bookings:", my_bookings)

    # Cancel ALL ROOM BOOKINGS TO LET CLASSMATES HAVE SOME
    # cancel_results = cancel_all_bookings(server_url, token)
    # print("Cancel all results:", cancel_results)

    # Get available rooms (without time range)
    available_rooms = get_available_rooms(server_url, token)
    print("Available Rooms:", available_rooms)

    # Pick first available room ID (assume at least one exists)
    if available_rooms:
        room_id = available_rooms[2]["id"]
    else:
        raise ValueError("No available rooms")

    # Prepare 15-minute reservation times (future time)
    now = datetime.now()
    start_time = (now + timedelta(hours=8, minutes=120)).strftime("%Y-%m-%d %I:%M %p")
    end_time = (now + timedelta(hours=8, minutes=135)).strftime("%Y-%m-%d %I:%M %p")

    booking = book_room(server_url, token, room_id, start_time, end_time)
    print("Booking:", booking)  # will show {'message': '...'}

    # Now get the updated list of your bookings
    my_bookings = get_my_bookings(server_url, token)
    print("My Bookings after booking:", my_bookings)

    if my_bookings:
        # Take the last one (most recent)
        latest_booking = my_bookings[-1]

        # Get the ID – use .get() to avoid crash if key missing
        booking_id = latest_booking.get('id')

        if booking_id is not None:
            print(f"New booking ID: {booking_id}")

            # canceled = cancel_booking(server_url, token, booking_id) # COMMENTED OUT BUT THIS WILL CANCEL A BOOKING
            # print("Canceled:", canceled)
        else:
            print("No 'id' key in the latest booking. Full latest booking:", latest_booking)
    else:
        print("No bookings found after creating one – check if booking really succeeded")

    # Get my bookings
    my_bookings = get_my_bookings(server_url, token)
    print("My Bookings:", my_bookings)

    # Cancel booking
    canceled = cancel_booking(server_url, token, booking_id)
    print("Canceled:", canceled)

if __name__ == "__main__":
    main()