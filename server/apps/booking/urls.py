from django.urls import path

from rest_api.booking.api import CancelMeetingRoomBookingView, MeetingRoomBookingView, MeetingRoomListView, MyBookingsView

urlpatterns = [
    # Endpoint for listing available meeting rooms
    path('available/', MeetingRoomListView.as_view(), name='meeting-room-list'),

    # Endpoint for booking a meeting room by room_id
    path('<int:room_id>/book/', MeetingRoomBookingView.as_view(), name='book-meeting-room'),

    # Endpoint for list of bookings booked by requested user
    path('my-bookings/', MyBookingsView.as_view(), name='my-bookings'),

    # Endpoint for cancel a booking room_id
    path('<int:booking_id>/cancel-booking/', CancelMeetingRoomBookingView.as_view(), name='cancel-meeting-room-booking'),
]
