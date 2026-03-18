# serializers.py
from rest_framework import serializers

from apps.booking.models import BookingHistory, MeetingRoom


class MeetingRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingRoom
        fields = ['id', 'room_name', 'capacity']


class BookingHistorySerializer(serializers.ModelSerializer):
    meeting_room = MeetingRoomSerializer(read_only=True)
    class Meta:
        model = BookingHistory
        fields = ['id', 'meeting_room', 'start_time', 'end_time']
