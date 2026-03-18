# imports
from rest_framework import generics
from django.db.models import Q
from apps.booking.models import BookingHistory, MeetingRoom
from rest_api.booking.utils import is_meeting_room_available, send_cancellation_email, send_confirmation_email
from .serializers import MeetingRoomSerializer
from .serializers import BookingHistorySerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import threading
from django.utils import timezone
from datetime import datetime
from rest_framework.views import APIView


class MeetingRoomListView(generics.ListCreateAPIView):
    """
    API View to list available meeting rooms during a specific time range.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = MeetingRoomSerializer

    def get_queryset(self):
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)

        # Check if start_time and end_time are provided in the request
        if start_time and end_time:
            from django.utils.dateparse import parse_datetime
            if not parse_datetime(start_time) or not parse_datetime(end_time):
                return MeetingRoom.objects.none()

            # Filter meeting rooms based on availability during the specified time range
            queryset = MeetingRoom.objects.filter(
                Q(booking_histories__end_time__lte=start_time) | Q(booking_histories__start_time__gte=end_time) | Q(booking_histories__isnull=True),
                is_active=True
            ).distinct()
        else:
            # If start_time and end_time are not provided, return all meeting rooms
            queryset = MeetingRoom.objects.filter(is_active=True)

        return queryset




class MeetingRoomBookingView(generics.CreateAPIView):
    """
    API View for booking a meeting room.

    Parameters:
    - room_id (int): The ID of the meeting room to be booked.

    Request Body:
    - start_time (str): Start time of the booking in ISO 8601 format.
    - end_time (str): End time of the booking in ISO 8601 format.
    - no_of_persons (int): Number of persons for the booking.

    Returns:
    - 201 Created: Meeting room successfully booked.
    - 400 Bad Request: Invalid input or meeting room is not available.
    - 404 Not Found: Meeting room with the given ID does not exist.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BookingHistorySerializer


    def create(self, request, *args, **kwargs):
        room_id = self.kwargs.get('room_id')
        start_time_str = request.data.get('start_time')
        end_time_str = request.data.get('end_time')
        no_of_persons = request.data.get('no_of_persons', 1)  # Default to 1 person if not provided
        
        # Convert to datetime objects
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %I:%M %p')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %I:%M %p')
        
        try:
            meeting_room = MeetingRoom.objects.get(pk=room_id, is_active=True)
        except MeetingRoom.DoesNotExist:
            return Response({"error": "Meeting room not found."}, status=status.HTTP_404_NOT_FOUND)

        # Use ISO 8601 format when saving to serializer
        serializer = self.get_serializer(data={
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "no_of_persons": no_of_persons,
        })
        serializer.is_valid(raise_exception=True)

        # Check if the meeting room is available for booking and has sufficient capacity
        if not is_meeting_room_available(meeting_room, start_time, end_time) or meeting_room.capacity < no_of_persons:
            return Response({"error": "Meeting room is not available or does not have sufficient capacity for the specified time range and number of persons."}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(meeting_room=meeting_room, booked_by=request.user, no_of_persons=no_of_persons)

        # Create a thread to send the confirmation email with necessary data
        thread = threading.Thread(
            target=send_confirmation_email,
            args=(
                meeting_room.room_name,
                serializer.instance.start_time,
                serializer.instance.end_time,
                request.user.email,
            )
        )
        thread.start()

        return Response({"message": "Meeting room booked successfully."}, status=status.HTTP_201_CREATED)



class MyBookingsView(APIView):
    """
    API View to retrieve a list of bookings made by the authenticated user.

    Returns:
    - 200 OK: List of bookings for the authenticated user.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        bookings = BookingHistory.objects.filter(booked_by=user)
        serializer = BookingHistorySerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class CancelMeetingRoomBookingView(generics.DestroyAPIView):
    """
    API View for canceling a meeting room booking.

    Parameters:
    - booking_id (int): The ID of the booking to be canceled.

    Returns:
    - 204 No Content: Meeting room booking successfully canceled.
    - 400 Bad Request: Invalid input or unable to cancel the booking.
    - 404 Not Found: Meeting room booking with the given ID does not exist.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BookingHistorySerializer

    def destroy(self, request, *args, **kwargs):
        booking_id = self.kwargs.get('booking_id')
        print(request.user)

        try:
            booking = BookingHistory.objects.get(pk=booking_id, booked_by=request.user)
        except BookingHistory.DoesNotExist:
            return Response({"error": "Meeting room booking not found or you are not authorized to cancel this booking."}, status=status.HTTP_404_NOT_FOUND)

        # Check if cancellation is allowed based on start time
        current_time = timezone.now()
        if booking.start_time <= current_time:
            return Response({"error": "Meeting room booking cannot be canceled as the start time has already passed."}, status=status.HTTP_400_BAD_REQUEST)

        booking.delete()

        # Create a thread to send the cancellation email with necessary data
        thread = threading.Thread(
            target=send_cancellation_email,
            args=(
                booking.meeting_room.room_name,
                booking.start_time,
                booking.end_time,
                request.user.email,
            )
        )
        thread.start()

        return Response({"message": "Your Meeting Room Booking has been cancelled!"}, status=status.HTTP_204_NO_CONTENT)
    