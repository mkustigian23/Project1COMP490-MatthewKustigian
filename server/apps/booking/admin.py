from django.contrib import admin
from .models import MeetingRoom, BookingHistory

@admin.register(MeetingRoom)
class MeetingRoomAdmin(admin.ModelAdmin):
    list_display = ('room_name','id', 'capacity', 'is_active')
    search_fields = ('room_name',)
    list_filter = ('is_active',)

@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    list_display = ('meeting_room', 'id', 'start_time', 'end_time', 'no_of_persons', 'booked_by')
    search_fields = ('meeting_room__room_name', 'booked_by__email')
    list_filter = ('start_time', 'end_time', 'no_of_persons', 'booked_by', 'meeting_room')
