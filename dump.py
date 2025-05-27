"""
User authentication and account management views.

This module provides views for user authentication, registration, password management,
and account verification in a secure manner with rate limiting and proper token validation.
"""

# Standard library imports
from datetime import datetime, timedelta, timezone
import logging

# Django imports
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

# Third-party imports
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

# Local imports
from .models import UserLoginAttempt
from .serializers import (
    EmailSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
)


@method_decorator(
    ratelimit(key="ip", rate="5/m", method="POST", block=True), name="post"
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # Get client IP
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        username = request.data.get("username", "")
        password = request.data.get("password", "")

        # Check if user exists without authenticating
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            user = None

        # Authenticate
        user_auth = authenticate(username=username, password=password)

        # Log the attempt

        UserLoginAttempt.objects.create(
            user=user, username=username, ip_address=ip, success=user_auth is not None
        )

        # Check for too many failed attempts
        if user:
            recent_failed_attempts = UserLoginAttempt.objects.filter(
                user=user,
                success=False,
                timestamp__gte=datetime.now() - timedelta(minutes=30),
            ).count()

            if recent_failed_attempts >= 5:
                return Response(
                    {
                        "error": "Account temporarily locked due to too many failed login attempts. Try again later.",
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        "user_login": "System",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Process the login
        return super().post(request, *args, **kwargs)


@method_decorator(
    ratelimit(key="ip", rate="10/h", method="POST", block=True), name="post"
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "user_login": user.username,
            }
        )


class UserProfileView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Add timestamp and user login information
        data["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        data["user_login"] = request.user.username

        return Response(data)


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = EmailSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

            # Send email with reset link
            send_mail(
                "Password Reset Request",
                f"Click the link to reset your password: {reset_link}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response(
                {
                    "message": "Password reset email has been sent.",
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_login": "System",
                }
            )
        except User.DoesNotExist:
            # Don't reveal user existence, but still return a success response
            return Response(
                {
                    "message": "Password reset email has been sent if the email exists.",
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_login": "System",
                }
            )


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        password = serializer.validated_data["password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)

            if default_token_generator.check_token(user, token):
                user.set_password(password)
                user.save()
                return Response(
                    {
                        "message": "Password has been reset successfully.",
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        "user_login": "System",
                    }
                )
            else:
                return Response(
                    {
                        "error": "Invalid token.",
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        "user_login": "System",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except (TypeError, ValueError, User.DoesNotExist):
            return Response(
                {
                    "error": "Invalid reset link.",
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_login": "System",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogoutView(APIView):
    """
    API endpoint that handles user logout by blacklisting JWT refresh tokens.

    This view invalidates the user's refresh token by adding it to the token blacklist,
    which prevents it from being used to obtain new access tokens. This effectively
    logs the user out of the system from all devices where this refresh token was used.

    Requires authentication to access.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """
        Handle POST requests for user logout.

        Blacklists the provided refresh token, preventing it from being used
        to generate new access tokens. Once blacklisted, the user will need to
        log in again to obtain new tokens.

        Args:
            request: HTTP request object containing:
                - refresh: The refresh token to blacklist in the request body

        Returns:
            Response: JSON response containing:
                - message: Success or error message
                - timestamp: Current UTC time in YYYY-MM-DD HH:MM:SS format
                - user_login: Username of the logged out user

        Status Codes:
            200: Successful logout
            400: Invalid token or other error
        """
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {
                    "message": "Logout successful",
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_login": request.user.username,
                }
            )
        except (TokenError, AttributeError, TypeError) as e:
            logging.error("Token blacklist error: %s", str(e))
            return Response(
                {
                    "error": str(e),
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_login": request.user.username,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class EmailVerificationView(generics.GenericAPIView):
    """
    API endpoint that handles email verification after user registration.

    This view verifies the user's email by checking the provided token and UID.
    If valid, it activates the user account, allowing the user to log in.
    """

    permission_classes = (permissions.AllowAny,)

    def get(self, request, uid, token):
        """
        Handle GET requests for email verification.

        Args:
            request: HTTP request object
            uid: Base64 encoded user ID
            token: Verification token

        Returns:
            Response: JSON response with success or error message
        """
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)

            if default_token_generator.check_token(user, token):
                # Activate user
                user.is_active = True
                user.save()
                return Response(
                    {
                        "message": "Email verified successfully. Your account is now active.",
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        "user_login": user.username,
                    }
                )
            else:
                return Response(
                    {
                        "error": "Invalid verification token.",
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        "user_login": "System",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except (TypeError, ValueError, User.DoesNotExist):  # pylint: disable=no-member
            return Response(
                {
                    "error": "Invalid verification link.",
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_login": "System",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
serializers.py
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from datetime import datetime
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.mail import send_mail
import re


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "roles")

    def get_roles(self, obj):
        return [group.name for group in obj.groups.all()]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom claims
        data["user"] = UserSerializer(self.user).data

        # Add timestamp in the specified format
        data["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        data["user_login"] = self.user.username

        return data

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(
        choices=["Admin", "Manager", "Employee", "Auditor"],
        write_only=True,
        required=False,
        default="Employee",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name", "role")
        extra_kwargs = {"email": {"required": True}}

    def create(self, validated_data):
        # Set user as inactive until email is verified
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_active=False,  # User inactive until verified
        )

        # Assign role
        role = validated_data.pop("role", "Employee")
        group = Group.objects.get(name=role)
        user.groups.add(group)

        # Generate verification token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Send verification email
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
        send_mail(
            "Verify Your Email",
            f"Click the link to verify your email: {verification_link}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return user


class EmailSerializer(serializers.Serializer):
    """
    Serializer for handling email-based operations like password reset requests.

    This serializer validates that the provided email is correctly formatted.
    It is used in the password reset flow to collect the user's email address
    before sending a reset link.
    """

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Validate that the email is properly formatted.

        Note: We don't validate if the email exists in the database here,
        as this would leak information about registered users.

        Args:
            value: The email to validate

        Returns:
            str: The validated email
        """
        # You could add custom email validation here if needed
        # For example, domain-specific rules or blocking certain domains
        return value

    # Need to add these to EmailSerializer:
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for handling password reset operations.

    This serializer collects and validates:
    - uid: Base64 encoded user ID
    - token: Password reset token
    - password: New password
    - confirm_password: Password confirmation

    It ensures the new password meets the system's security requirements
    and that the confirmation matches.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, min_length=8, write_only=True, style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        """
        Validate that the passwords match.

        Args:
            data: The serializer data containing both passwords

        Returns:
            dict: The validated data

        Raises:
            ValidationError: If passwords don't match
        """
        # Check that passwords match
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": ["Passwords do not match."]}
            )
        return attrs

    def validate_password(self, value):
        """
        Validate the password strength.

        Ensures the password meets security requirements:
        - At least 8 characters long
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        - Contains at least one special character

        Args:
            value: The password to validate

        Returns:
            str: The validated password

        Raises:
            ValidationError: If password doesn't meet requirements
        """
        # Check password length
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )

        # Check for uppercase letter
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        # Check for lowercase letter
        if not any(char.islower() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )

        # Check for digit
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )

        # Check for special character

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError(
                "Password must contain at least one special character."
            )

        return value

    def validate_uid(self, value):
        """
        Validate that the UID can be decoded.

        Args:
            value: The encoded UID

        Returns:
            str: The validated UID

        Raises:
            ValidationError: If UID is invalid
        """
        try:
            uid = force_str(urlsafe_base64_decode(value))
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, User.DoesNotExist, OverflowError) as exc:
            raise serializers.ValidationError("Invalid user identification.") from exc
        return value

    def validate_token(self, value):
        """
        Validate the password reset token.

        Note: This requires validate_uid to be called first,
        which happens automatically in DRF's validation flow.

        Args:
            value: The token to validate

        Returns:
            str: The validated token

        Raises:
            ValidationError: If token is invalid
        """
        if not hasattr(self, "user"):
            # This shouldn't happen as validate_uid should be called first
            raise serializers.ValidationError("Invalid validation order.")

        is_valid = default_token_generator.check_token(self.user, value)
        if not is_valid:
            raise serializers.ValidationError("Invalid or expired token.")
        return value

    # Need to add these to PasswordResetSerializer:
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
urls.py:
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    EmailVerificationView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    UserProfileView,
    CustomTokenObtainPairView,
)

urlpatterns = [
    # JWT token endpoints
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # User management endpoints
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "verify-email/<str:uid>/<str:token>/",
        EmailVerificationView.as_view(),
        name="verify_email",
    ),
]

config/urls.py:
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/inventory/", include("inventory.urls")),
    path("api/users/", include("user_management.urls")),
]

models.py:
from django.db import models
from django.contrib.auth.models import User


class UserLoginAttempt(models.Model):
    """
    Tracks all login attempts to the system for security monitoring and audit purposes.

    This model records both successful and failed login attempts, storing information
    about the user, username attempted, IP address, success status, and timestamp.
    This data can be used for security analysis, detecting brute force attacks,
    and meeting audit/compliance requirements.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    """Reference to the User if login was successful or if user exists (null for non-existent users)"""

    username = models.CharField(max_length=150)
    """The username that was used in the login attempt"""

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    """IP address from which the login attempt originated"""

    success = models.BooleanField(default=False)
    """Whether the login attempt was successful (True) or failed (False)"""

    timestamp = models.DateTimeField(auto_now_add=True)
    """When the login attempt occurred (automatically set on creation)"""

    class Meta:
        """
        Model metadata options.
        """

        ordering = ["-timestamp"]  # Most recent attempts first

config/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/inventory/", include("inventory.urls")),
    path("api/users/", include("user_management.urls")),
]

permissions.py:
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="Admin").exists()
        )


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="Manager").exists()
        )


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="Employee").exists()
        )


class IsAuditor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="Auditor").exists()
        )


class IsAuditLogViewer(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return any(
            [
                request.user.groups.filter(name="Admin").exists(),
                request.user.groups.filter(name="Manager").exists(),
                request.user.groups.filter(name="Auditor").exists(),
            ]
        )


class IsAnyOf(BasePermission):
    def __init__(self, *perms):
        self.perms = perms

    def has_permission(self, request, view):
        return any(perm().has_permission(request, view) for perm in self.perms)

confest.py:

"""
Test fixtures for user management app.

This module provides pytest fixtures for testing the authentication system,
including user creation, group setup, and API client configuration.
"""

import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from datetime import datetime, timedelta


@pytest.fixture
def api_client():
    """
    Return an authenticated API client for testing API endpoints.

    This fixture provides a DRF APIClient instance that can be used to make
    requests to the API endpoints.

    Returns:
        APIClient: An instance of the DRF API client
    """
    return APIClient()


@pytest.fixture
def create_groups():
    """
    Create the user groups required for the application.

    This fixture ensures that all the required groups (Admin, Manager, Employee, Auditor)
    exist in the database for testing role-based permissions.

    Returns:
        list: List of created Group instances
    """
    groups = []
    for group_name in ["Admin", "Manager", "Employee", "Auditor"]:
        group, _ = Group.objects.get_or_create(name=group_name)
        groups.append(group)
    return groups


@pytest.fixture
def create_user(create_groups):
    """
    Factory fixture to create test users with specific roles.

    This fixture returns a function that can be used to create users with
    different attributes and roles for testing.

    Args:
        create_groups: Fixture to ensure groups exist

    Returns:
        function: User creation function that accepts parameters:
            - username: Username for the user (default: 'testuser')
            - password: Password for the user (default: 'Test1234!')
            - email: Email for the user (default: 'test@example.com')
            - role: Role to assign (default: 'Employee')
            - is_active: Whether user is active (default: True)
            - first_name: First name (default: '')
            - last_name: Last name (default: '')
    """

    def _create_user(
        username="testuser",
        password="Test1234!",
        email="test@example.com",
        role="Employee",
        is_active=True,
        first_name="",
        last_name="",
    ):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
        )
        # Assign role
        group = Group.objects.get(name=role)
        user.groups.add(group)
        return user

    return _create_user


@pytest.fixture
def admin_user(create_user):
    """
    Create an admin user for testing admin permissions.

    Returns:
        User: A user with Admin role
    """
    return create_user(
        username="admin",
        email="admin@example.com",
        role="Admin",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
def employee_user(create_user):
    """
    Create an employee user for testing standard permissions.

    Returns:
        User: A user with Employee role
    """
    return create_user(
        username="employee",
        email="employee@example.com",
        role="Employee",
        first_name="Regular",
        last_name="Employee",
    )


@pytest.fixture
def manager_user(create_user):
    """
    Create a manager user for testing management permissions.

    Returns:
        User: A user with Manager role
    """
    return create_user(
        username="manager",
        email="manager@example.com",
        role="Manager",
        first_name="Department",
        last_name="Manager",
    )


@pytest.fixture
def auditor_user(create_user):
    """
    Create an auditor user for testing audit permissions.

    Returns:
        User: A user with Auditor role
    """
    return create_user(
        username="auditor",
        email="auditor@example.com",
        role="Auditor",
        first_name="System",
        last_name="Auditor",
    )


@pytest.fixture
def inactive_user(create_user):
    """
    Create an inactive user for testing activation.

    Returns:
        User: An inactive user
    """
    return create_user(
        username="inactive", email="inactive@example.com", is_active=False
    )


@pytest.fixture
def auth_client(api_client):
    """
    Factory fixture to create an authenticated client for a user.

    This fixture returns a function that accepts a user object and returns
    an authenticated API client for that user.

    Args:
        api_client: The API client fixture

    Returns:
        function: Function that accepts a user and returns an authenticated client
    """

    def _get_auth_client(user):
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return api_client, str(refresh)

    return _get_auth_client


@pytest.fixture
def login_user():
    """
    Factory fixture to login a user and get their tokens.

    This fixture returns a function that makes a login request to the API
    and returns the access and refresh tokens.

    Returns:
        function: Function that accepts a client, username, and password
                 and returns access and refresh tokens
    """

    def _login_user(client, username, password):
        url = reverse("token_obtain_pair")
        response = client.post(
            url, {"username": username, "password": password}, format="json"
        )
        return {
            "access": response.data.get("access"),
            "refresh": response.data.get("refresh"),
            "response": response,
        }

    return _login_user


# In conftest.py - fix the create_failed_login_attempts fixture:
@pytest.fixture
def create_failed_login_attempts():
    def _create_failed_attempts(user, count=5, ip_address="127.0.0.1"):
        from user_management.models import UserLoginAttempt
        from django.utils import timezone

        for i in range(count):
            UserLoginAttempt.objects.create(
                user=user,
                username=user.username,
                ip_address=ip_address,
                success=False,
                # Use timezone-aware datetime
                timestamp=timezone.now()
                - timezone.timedelta(minutes=5)
                + timezone.timedelta(seconds=i * 30),
            )

    return _create_failed_attempts


@pytest.fixture
def create_verification_token():
    """
    Factory fixture to create email verification tokens.

    This fixture creates a verification token and UID for a user,
    similar to what would be generated during registration.

    Returns:
        function: Function that accepts a user and returns uid and token
    """

    def _create_verification_token(user):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return uid, token

    return _create_verification_token


@pytest.fixture
def create_password_reset_token():
    """
    Factory fixture to create password reset tokens.

    This fixture creates a password reset token and UID for a user,
    similar to what would be generated during a password reset request.

    Returns:
        function: Function that accepts a user and returns uid and token
    """

    def _create_password_reset_token(user):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return uid, token

    return _create_password_reset_token

tokens.py
"""
Token generation for email verification.

This module provides token generation functionality for email verification
using Django's PasswordResetTokenGenerator.
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator
import hashlib
from django.utils.encoding import force_bytes


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Token generator for account activation/email verification."""

    def _make_hash_value(self, user, timestamp):
        """
        Create a unique hash value for the user.

        This includes the user's primary key, timestamp, and active status
        to ensure the token is unique and becomes invalid when the user's
        status changes.
        """
        # Convert values to strings and concatenate
        login_timestamp = (
            ""
            if user.last_login is None
            else user.last_login.replace(microsecond=0, tzinfo=None).isoformat()
        )

        # Create a unique string based on user data that changes when account is activated
        return f"{user.pk}{timestamp}{user.is_active}{login_timestamp}"


# Create a single instance of the token generator
account_activation_token = AccountActivationTokenGenerator()


Complete Test Structure
Code
user_management/
├── tests/
│   ├── __init__.py
│   ├── conftest.py (global fixtures)
│   ├── test_models.py
│   ├── test_serializers.py
│   ├── test_views.py
│   ├── test_permissions.py
│   ├── test_registration.py
│   ├── test_authentication.py
│   ├── test_password_reset.py
│   ├── test_profile.py
│   ├── test_email_verification.py
│   └── test_security.py
