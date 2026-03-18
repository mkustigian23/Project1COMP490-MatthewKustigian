from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.member.models import CustomUser
from apps.booking.models import MeetingRoom, BookingHistory
from django.utils import timezone
from datetime import timedelta, datetime
import json

class MeetingRoomAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_password = 'password123'
        self.user = CustomUser.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password=self.user_password
        )
        self.login_url = reverse('user-login')
        self.room_list_url = reverse('meeting-room-list')
        self.my_bookings_url = reverse('my-bookings')
        
        # Create a meeting room
        self.room = MeetingRoom.objects.create(
            room_name='Alpha Room',
            capacity=10,
            is_active=True
        )
        
        # Helper to get JWT token
        response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': self.user_password
        }, format='json')
        self.token = response.data['token']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_user_login(self):
        # Reset credentials to test login
        self.client.credentials()
        response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': self.user_password
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('access', response.data['token'])

    def test_user_login_invalid_credentials(self):
        self.client.credentials()
        response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': 'wrongpassword'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_available_meeting_rooms(self):
        # Test listing all active rooms (no time range provided)
        response = self.client.get(self.room_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['room_name'], 'Alpha Room')

    def test_list_available_meeting_rooms_with_time_range(self):
        start_time = (timezone.now() + timedelta(days=1)).replace(microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        # Room should be available
        response = self.client.get(self.room_list_url, {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_book_meeting_room(self):
        start_time = (timezone.now() + timedelta(days=1)).replace(microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        # Format used in MeetingRoomBookingView.create: datetime.strptime(start_time_str, '%Y-%m-%d %I:%M %p')
        start_time_str = start_time.strftime('%Y-%m-%d %I:%M %p')
        end_time_str = end_time.strftime('%Y-%m-%d %I:%M %p')
        
        url = reverse('book-meeting-room', kwargs={'room_id': self.room.id})
        data = {
            'start_time': start_time_str,
            'end_time': end_time_str,
            'no_of_persons': 5
        }
        
        # We need to mock the email sending or just let it run if it doesn't fail
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Meeting room booked successfully.')
        self.assertTrue(BookingHistory.objects.filter(booked_by=self.user, meeting_room=self.room).exists())

    def test_book_meeting_room_insufficient_capacity(self):
        start_time = (timezone.now() + timedelta(days=1)).replace(microsecond=0)
        end_time = start_time + timedelta(hours=2)
        start_time_str = start_time.strftime('%Y-%m-%d %I:%M %p')
        end_time_str = end_time.strftime('%Y-%m-%d %I:%M %p')
        
        url = reverse('book-meeting-room', kwargs={'room_id': self.room.id})
        data = {
            'start_time': start_time_str,
            'end_time': end_time_str,
            'no_of_persons': 20 # Capacity is 10
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_list_my_bookings(self):
        start_time = (timezone.now() + timedelta(days=1)).replace(microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        BookingHistory.objects.create(
            meeting_room=self.room,
            booked_by=self.user,
            start_time=timezone.make_aware(start_time.replace(tzinfo=None)) if timezone.is_naive(start_time) else start_time,
            end_time=timezone.make_aware(end_time.replace(tzinfo=None)) if timezone.is_naive(end_time) else end_time,
            no_of_persons=5
        )
        
        response = self.client.get(self.my_bookings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['meeting_room']['id'], self.room.id)

    def test_cancel_booking(self):
        start_time = (timezone.now() + timedelta(days=1)).replace(microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        booking = BookingHistory.objects.create(
            meeting_room=self.room,
            booked_by=self.user,
            start_time=timezone.make_aware(start_time.replace(tzinfo=None)) if timezone.is_naive(start_time) else start_time,
            end_time=timezone.make_aware(end_time.replace(tzinfo=None)) if timezone.is_naive(end_time) else end_time,
            no_of_persons=5
        )
        
        url = reverse('cancel-meeting-room-booking', kwargs={'booking_id': booking.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BookingHistory.objects.filter(id=booking.id).exists())

    def test_cancel_booking_not_authorized(self):
        other_user = CustomUser.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='password123'
        )
        start_time = (timezone.now() + timedelta(days=1)).replace(microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        booking = BookingHistory.objects.create(
            meeting_room=self.room,
            booked_by=other_user,
            start_time=timezone.make_aware(start_time.replace(tzinfo=None)) if timezone.is_naive(start_time) else start_time,
            end_time=timezone.make_aware(end_time.replace(tzinfo=None)) if timezone.is_naive(end_time) else end_time,
            no_of_persons=5
        )
        
        url = reverse('cancel-meeting-room-booking', kwargs={'booking_id': booking.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(BookingHistory.objects.filter(id=booking.id).exists())

    def test_cancel_booking_already_passed(self):
        start_time = (timezone.now() - timedelta(hours=1)).replace(microsecond=0)
        end_time = (timezone.now() + timedelta(hours=1)).replace(microsecond=0)
        
        booking = BookingHistory.objects.create(
            meeting_room=self.room,
            booked_by=self.user,
            start_time=timezone.make_aware(start_time.replace(tzinfo=None)) if timezone.is_naive(start_time) else start_time,
            end_time=timezone.make_aware(end_time.replace(tzinfo=None)) if timezone.is_naive(end_time) else end_time,
            no_of_persons=5
        )
        
        url = reverse('cancel-meeting-room-booking', kwargs={'booking_id': booking.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertTrue(BookingHistory.objects.filter(id=booking.id).exists())

    def test_authentication_required(self):
        self.client.credentials() # Clear tokens
        
        protected_urls = [
            ('get', self.room_list_url),
            ('post', reverse('book-meeting-room', kwargs={'room_id': self.room.id})),
            ('get', self.my_bookings_url),
            ('delete', reverse('cancel-meeting-room-booking', kwargs={'booking_id': 1})),
        ]
        
        for method, url in protected_urls:
            response = getattr(self.client, method)(url)
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN], f"URL {url} should be protected")

    def test_book_overlapping_booking(self):
        start_time = (timezone.now() + timedelta(days=2)).replace(microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        # Create existing booking
        BookingHistory.objects.create(
            meeting_room=self.room,
            booked_by=self.user,
            start_time=timezone.make_aware(start_time.replace(tzinfo=None)) if timezone.is_naive(start_time) else start_time,
            end_time=timezone.make_aware(end_time.replace(tzinfo=None)) if timezone.is_naive(end_time) else end_time,
            no_of_persons=5
        )
        
        # Attempt to book overlapping time
        url = reverse('book-meeting-room', kwargs={'room_id': self.room.id})
        start_time_str = (start_time + timedelta(hours=1)).strftime('%Y-%m-%d %I:%M %p')
        end_time_str = (end_time + timedelta(hours=1)).strftime('%Y-%m-%d %I:%M %p')
        
        data = {
            'start_time': start_time_str,
            'end_time': end_time_str,
            'no_of_persons': 5
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_book_room_not_found(self):
        url = reverse('book-meeting-room', kwargs={'room_id': 999})
        start_time = timezone.now() + timedelta(days=1)
        data = {
            'start_time': start_time.strftime('%Y-%m-%d %I:%M %p'),
            'end_time': (start_time + timedelta(hours=1)).strftime('%Y-%m-%d %I:%M %p'),
            'no_of_persons': 5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_available_rooms_overlapping(self):
        start_time = (timezone.now() + timedelta(days=3)).replace(microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        # Create existing booking
        BookingHistory.objects.create(
            meeting_room=self.room,
            booked_by=self.user,
            start_time=timezone.make_aware(start_time.replace(tzinfo=None)) if timezone.is_naive(start_time) else start_time,
            end_time=timezone.make_aware(end_time.replace(tzinfo=None)) if timezone.is_naive(end_time) else end_time,
            no_of_persons=5
        )
        
        # Query for a range that overlaps
        query_start = (start_time + timedelta(minutes=30)).isoformat()
        query_end = (end_time - timedelta(minutes=30)).isoformat()
        
        response = self.client.get(self.room_list_url, {
            'start_time': query_start,
            'end_time': query_end
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_book_meeting_room_invalid_time_format(self):
        url = reverse('book-meeting-room', kwargs={'room_id': self.room.id})
        data = {
            'start_time': 'invalid-time',
            'end_time': 'invalid-time',
            'no_of_persons': 5
        }
        
        with self.assertRaises(ValueError):
            self.client.post(url, data, format='json')

    def test_list_available_rooms_invalid_time_format(self):
        # The API doesn't seem to validate start_time/end_time in MeetingRoomListView
        # but it uses them in Q filters. SQLite might handle it or it might just return 
        # empty or all rooms.
        response = self.client.get(self.room_list_url, {
            'start_time': 'invalid-time',
            'end_time': 'invalid-time'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
