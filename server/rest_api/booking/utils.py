
from django.conf import settings
from django.core.mail import send_mail


def is_meeting_room_available(booking, start_time, end_time):
    """
    Checks if the meeting room is available for the current booking.

    Returns:
        bool: True if the meeting room is available, False otherwise.
    """
    return not booking.booking_histories.filter(
        start_time__lt=end_time,
        end_time__gt=start_time
    ).exists()


def send_confirmation_email(room_name, start_time, end_time, booked_by_email):
    """
    Send a confirmation email for a meeting room booking.

    Parameters:
    - room_name (str): The name of the booked meeting room.
    - start_time (datetime): The start time of the booking.
    - end_time (datetime): The end time of the booking.
    - booked_by_email (str): The email address of the user who made the booking.

    The email will contain details of the booking, including the meeting room name, date, and time.

    Example:
    send_confirmation_email('Conference Room A', datetime(2023, 12, 15, 10, 0), datetime(2023, 12, 15, 12, 0), 'user@example.com')
    """
    subject = 'Meeting Room Booking Confirmation'
    formatted_start_time = start_time.strftime("%d-%B-%Y %I:%M %p")
    formatted_end_time = end_time.strftime("%I:%M %p")
    message = f'You have successfully booked meeting room {room_name}. Your booking details:\nDate & Time: {formatted_start_time}  -  {formatted_end_time}.'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = booked_by_email
    try:
        send_mail(subject, message, from_email, [to_email])
    except Exception as e:
        print(f"Error sending confirmation email: {e}")


def send_cancellation_email(room_name, start_time, end_time, booked_by_email):
    """
    Send a cancellation email for a meeting room booking.

    Parameters:
    - room_name (str): The name of the canceled meeting room booking.
    - start_time (datetime): The start time of the canceled booking.
    - end_time (datetime): The end time of the canceled booking.
    - booked_by_email (str): The email address of the user who made the canceled booking.

    The email will notify the user about the cancellation and include details such as the meeting room name, date, and time.

    Example:
    send_cancellation_email('Conference Room A', datetime(2023, 12, 15, 10, 0), datetime(2023, 12, 15, 12, 0), 'user@example.com')
    """
    subject = 'Meeting Room Booking Cancellation'
    formatted_start_time = start_time.strftime("%d-%B-%Y %I:%M %p")
    formatted_end_time = end_time.strftime("%I:%M %p")
    message = f'Your booking for meeting room {room_name} from {formatted_start_time} to {formatted_end_time} has been canceled.'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = booked_by_email
    try:
        send_mail(subject, message, from_email, [to_email])
    except Exception as e:
        print(f"Error sending cancellation email: {e}")





def send_cancellation_email(room_name, start_time, end_time, booked_by_email):
    subject = 'Meeting Room Booking Cancellation'
    formatted_start_time = start_time.strftime("%d-%B-%Y %I:%M %p")
    formatted_end_time = end_time.strftime("%I:%M %p")
    message = f'Your booking for meeting room {room_name} from {formatted_start_time} to {formatted_end_time} has been canceled.'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = booked_by_email
    try:
        send_mail(subject, message, from_email, [to_email])
    except Exception as e:
        print(f"Error sending cancellation email: {e}")