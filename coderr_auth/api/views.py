from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegistrationSerializer, LoginSerializer
from rest_framework.authtoken.models import Token
from coderr_auth.models import Profile
from coderr_auth.api.serializers import ProfileSerializer, BusinessProfilesListSerializer, CustomerProfilesListSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied


class RegistrationAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """
        Handles user registration by validating and saving the provided data.

        This method uses the `RegistrationSerializer` to validate the incoming
        request data. If the data is valid, it creates a new user and generates
        an authentication token for that user. The response includes the user's
        email, username, user ID, and authentication token, returned with 
        a 201 HTTP status code. If the data is invalid, it returns the serializer
        errors with a 400 HTTP status code.

        :param request: The HTTP request containing user registration data.
        :return: A Response object with user information and a token if successful,
                or error details if the validation fails.
        """

        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "email": user.email,
                "username": user.username,
                "user_id": user.id,
                "token": token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProfileDetailsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        """
        Retrieves the profile details for a given primary key.

        This method fetches the profile from the database using the provided
        primary key and serializes the data for response.

        :param request: The HTTP request object.
        :param pk: The primary key of the profile to retrieve.
        :return: A Response object containing the serialized profile data
                with an HTTP 200 status code.
        """

        profile = get_object_or_404(Profile, pk=pk)
        serializer = ProfileSerializer(profile)
        data = serializer.data
        data.pop('uploaded_at', None)
        return Response(data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk, format=None):
        """
        Partially updates a profile with the given primary key, allowing
        updates only to specific fields, and rejecting any other fields.
        """
        profile = get_object_or_404(Profile, pk=pk)

        # Check if the requesting user matches the profile's user
        if profile.user != request.user:
            raise PermissionDenied("Sie haben keine Berechtigung, dieses Profil zu ändern.")

        allowed_fields = {
            'email', 'first_name', 'last_name',
            'file', 'location', 'description', 'working_hours', 'tel'
        }

        # Check for disallowed fields in the request
        disallowed_fields = [key for key in request.data.keys() if key not in allowed_fields]
        if disallowed_fields:
            return Response(
                {"detail": f"Die Felder {', '.join(disallowed_fields)} können nicht aktualisiert werden. Nur die Felder {', '.join(allowed_fields)} dürfen aktualisiert werden."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filter allowed fields from the request
        data = {key: value for key, value in request.data.items() if key in allowed_fields}

        if not data:
            return Response(
                {"detail": f"Es können nur die Felder {', '.join(allowed_fields)} aktualisiert werden."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Pass data to the serializer
        serializer = ProfileSerializer(profile, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Return only the fields that were updated
            updated_fields = {key: serializer.data[key] for key in data.keys()}
            return Response(updated_fields, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """
        Handles user login by validating and returning the authentication token.

        This method uses the `LoginSerializer` to validate the incoming
        request data. If the data is valid, it returns a Response object with
        the user's ID, username, authentication token and profile data returned
        with a 200 HTTP status code. If the data is invalid, it returns the
        serializer errors with a 400 HTTP status code.

        :param request: The HTTP request containing user login data.
        :return: A Response object with user information and a token if successful,
                or error details if the validation fails.
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                "user_id": serializer.validated_data["user_id"],
                "token": serializer.validated_data["token"],
                "username": serializer.validated_data["username"],
                "email": serializer.validated_data["email"],
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProfileListCustomers(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        """
        Retrieves a list of customer profiles.

        This method fetches all profiles with the type 'customer' from the database, 
        serializes the data using `ProfilesListSerializer`, and returns the serialized
        data with an HTTP 200 status code.

        :param request: The HTTP request object.
        :return: A Response object containing the serialized customer profiles data 
                with an HTTP 200 status code.
        """

        profiles = Profile.objects.filter(type='customer')
        serializer = CustomerProfilesListSerializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ProfileListBusiness(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        """
        Retrieves a list of business profiles.

        This method fetches all profiles with the type 'business' from the database,
        serializes the data using `ProfilesListSerializer`, and returns the serialized
        data with an HTTP 200 status code.

        :param request: The HTTP request object.
        :return: A Response object containing the serialized business profiles data 
                with an HTTP 200 status code.
        """

        profiles = Profile.objects.filter(type='business')
        serializer = BusinessProfilesListSerializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

