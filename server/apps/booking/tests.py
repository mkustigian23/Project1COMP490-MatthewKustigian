from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import MeetingRoom, BookingHistory

class MeetingRoomAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.meeting_room_url = reverse('meeting-room-list')
        self.booking_url = reverse('book-meeting-room', kwargs={'room_id': 1})
        self.cancel_booking_url = reverse('cancel-meeting-room-booking', kwargs={'booking_id': 1})
        self.meeting_room_data = {'room_name': 'Test Room', 'capacity': 10, 'is_active': True}
        self.start_time = timezone.now() + timezone.timedelta(days=1)
        self.end_time = self.start_time + timezone.timedelta(hours=2)
        self.booking_data = {'start_time': self.start_time.isoformat(), 'end_time': self.end_time.isoformat(), 'no_of_persons': 5}

        # Create a meeting room for testing
        self.meeting_room = MeetingRoom.objects.create(**self.meeting_room_data)

    def test_list_meeting_rooms(self):
        response = self.client.get(self.meeting_room_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_book_meeting_room(self):
        response = self.client.post(self.booking_url, data=self.booking_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cancel_meeting_room_booking(self):
        # Book a meeting room first for testing cancellation
        booking_response = self.client.post(self.booking_url, data=self.booking_data, format='json')
        self.assertEqual(booking_response.status_code, status.HTTP_201_CREATED)
        booking_id = booking_response.data.get('id')

        # Attempt to cancel the booking
        cancel_response = self.client.delete(self.cancel_booking_url)
        self.assertEqual(cancel_response.status_code, status.HTTP_204_NO_CONTENT)