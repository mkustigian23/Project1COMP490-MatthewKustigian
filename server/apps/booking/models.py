from django.db import models

from apps.member.models import CustomUser

class MeetingRoom(models.Model):
    """
    Model representing a meeting room.

    Attributes:
        room_name (str): Name of the meeting room.
        capacity (int): Capacity of the meeting room.
        is_active (bool): Indicates whether the meeting room is active or not.

    Methods:
        __str__(): Returns a string representation of the meeting room.
        is_available(): Checks if the meeting room is available for the current booking.
    """
    
    room_name = models.CharField(max_length=255, help_text="Name of the meeting room.")
    capacity = models.PositiveIntegerField(help_text="Capacity of the meeting room.")
    is_active = models.BooleanField(default=True, help_text="Indicates whether the meeting room is active or not.")

    def __str__(self):
        """
        Returns a string representation of the meeting room.
        """
        return self.room_name
    

class BookingHistory(models.Model):
    """
    Model representing the booking history of meeting rooms.

    Attributes:
        meeting_room (MeetingRoom): Meeting room associated with the booking.
        start_time (datetime): Start time of the booking.
        end_time (datetime): End time of the booking.
        no_of_persons (int): Number of persons for the booking.
        booked_by (CustomUser): User making the booking.

    Methods:
        __str__(): Returns a string representation of the booking.
        is_available(): Checks if the meeting room is available for the current booking.
    """

    meeting_room = models.ForeignKey(MeetingRoom, on_delete=models.CASCADE, related_name="booking_histories", help_text="Meeting room associated with the booking.")
    start_time = models.DateTimeField(help_text="Start time of the booking.")
    end_time = models.DateTimeField(help_text="End time of the booking.")
    no_of_persons = models.PositiveIntegerField(help_text="Number of persons for the booking.")
    booked_by = models.ForeignKey(
            CustomUser,
            on_delete=models.CASCADE,
            related_name="bookings",
            help_text="User making the booking."
        )
    
    def __str__(self):
        """
        Returns a string representation of the booking.
        """
        return f"{self.booked_by} booked {self.meeting_room.room_name} from {self.start_time} to {self.end_time}"

    class Meta:
        # Database index for optimized query performance
        indexes = [
            models.Index(fields=['meeting_room', 'start_time', 'end_time']),
        ]
        verbose_name_plural = "Booking Histories"
