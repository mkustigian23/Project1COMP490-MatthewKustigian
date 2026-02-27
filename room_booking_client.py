import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from langchain_core.tools import tool

load_dotenv() # loads .env file

SERVER_URL = os.getenv("SERVER_URL")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

if not all([SERVER_URL, EMAIL, PASSWORD]):
    raise ValueError("Missing SERVER_URL, EMAIL or PASSWORD in .env file")


def get_auth_token() -> str:
    """
    Logs in once and returns a fresh access token.
    Caches in memory for the current process (simple approach).
    """
    global _cached_token
    if _cached_token is None:
        endpoint = "/api/v1/member/login/"
        data = {"email": EMAIL, "password": PASSWORD}
        response = requests.post(SERVER_URL + endpoint, json=data)
        response.raise_for_status()
        json_data = response.json()
        _cached_token = json_data["token"]["access"]
    return _cached_token


_cached_token: Optional[str] = None


def _make_authenticated_request(
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    json: Optional[Dict] = None,
) -> Dict:
    """Helper: authenticated request with automatic token refresh on 401."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = SERVER_URL + endpoint

    if method.upper() == "GET":
        response = requests.get(url, headers=headers, params=params)
    elif method.upper() == "POST":
        response = requests.post(url, headers=headers, json=json)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")

    if response.status_code == 401:
        # token is probably expired
        global _cached_token
        _cached_token = None
        token = get_auth_token()
        headers["Authorization"] = f"Bearer {token}"
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)

    response.raise_for_status()
    if response.status_code == 204:
        return {"success": True}
    try:
        return response.json()
    except ValueError:
        return {"message": response.text.strip()}


#   Original functions (kept from sprint 2 and minorly edited)



def login() -> str:
    """Legacy login function — prefer get_auth_token() now."""
    return get_auth_token()


def get_available_rooms(start_time: Optional[str] = None, end_time: Optional[str] = None) -> List[Dict]:
    """Retrieves available rooms, optionally filtered by time range."""
    endpoint = "/api/v1/meeting-rooms/available/"
    params = {}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    return _make_authenticated_request("GET", endpoint, params=params)


def book_room(room_id: int, start_time: str, end_time: str, no_of_persons: int = 1) -> Dict:
    """Books a room for the given time range."""
    endpoint = f"/api/v1/meeting-rooms/{room_id}/book/"
    data = {
        "start_time": start_time,
        "end_time": end_time,
        "no_of_persons": no_of_persons,
    }
    return _make_authenticated_request("POST", endpoint, json=data)


def get_my_bookings() -> List[Dict]:
    """Retrieves the authenticated user's booking history."""
    endpoint = "/api/v1/meeting-rooms/my-bookings/"
    return _make_authenticated_request("GET", endpoint)


def cancel_booking(booking_id: int) -> bool:
    """Cancels a single booking by ID."""
    endpoint = f"/api/v1/meeting-rooms/{booking_id}/cancel-booking/"
    result = _make_authenticated_request("DELETE", endpoint)
    return result.get("success", False)



#   LangChain Tools for Sprint 3 (read-only queries)

@tool
def get_current_datetime() -> str:
    """Returns the current date and time in ISO format (YYYY-MM-DDTHH:MM:SS).
Use this for questions involving 'today', 'now', 'current time', etc."""
    return datetime.now().isoformat()


@tool
def get_my_bookings_today() -> str:
    """Returns a human-readable summary of the user's bookings scheduled for today."""
    bookings = get_my_bookings()
    if not bookings:
        return "You have no bookings at all."

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_bookings = [
        b for b in bookings
        if b.get("start_time", "").startswith(today_str)
    ]

    if not today_bookings:
        return "You have no bookings today."

    lines = ["Your bookings today:"]
    for b in sorted(today_bookings, key=lambda x: x.get("start_time", "")):
        start = b.get("start_time", "??").split("T")[-1][:5]  # HH:MM
        end = b.get("end_time", "??").split("T")[-1][:5]
        room = b.get("room_name", b.get("room", "Unknown room"))
        lines.append(f"• {room}  {start} – {end}")
    return "\n".join(lines)


@tool
def get_bookings_for_room(room_name: str) -> str:
    """Returns a summary of all bookings for a given room name (case-insensitive partial match)."""
    bookings = get_my_bookings()  #currently returns my bookings

    if not bookings:
        return "No bookings found (you have none)."

    matching = [
        b for b in bookings
        if room_name.lower() in str(b.get("room_name", "") + b.get("room", "")).lower()
    ]

    if not matching:
        return f"No bookings found for rooms matching '{room_name}'."

    lines = [f"Bookings matching '{room_name}':"]
    for b in sorted(matching, key=lambda x: x.get("start_time", "")):
        start = b.get("start_time", "?")
        end = b.get("end_time", "?")
        who = "you" if True else b.get("user", "someone")  # currently only bookings
        lines.append(f"• {start} – {end} ({who})")
    return "\n".join(lines)


@tool
def list_available_rooms_now_or_soon() -> str:
    """Returns a list of currently available meeting rooms (or soon available)."""
    rooms = get_available_rooms()
    if not rooms:
        return "No rooms are currently available."

    lines = ["Available rooms right now:"]
    for r in rooms:
        name = r.get("name", "Unnamed")
        capacity = r.get("capacity", "?")
        lines.append(f"• {name} (capacity {capacity})")
    return "\n".join(lines)


# ────────────────────────────────────────────────
#   Optional: keep your main() for manual testing
# ────────────────────────────────────────────────

def main():
    token = get_auth_token()
    print("Authenticated successfully.")

    bookings = get_my_bookings()
    print("My bookings:", bookings)

    avail = get_available_rooms()
    print("Available rooms:", avail)

    # Example tool usage (for debugging)
    print(get_my_bookings_today.invoke({}))
    print(get_current_datetime.invoke({}))


if __name__ == "__main__":
    main()