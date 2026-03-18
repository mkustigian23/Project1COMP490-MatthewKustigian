# Meeting Room Booking System

## Overview
The Meeting Room Booking System that allows users to book meeting rooms, view available meeting rooms, and manage their bookings.

## Features

### 1. Members Login
- Endpoint: `api/v1/member/login/`
- Method: POST
- Members can log in using their email and password. (send json with keys "email" and "password")
- returns a JWT token object with access and refresh if login is successful.
- Self-registration is not permitted; members are created exclusively through Django admin, and only they can access the login functionality.
- 


### 2. List Available Meeting Rooms
- Endpoint: `/api/v1/meeting-rooms/available/`
- Method: GET
- login required
- Parameters sent in json (both optional):
  - `start_time` (str in strftime format):
  - `end_time` (str strftime format):
- Lists all [available] meeting rooms based on the specified time range. (my testing indicates that it will list all rooms even if already booked as of Feb 4)

### 3. Book a Meeting Room
- Endpoint: `/api/v1/meeting-rooms/<int:room_id>/book/`
- Method: POST
- login required
- Parameters:
  - `start_time` (str): Start time of the booking. Time should be in python strftime format. (eg "2026-02-05 11:00 AM")
  - `end_time` (str): End time of the booking. (time in same format as above)
  - `no_of_persons` (int, optional): Number of persons for the booking (default is 1).
- Books a meeting room for the specified time range.
- After Booking mail will send to the one who booked

### 4. List My Bookings
- Endpoint: `api/v1/meeting-rooms/my-bookings/`
- Method: GET
- Lists all booked meeting rooms history for a requested user.

### 5. Cancel Meeting Room Booking
- Endpoint: `api/v1/meeting-rooms/<int:booking_id>/cancel-booking/`
- Method: DELETE
- login required
- Cancels a previously booked meeting room.
- Conditions:
  - The meeting room can be canceled only by the user who made the booking.
  - Cancellation is not allowed if the start time has already passed.
- After Cancellation mail will send to the one who booked


### 6. Mail send after booking and cancel booking Feature added

### 7. Unit Test cases
- To run the tests ```python manage.py test```


## Setup Instructions

### Installation
-  Clone the repository:
   ```bash
   git clone https://github.com/your-username/meeting-room-booking.git
    ```
-  Installation steps
    ```
   cd meeting-room-booking
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py loaddata fixtures/data.json
   python manage.py createsuperuser
   ```
- Note - 
  need to create a user in django-admin to use the booking system

