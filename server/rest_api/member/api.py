from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.core.utils import is_valid_email
from rest_framework_simplejwt.tokens import RefreshToken


class UserLoginView(APIView):
    """
    API View for user login with email and password, returning a JWT token on success.
    """
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        # Validate email
        if not is_valid_email(email):
            return Response({"error": "Invalid email!"}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            token = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

            return Response({"token": token}, status=status.HTTP_200_OK)

        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
    
