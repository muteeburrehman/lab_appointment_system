from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    PendingUserSerializer,
    UserApprovalSerializer,
    UserProfileSerializer  # Add this new serializer
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user (pending approval)
    """
    logger.info(f"Registration attempt with data: {request.data}")

    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            logger.info(f"User created successfully: {user.username} (pending approval)")

            return Response({
                'message': 'Registration successful! Your account is pending approval.',
                'user': UserSerializer(user).data,
                'status': 'pending_approval'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return Response({
                'error': 'Failed to create user account'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    logger.error(f"Validation errors: {serializer.errors}")
    return Response({
        'errors': serializer.errors,
        'detail': 'Validation failed'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_approval_status(request, username):
    """
    Check if a user's account is approved
    """
    try:
        user = User.objects.get(username=username)
        return Response({
            'username': user.username,
            'approval_status': user.approval_status,
            'is_approved': user.is_approved
        })
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Get current user's profile
    """
    try:
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return Response({
            'error': 'Failed to fetch user profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Update current user's profile
    """
    try:
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        return Response({
            'error': 'Failed to update user profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PendingUsersView(generics.ListAPIView):
    """
    List all pending users (admin only)
    """
    serializer_class = PendingUserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return User.objects.filter(approval_status='pending').order_by('-created_at')


class UserApprovalView(generics.UpdateAPIView):
    """
    Approve or reject a user (admin only)
    """
    serializer_class = UserApprovalSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()

    def get_queryset(self):
        return User.objects.filter(approval_status='pending')


# Custom authentication backend to check approval status
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class ApprovalRequiredBackend(ModelBackend):
    """
    Custom authentication backend that checks if user is approved
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                # Check if user is approved
                if user.approval_status != 'approved':
                    return None  # Don't authenticate unapproved users
                return user
            return None
        except User.DoesNotExist:
            return None