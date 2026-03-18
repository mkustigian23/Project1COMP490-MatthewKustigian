from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from apps.member.manager import CustomUserManager



class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model representing a user account.

    Attributes:
    - email (str): The unique email address associated with the user.
    - username (str): The username of the user (optional).
    - is_active (bool): A boolean indicating whether the user account is active.
    - is_staff (bool): A boolean indicating whether the user has staff privileges.
    - is_superuser (bool): A boolean indicating whether the user has superuser privileges.

    Additional Attributes:
    - USERNAME_FIELD (str): The field used as the unique identifier for authentication (email in this case).
    - REQUIRED_FIELDS (list): A list of fields required for creating a user via the `createsuperuser` management command.

    Methods:
    - __str__(): Returns a string representation of the user (email).

    Meta:
    - verbose_name (str): Singular name for the user model.
    - verbose_name_plural (str): Plural name for the user model.
    """
    email = models.EmailField(max_length=50, unique=True)
    username = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
